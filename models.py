from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User input text")
    user_id: Optional[str] = Field(default=None, description="Stable user id for memory context")
    channel: str = Field(default="web", description="Origin channel")


class ChatResponse(BaseModel):
    user_id: str
    response: str


class ResetRequest(BaseModel):
    user_id: str
