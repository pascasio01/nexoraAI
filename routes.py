from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from ai_core import ask_nexora
from config import APP_NAME, MODEL_NAME
from deps import get_openai_client, get_redis, get_tavily
from memory import reset_memory
from models import ChatRequest, ChatResponse, ResetRequest
from telegram_actor import telegram_is_active, telegram_webhook

router = APIRouter()


@router.get("/")
async def home() -> dict:
    return {"app": APP_NAME, "status": "online", "model": MODEL_NAME}


@router.get("/health")
async def health() -> dict:
    redis_ok = False
    redis_client = get_redis()
    if redis_client is not None:
        try:
            redis_ok = bool(await redis_client.ping())
        except Exception:
            redis_ok = False

    return {
        "status": "ok",
        "services": {
            "redis": redis_ok,
            "openai": get_openai_client() is not None,
            "tavily": get_tavily() is not None,
            "telegram": telegram_is_active(),
        },
    }


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    user_id = (req.user_id or "").strip() or "web-user"
    response = await ask_nexora(user_id=user_id, text=req.message, channel=req.channel)
    return ChatResponse(user_id=user_id, response=response)


@router.post("/reset")
async def reset(req: ResetRequest) -> dict:
    await reset_memory(req.user_id)
    return {"status": "ok", "user_id": req.user_id}


@router.post("/tg/{token}")
async def tg_webhook(token: str, request: Request) -> dict:
    ok = await telegram_webhook(token, request)
    if not ok:
        raise HTTPException(status_code=403, detail="invalid or inactive telegram webhook")
    return {"ok": True}
