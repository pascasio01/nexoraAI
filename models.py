from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ChatRequest(BaseModel):
    texto: str
    usuario: str = "web_user"
    channel: str = "Web"


class AgentSettings(BaseModel):
    model_name: str | None = None
    temperature: float = 0.4
    max_tokens: int = 450
    system_prompt_suffix: str = ""


class AgentRecord(BaseModel):
    user_id: str
    agent_id: str
    endpoint: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    tools_allowed: list[str] = Field(default_factory=list)
    permissions: dict[str, bool] = Field(default_factory=dict)
    created_at: str = Field(default_factory=_utc_now_iso)


class AgentEvent(BaseModel):
    from_agent_id: str
    to_agent_id: str
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: str = Field(default_factory=_utc_now_iso)


class AgentSettingsUpdate(BaseModel):
    settings: AgentSettings


class AgentPermissionsUpdate(BaseModel):
    tools_allowed: list[str] = Field(default_factory=list)
    permissions: dict[str, bool] = Field(default_factory=dict)


class ToolExecutionRequest(BaseModel):
    user_id: str
    tool_name: str
    args: dict[str, Any] = Field(default_factory=dict)


class AgentMessageRequest(BaseModel):
    from_user_id: str
    to_agent_id: str
    event_type: str = "task_request"
    payload: dict[str, Any] = Field(default_factory=dict)
