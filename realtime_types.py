from enum import Enum

from pydantic import BaseModel, Field


class AssistantState(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    RESPONDING = "responding"


class ConnectionContext(BaseModel):
    user_id: str = "anonymous"
    session_id: str | None = None
    room_id: str | None = None
    site_id: str | None = None
    visitor_id: str | None = None
    device_id: str | None = None


class EventEnvelope(BaseModel):
    event: str
    data: dict = Field(default_factory=dict)
    meta: dict = Field(default_factory=dict)
