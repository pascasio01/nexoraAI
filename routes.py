from fastapi import APIRouter, Request

from ai_core import ask_nexora
from config import APP_NAME, MODEL_NAME
from deps import get_integrations_status, get_redis
from memory import load_chat_memory, reset_memory
from models import ChatRequest
from telegram_actor import telegram_enabled, telegram_webhook

router = APIRouter()


@router.get("/")
async def home():
    return {"app": APP_NAME, "status": "online", "model": MODEL_NAME}


@router.get("/health")
async def health():
    status = get_integrations_status()

    redis_ok = False
    redis_client = get_redis()
    if redis_client is not None:
        try:
            await redis_client.ping()
            redis_ok = True
        except Exception:
            redis_ok = False

    return {
        "status": "ok",
        "redis": redis_ok,
        "openai": status["openai"],
        "tavily": status["tavily"],
        "telegram": telegram_enabled(),
    }


@router.post("/chat")
async def chat(req: ChatRequest):
    answer = await ask_nexora(req.user_id, req.text, "web")
    return {"answer": answer}


@router.post("/memory/reset")
async def reset(req: ChatRequest):
    await reset_memory(req.user_id)
    return {"ok": True}


@router.get("/memory/{user_id}")
async def memory(user_id: str):
    return {"items": await load_chat_memory(user_id)}


@router.post("/tg/{token}")
async def tg_webhook(token: str, request: Request):
    return await telegram_webhook(token, request)
