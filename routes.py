import html

from fastapi import APIRouter, Form, Request, Response

from ai_core import ask_nexora
from config import APP_NAME, MODEL_NAME
from deps import client, r, tavily
from memory import reset_memory
from models import ChatRequest
from telegram_actor import telegram_is_running, telegram_webhook

router = APIRouter()


@router.get("/")
async def home():
    return {"app": APP_NAME, "status": "active", "model": MODEL_NAME}


@router.get("/health")
async def health():
    redis_ok = False
    try:
        if r:
            await r.ping()
            redis_ok = True
    except Exception:
        redis_ok = False

    return {
        "status": "ok",
        "redis": redis_ok,
        "openai": client is not None,
        "tavily": tavily is not None,
        "telegram": telegram_is_running(),
    }


@router.post("/chat")
async def chat(req: ChatRequest):
    try:
        answer = await ask_nexora(req.usuario or "web_user", req.texto, "Web")
        return {"respuesta": answer}
    except Exception as exc:
        return {"error": str(exc)}


@router.post("/reset-web")
async def reset_web(req: ChatRequest):
    await reset_memory(req.usuario or "web_user")
    return {"ok": True, "mensaje": "Memoria reiniciada."}


@router.post("/whatsapp")
async def whatsapp_webhook(Body: str = Form(...), From: str = Form(...)):
    try:
        answer = await ask_nexora(From, Body, "WhatsApp")
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{html.escape(answer)}</Message>
</Response>"""
        return Response(content=twiml, media_type="application/xml")
    except Exception as exc:
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{html.escape(str(exc))}</Message>
</Response>"""
        return Response(content=twiml, media_type="application/xml")


@router.post("/tg/{token}")
async def tg_webhook(token: str, request: Request):
    return await telegram_webhook(token, request)
