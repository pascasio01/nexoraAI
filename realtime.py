import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket


ASSISTANT_STATES = {"idle", "listening", "thinking", "responding"}


@dataclass(slots=True)
class VoiceStreamHooks:
    """Interface placeholders for future voice streaming."""

    async def on_voice_input_chunk(self, room_id: str, session_id: str, chunk_meta: dict[str, Any]) -> None:  # pragma: no cover
        return None

    async def on_voice_output_chunk(self, room_id: str, session_id: str, chunk_meta: dict[str, Any]) -> None:  # pragma: no cover
        return None


class RealtimeConnectionManager:
    def __init__(self) -> None:
        self._rooms: dict[str, set[WebSocket]] = defaultdict(set)
        self._session_room: dict[str, str] = {}

    async def connect(self, websocket: WebSocket, room_id: str, session_id: str) -> None:
        await websocket.accept()
        self._rooms[room_id].add(websocket)
        self._session_room[session_id] = room_id

    def disconnect(self, websocket: WebSocket, room_id: str, session_id: str) -> None:
        self._rooms[room_id].discard(websocket)
        if not self._rooms[room_id]:
            self._rooms.pop(room_id, None)
        self._session_room.pop(session_id, None)

    async def broadcast_room(self, room_id: str, event: dict[str, Any]) -> None:
        payload = json.dumps(event)
        dead: list[WebSocket] = []
        for ws in self._rooms.get(room_id, set()):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._rooms[room_id].discard(ws)


manager = RealtimeConnectionManager()
voice_hooks = VoiceStreamHooks()


def build_event(event_type: str, room_id: str, session_id: str, **data: Any) -> dict[str, Any]:
    event = {
        "event": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "room_id": room_id,
        "session_id": session_id,
    }
    event.update(data)
    return event
