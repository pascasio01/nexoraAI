from __future__ import annotations

from fastapi import APIRouter, Form, Request

from ai_core import ask_nexora
from config import APP_NAME, MODEL_NAME
import deps
from memory import reset_memory
from models import ChatRequest
from telegram_actor import telegram_health, telegram_webhook

router = APIRouter()


@router.get("/")
async def home():
    return {"app": APP_NAME, "status": "online", "model": MODEL_NAME}


@router.get("/health")
async def health():
    redis_ok = False
    if deps.r:
        try:
            await deps.r.ping()
            redis_ok = True
        except Exception:
            redis_ok = False

    return {
        "status": "ok",
        "server": {"online": True},
        "redis": {"configured": deps.r is not None, "healthy": redis_ok},
        "openai": {"configured": deps.client is not None, "healthy": deps.client is not None},
        "tavily": {"configured": deps.tavily is not None, "healthy": deps.tavily is not None},
        "telegram": telegram_health(),
    }


@router.post("/chat")
async def chat(req: ChatRequest):
    answer = await ask_nexora(user_id=req.user_id, text=req.text, channel=req.channel)
    return {"reply": answer}


@router.post("/reset-web")
async def reset_web(req: ChatRequest):
    await reset_memory(req.user_id)
    return {"ok": True, "message": "Memoria reiniciada."}


@router.post("/whatsapp")
async def whatsapp_webhook(
    body: str = Form(..., alias="Body"),
    sender: str = Form(..., alias="From"),
):
    reply = await ask_nexora(user_id=sender, text=body, channel="whatsapp")
    return {"reply": reply}


@router.post("/tg/{token}")
async def tg_webhook(token: str, request: Request):
    return await telegram_webhook(token, request)
