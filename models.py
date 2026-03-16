"""Pydantic models for requests, users, and personal agents."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    texto: str = Field(..., min_length=1)
    usuario: str = Field(default="web_user")
    channel: str = Field(default="Web")


class AgentSettings(BaseModel):
    model: str = "gpt-4o-mini"
    temperature: float = 0.4
    system_prompt: str | None = None


class AgentDescriptor(BaseModel):
    user_id: str
    agent_id: str
    endpoint: str
    capabilities: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    permissions: dict[str, bool] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentMessageEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event_type: Literal["task_request", "task_result", "info_exchange", "schedule"]
    from_agent_id: str
    to_agent_id: str
    payload: dict[str, Any] = Field(default_factory=dict)


class AgentSettingsUpdate(BaseModel):
    model: str | None = None
    temperature: float | None = None
    system_prompt: str | None = None


class AgentPermissionUpdate(BaseModel):
    tools: list[str] | None = None
    permissions: dict[str, bool] | None = None
