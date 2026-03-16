from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    text: str = Field(min_length=1)
    user_id: str = "web_user"
