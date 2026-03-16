from __future__ import annotations

import json
import uuid
from collections import defaultdict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ai_core import stream_assistant_events
from config import logger
from events import build_event
from realtime_types import AssistantState, RealtimeContext

router = APIRouter(tags=["realtime"])


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, tuple[WebSocket, RealtimeContext]] = {}
        self._session_connections: dict[str, set[str]] = defaultdict(set)
        self._room_connections: dict[str, set[str]] = defaultdict(set)

    async def connect(self, websocket: WebSocket, context: RealtimeContext) -> str:
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        self._connections[connection_id] = (websocket, context)
        self._session_connections[context.session_id].add(connection_id)
        if context.room_id:
            self._room_connections[context.room_id].add(connection_id)
        return connection_id

    def disconnect(self, connection_id: str) -> None:
        entry = self._connections.pop(connection_id, None)
        if not entry:
            return
        _, context = entry
        self._session_connections[context.session_id].discard(connection_id)
        if not self._session_connections[context.session_id]:
            self._session_connections.pop(context.session_id, None)

        if context.room_id:
            self._room_connections[context.room_id].discard(connection_id)
            if not self._room_connections[context.room_id]:
                self._room_connections.pop(context.room_id, None)

    async def send_to_connection(self, connection_id: str, payload: dict) -> None:
        entry = self._connections.get(connection_id)
        if not entry:
            return
        websocket, _ = entry
        await websocket.send_json(payload)

    async def send_to_session(self, session_id: str, payload: dict) -> None:
        for connection_id in list(self._session_connections.get(session_id, ())):
            await self.send_to_connection(connection_id, payload)


manager = ConnectionManager()


def _build_context(websocket: WebSocket, room_id: str | None = None) -> RealtimeContext:
    params = websocket.query_params
    user_id = params.get("user_id") or "web_user"
    session_id = params.get("session_id") or f"session-{user_id}"
    return RealtimeContext(
        user_id=user_id,
        session_id=session_id,
        room_id=room_id or params.get("room_id"),
        site_id=params.get("site_id"),
        visitor_id=params.get("visitor_id"),
    )


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await _websocket_handler(websocket, room_id=None)


@router.websocket("/ws/{room_id}")
async def websocket_room_endpoint(websocket: WebSocket, room_id: str) -> None:
    await _websocket_handler(websocket, room_id=room_id)


async def _websocket_handler(websocket: WebSocket, room_id: str | None) -> None:
    context = _build_context(websocket, room_id=room_id)
    connection_id = await manager.connect(websocket, context)

    await manager.send_to_connection(
        connection_id,
        build_event("assistant.state", context, {"state": AssistantState.IDLE.value}).model_dump(),
    )

    try:
        while True:
            raw_message = await websocket.receive_text()
            try:
                incoming = json.loads(raw_message)
            except json.JSONDecodeError:
                await manager.send_to_connection(
                    connection_id,
                    build_event("error", context, {"message": "Invalid JSON payload"}).model_dump(),
                )
                continue

            if incoming.get("event") != "message.user":
                await manager.send_to_connection(
                    connection_id,
                    build_event("error", context, {"message": "Unsupported event type"}).model_dump(),
                )
                continue

            text = str((incoming.get("data") or {}).get("text") or "").strip()
            if not text:
                await manager.send_to_connection(
                    connection_id,
                    build_event("error", context, {"message": "message.user requires non-empty data.text"}).model_dump(),
                )
                continue

            await manager.send_to_session(
                context.session_id,
                build_event("message.user", context, {"text": text}).model_dump(),
            )

            async for event in stream_assistant_events(context=context, user_text=text, channel="WebSocket"):
                await manager.send_to_session(context.session_id, event)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected user=%s session=%s", context.user_id, context.session_id)
    except Exception as exc:
        logger.exception("WebSocket error user=%s session=%s error=%s", context.user_id, context.session_id, exc)
        await manager.send_to_connection(
            connection_id,
            build_event("error", context, {"message": "Internal realtime error"}).model_dump(),
        )
    finally:
        manager.disconnect(connection_id)
