from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class AssistantState(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    RESPONDING = "responding"


RealtimeEventType = Literal[
    "message.user",
    "message.assistant",
    "assistant.state",
    "typing.start",
    "typing.stop",
    "error",
]


class RealtimeContext(BaseModel):
    user_id: str
    session_id: str
    room_id: str | None = None
    site_id: str | None = None
    visitor_id: str | None = None


class RealtimeEvent(BaseModel):
    event: RealtimeEventType
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    user_id: str
    session_id: str
    room_id: str | None = None
    site_id: str | None = None
    visitor_id: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
