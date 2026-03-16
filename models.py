from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    texto: str = Field(..., min_length=1)
    usuario: str = "web_user"
    session_id: str | None = None
    room_id: str | None = None
    site_id: str | None = None
    visitor_id: str | None = None


class ChatResponse(BaseModel):
    respuesta: str
