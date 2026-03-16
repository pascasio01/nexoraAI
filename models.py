from pydantic import BaseModel, ConfigDict, Field, model_validator


class ChatRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    user_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    usuario: str | None = Field(default=None, exclude=True)
    texto: str | None = Field(default=None, exclude=True)

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_fields(cls, data):
        if isinstance(data, dict):
            data = {**data}
            data.setdefault("user_id", data.get("usuario"))
            data.setdefault("message", data.get("texto"))
        return data


class ChatResponse(BaseModel):
    reply: str
