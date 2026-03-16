"""Pydantic models for API and assistant state."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AssistantConfig(BaseModel):
    """Per-user assistant settings."""

    model: str = Field(default="")
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    enabled_tools: list[str] = Field(default_factory=list)
    denied_tools: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)


class UserProfile(BaseModel):
    """Long-term user profile information."""

    user_id: str
    summary: str = "New user."
    preferences: dict[str, str] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    """Unified inbound message model for all channels."""

    text: str = Field(..., alias="texto")
    user_id: str = Field(default="web_user", alias="usuario")
    session_id: str = "default"
    channel: str = "web"

    class Config:
        populate_by_name = True


class ChatResponse(BaseModel):
    """Chat response payload."""

    reply: str
    user_id: str
    session_id: str
    channel: str


class ToolRegistrationRequest(BaseModel):
    """Metadata-only plugin tool registration payload."""

    plugin_name: str
    tool_name: str
    description: str
