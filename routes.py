import json
import re

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ai_core import generate_assistant_reply, stream_assistant_reply
from config import APP_NAME, MODEL_NAME, logger
from memory import memory_store
from models import ChatRequest, ChatResponse
from realtime import build_event, manager, voice_hooks

router = APIRouter()
# user_id policy: alphanumeric/underscore/hyphen only, 1-64 chars.
USER_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


@router.get("/")
async def home() -> dict[str, str]:
    return {"app": APP_NAME, "status": "ok"}


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "model": MODEL_NAME}


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    memory_store.add_message(req.user_id, "user", req.message)
    reply = await generate_assistant_reply(req.message, memory_store.get_history(req.user_id))
    memory_store.add_message(req.user_id, "assistant", reply)
    return ChatResponse(reply=reply)


@router.websocket("/ws/{room_id}/{session_id}")
async def websocket_chat(websocket: WebSocket, room_id: str, session_id: str) -> None:
    candidate_user_id = websocket.query_params.get("user_id", session_id)
    user_id = candidate_user_id if USER_ID_PATTERN.fullmatch(candidate_user_id) else session_id
    await manager.connect(websocket, room_id=room_id, session_id=session_id)
    memory_store.bind_session(room_id=room_id, session_id=session_id, user_id=user_id)

    await manager.broadcast_room(
        room_id,
        build_event("session.joined", room_id, session_id, user_id=user_id, transport="websocket"),
    )

    stage = "connect"
    try:
        await manager.broadcast_room(room_id, build_event("assistant.state", room_id, session_id, state="idle"))
        while True:
            stage = "receive"
            raw = await websocket.receive_text()
            payload = json.loads(raw)
            kind = payload.get("type", "chat")

            if kind == "voice.input.chunk":
                await voice_hooks.on_voice_input_chunk(room_id, session_id, payload)
                await manager.broadcast_room(
                    room_id,
                    build_event("voice.input.ack", room_id, session_id, status="accepted", meta=payload.get("meta", {})),
                )
                continue

            user_message = str(payload.get("message", "")).strip()
            if not user_message:
                logger.warning("Empty websocket message rejected for room=%s session=%s", room_id, session_id)
                await manager.broadcast_room(
                    room_id,
                    build_event("error", room_id, session_id, code="empty_message", detail="Message cannot be empty"),
                )
                continue

            memory_store.add_message(user_id, "user", user_message)
            await manager.broadcast_room(
                room_id,
                build_event("assistant.state", room_id, session_id, state="listening", message=user_message),
            )
            await manager.broadcast_room(
                room_id,
                build_event("assistant.state", room_id, session_id, state="thinking"),
            )
            await manager.broadcast_room(
                room_id,
                build_event("assistant.state", room_id, session_id, state="responding"),
            )

            full_reply = ""
            stage = "stream"
            async for chunk in stream_assistant_reply(user_message, memory_store.get_history(user_id)):
                full_reply += chunk
                await manager.broadcast_room(
                    room_id,
                    build_event("assistant.response.chunk", room_id, session_id, chunk=chunk),
                )

            memory_store.add_message(user_id, "assistant", full_reply)
            await manager.broadcast_room(
                room_id,
                build_event("assistant.response.complete", room_id, session_id, message=full_reply),
            )
            await manager.broadcast_room(room_id, build_event("assistant.state", room_id, session_id, state="idle"))

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id=room_id, session_id=session_id)
        await manager.broadcast_room(room_id, build_event("session.left", room_id, session_id, user_id=user_id))
    except Exception as exc:
        logger.exception("Websocket error in room %s: %s", room_id, exc)
        await manager.broadcast_room(
            room_id,
            build_event(
                "error",
                room_id,
                session_id,
                code="internal_error",
                detail=f"Unexpected realtime error during {stage}",
            ),
        )
        manager.disconnect(websocket, room_id=room_id, session_id=session_id)


__all__ = ["router"]
