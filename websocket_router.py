import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ai_core import stream_nexora_response
from config import logger
from events import (
    assistant_message_event,
    assistant_state_event,
    error_event,
    typing_start_event,
    typing_stop_event,
    user_message_event,
)
from realtime_types import AssistantState, ConnectionContext

router = APIRouter()


class ConnectionManager:
    def __init__(self) -> None:
        self.room_connections: dict[str, set[WebSocket]] = {}
        self.connection_context: dict[WebSocket, ConnectionContext] = {}

    @staticmethod
    def _room_key(context: ConnectionContext) -> str:
        return context.room_id or context.session_id or context.user_id

    async def connect(self, websocket: WebSocket, context: ConnectionContext) -> None:
        await websocket.accept()
        room_key = self._room_key(context)
        self.room_connections.setdefault(room_key, set()).add(websocket)
        self.connection_context[websocket] = context

    def disconnect(self, websocket: WebSocket) -> None:
        context = self.connection_context.pop(websocket, None)
        if context is None:
            return
        room_key = self._room_key(context)
        members = self.room_connections.get(room_key)
        if not members:
            return
        members.discard(websocket)
        if not members:
            self.room_connections.pop(room_key, None)

    async def send_json(self, websocket: WebSocket, payload: dict) -> None:
        try:
            await websocket.send_text(json.dumps(payload, ensure_ascii=False))
        except Exception as exc:  # pragma: no cover - network/runtime condition
            logger.warning("Failed to send websocket event: %s", exc)
            self.disconnect(websocket)

    async def broadcast(self, context: ConnectionContext, payload: dict) -> None:
        room_key = self._room_key(context)
        for connection in list(self.room_connections.get(room_key, set())):
            await self.send_json(connection, payload)


manager = ConnectionManager()


def _context_from_payload(base: ConnectionContext, data: dict) -> ConnectionContext:
    return ConnectionContext(
        user_id=data.get("user_id") or base.user_id,
        session_id=data.get("session_id") or base.session_id,
        room_id=data.get("room_id") or base.room_id,
        site_id=data.get("site_id") or base.site_id,
        visitor_id=data.get("visitor_id") or base.visitor_id,
        device_id=data.get("device_id") or base.device_id,
    )


@router.websocket("/ws")
async def realtime_websocket(websocket: WebSocket):
    context = ConnectionContext(
        user_id=websocket.query_params.get("user_id") or "anonymous",
        session_id=websocket.query_params.get("session_id"),
        room_id=websocket.query_params.get("room_id"),
        site_id=websocket.query_params.get("site_id"),
        visitor_id=websocket.query_params.get("visitor_id"),
        device_id=websocket.query_params.get("device_id"),
    )
    await manager.connect(websocket, context)

    await manager.send_json(websocket, assistant_state_event(AssistantState.IDLE, context))

    try:
        while True:
            incoming = await websocket.receive_json()
            event_type = incoming.get("event")
            data = incoming.get("data") or {}
            current_context = _context_from_payload(context, data)

            if event_type == "ping":
                await manager.send_json(websocket, {"event": "pong"})
                continue

            if event_type == "voice.audio.chunk":
                await manager.send_json(
                    websocket,
                    error_event("voice.audio.chunk is reserved for future voice pipeline integration.", current_context),
                )
                continue

            if event_type not in {"message.user", "voice.transcript"}:
                await manager.send_json(websocket, error_event(f"Unsupported event '{event_type}'.", current_context))
                continue

            text = (data.get("text") or data.get("transcript") or "").strip()
            if not text:
                await manager.send_json(websocket, error_event("Message text is required.", current_context))
                continue

            await manager.broadcast(current_context, user_message_event(text, current_context))
            await manager.send_json(websocket, assistant_state_event(AssistantState.LISTENING, current_context))
            await manager.send_json(websocket, assistant_state_event(AssistantState.THINKING, current_context))
            await manager.send_json(websocket, typing_start_event(current_context))
            await manager.send_json(websocket, assistant_state_event(AssistantState.RESPONDING, current_context))

            pending_chunk = None
            async for chunk in stream_nexora_response(
                user_id=current_context.user_id,
                text=text,
                channel="WebSocket",
                session_id=current_context.session_id,
                room_id=current_context.room_id,
                site_id=current_context.site_id,
                visitor_id=current_context.visitor_id,
            ):
                if pending_chunk is not None:
                    await manager.send_json(
                        websocket,
                        assistant_message_event(pending_chunk, current_context, partial=True),
                    )
                pending_chunk = chunk

            if pending_chunk is not None:
                await manager.send_json(
                    websocket,
                    assistant_message_event(pending_chunk, current_context, partial=False),
                )

            await manager.send_json(websocket, typing_stop_event(current_context))
            await manager.send_json(websocket, assistant_state_event(AssistantState.IDLE, current_context))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as exc:  # pragma: no cover - defensive runtime branch
        logger.exception("Websocket failure: %s", exc)
        manager.disconnect(websocket)
