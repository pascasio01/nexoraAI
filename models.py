from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    channel: str = Field(default="web")


class ToolRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    tool_name: str = Field(..., min_length=1)
    arguments: dict = Field(default_factory=dict)


class ProfileRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    profile: str = Field(..., min_length=1)


class SettingsRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    settings: dict = Field(default_factory=dict)


class MemoryRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    memory: str = Field(..., min_length=1)
