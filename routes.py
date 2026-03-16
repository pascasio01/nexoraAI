from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ai_core import ask_nexora, openai_enabled, tavily_enabled
from config import APP_NAME, MODEL_NAME
from memory import redis_healthcheck
from telegram_actor import telegram_is_running, telegram_webhook

router = APIRouter()


class ChatRequest(BaseModel):
    text: str | None = None
    texto: str | None = None
    user: str | None = None
    usuario: str | None = None
    use_web_search: bool = False


@router.get("/")
async def home():
    return {"app": APP_NAME, "status": "online", "model": MODEL_NAME}


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "redis": await redis_healthcheck(),
        "openai": openai_enabled(),
        "tavily": tavily_enabled(),
        "telegram": telegram_is_running(),
    }


@router.post("/chat")
async def chat(req: ChatRequest):
    message = req.text or req.texto
    if not message:
        raise HTTPException(status_code=400, detail="Missing chat text")

    user_id = req.user or req.usuario or "web_user"
    answer = await ask_nexora(
        user_id=user_id,
        text=message,
        channel="web",
        use_web_search=req.use_web_search,
    )
    return {"respuesta": answer}


@router.post("/tg/{token}")
async def tg_webhook(token: str, request: Request):
    return await telegram_webhook(token, request)
