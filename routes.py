from __future__ import annotations

import html

from fastapi import APIRouter, Form, HTTPException, Request, Response

from ai_core import ask_nexora
from config import APP_NAME, MODEL_NAME
from deps import client, r
from memory import reset_memory
from models import ChatRequest
from telegram_actor import telegram_webhook

router = APIRouter()


@router.get("/")
async def home():
    return {"app": APP_NAME, "status": "active", "model": MODEL_NAME}


@router.get("/health")
async def health():
    redis_ok = False
    try:
        if r:
            redis_ok = await r.ping()
    except Exception:
        redis_ok = False
    return {
        "ok": True,
        "redis": redis_ok,
        "openai": client is not None,
    }


@router.post("/chat")
async def chat(req: ChatRequest):
    try:
        answer = await ask_nexora(req.usuario, req.texto, "Web")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"chat_failed: {exc}") from exc
    return {"respuesta": answer}


@router.post("/reset-web")
async def reset_web(req: ChatRequest):
    await reset_memory(req.usuario)
    return {"ok": True, "mensaje": "Memoria reiniciada."}


@router.post("/whatsapp")
async def whatsapp_webhook(Body: str = Form(...), From: str = Form(...)):
    try:
        answer = await ask_nexora(From, Body, "WhatsApp")
        payload = answer
    except Exception as exc:
        payload = str(exc)

    twiml = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Response>
    <Message>{html.escape(payload)}</Message>
</Response>"""
    return Response(content=twiml, media_type="application/xml")


@router.post("/tg/{token}")
async def tg_webhook(token: str, request: Request):
    return await telegram_webhook(token, request)
