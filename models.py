from pydantic import BaseModel, Field, model_validator


class ChatRequest(BaseModel):
    texto: str = Field(..., min_length=0)
    usuario: str = "web_user"

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_fields(cls, data):
        if isinstance(data, dict):
            if "texto" not in data and "text" in data:
                data["texto"] = data["text"]
            if "usuario" not in data and "user_id" in data:
                data["usuario"] = data["user_id"]
        return data
