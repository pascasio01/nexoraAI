from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    text: str = Field(min_length=1)
    user_id: str = "web_user"
    channel: str = "web"
    assistant_id: str = "default"


class ResetRequest(BaseModel):
    user_id: str = "web_user"
    assistant_id: str = "default"


class AssistantSettingsRequest(BaseModel):
    user_id: str
    assistant_id: str = "default"
    tone: str | None = None
    language: str | None = None
    goals: list[str] | None = None


class PersonalMemoryRequest(BaseModel):
    user_id: str
    assistant_id: str = "default"
    kind: str = "note"
    content: str = Field(min_length=1)


class ToolExecutionRequest(BaseModel):
    user_id: str
    assistant_id: str = "default"
    tool_name: str
    arguments: dict = Field(default_factory=dict)
