import html

from fastapi import APIRouter, Form, Request, Response
from pydantic import BaseModel

from config import APP_NAME, MODEL_NAME, r, logger
from ai_core import ask_nexora
from memory import reset_memory
from telegram_actor import telegram_webhook


class ChatRequest(BaseModel):
    texto: str
    usuario: str | None = "web_user"


router = APIRouter()


@router.get("/")
async def home():
    return {"app": APP_NAME, "status": "online", "model": MODEL_NAME}


@router.get("/health")
async def health():
    redis_ok = False
    try:
        if r:
            await r.ping()
            redis_ok = True
    except Exception:
        redis_ok = False
    return {"ok": True, "redis": redis_ok}


@router.post("/chat")
async def chat(req: ChatRequest):
    try:
        answer = await ask_nexora(req.usuario or "web_user", req.texto, "Web")
        return {"respuesta": answer}
    except Exception as e:
        logger.error(f"Error /chat: {e}")
        return {"error": str(e)}


@router.post("/reset-web")
async def reset_web(req: ChatRequest):
    await reset_memory(req.usuario or "web_user")
    return {"ok": True, "mensaje": "Memoria reiniciada."}


# =========================
# WHATSAPP (Twilio)
# =========================
@router.post("/whatsapp")
async def whatsapp_webhook(Body: str = Form(...), From: str = Form(...)):
    try:
        answer = await ask_nexora(From, Body, "WhatsApp")
    except Exception as e:
        answer = str(e)
    twiml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        f"<Message>{html.escape(answer)}</Message>"
        "</Response>"
    )
    return Response(content=twiml, media_type="application/xml")


# =========================
# TELEGRAM WEBHOOK
# =========================
@router.post("/tg/{token}")
async def tg_webhook(token: str, request: Request):
    return await telegram_webhook(token, request)
