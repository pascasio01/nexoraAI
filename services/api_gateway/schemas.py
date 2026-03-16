from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    device_name: str = "Web Browser"
    device_platform: str = "web"


class RefreshRequest(BaseModel):
    refresh_token: str


class ProfileUpdateRequest(BaseModel):
    full_name: str = Field(min_length=2)


class ConversationCreateRequest(BaseModel):
    title: str = Field(min_length=1)


class MessageCreateRequest(BaseModel):
    content: str = Field(min_length=1)


class MemoryCreateRequest(BaseModel):
    tier: Literal["short_term", "mid_term", "long_term"]
    content: str = Field(min_length=1)
    summary: str = ""
    importance: int = Field(default=1, ge=1, le=5)
    sensitive: bool = False


class TaskCreateRequest(BaseModel):
    title: str = Field(min_length=1)
    due_at: str | None = None


class TaskUpdateRequest(BaseModel):
    status: Literal["pending", "in_progress", "done"]


class DeviceUpsertRequest(BaseModel):
    name: str
    platform: str


class NotificationReadRequest(BaseModel):
    notification_id: int
