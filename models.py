from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ChannelName(str, Enum):
    web = "web"
    whatsapp = "whatsapp"
    telegram = "telegram"
    mobile = "mobile"
    voice = "voice"
    avatar = "avatar"


class ChatRequest(BaseModel):
    texto: str = Field(min_length=1)
    usuario: Optional[str] = "web_user"
    channel: ChannelName = ChannelName.web


class UserProfileUpdate(BaseModel):
    profile: str


class AssistantSettingsUpdate(BaseModel):
    tone: str = "premium"
    response_length: str = "balanced"
    voice_enabled: bool = False
    avatar_enabled: bool = False


class ChannelContext(BaseModel):
    name: ChannelName
    trusted: bool = False
    supports_voice_input: bool = False
    supports_voice_output: bool = False
    supports_avatar: bool = False
