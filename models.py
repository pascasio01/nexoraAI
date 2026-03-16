from pydantic import BaseModel


class ChatRequest(BaseModel):
    texto: str
    usuario: str | None = "web_user"
