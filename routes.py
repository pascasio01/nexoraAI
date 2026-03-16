import html

from fastapi import APIRouter, Form, Request, Response

from ai_core import ask_nexora
from config import APP_NAME, MODEL_NAME
from deps import client, r
from memory import build_conversation_key, reset_memory
from models import ChatRequest
from telegram_actor import telegram_webhook

router = APIRouter()


@router.get("/")
async def home():
    return {"app": APP_NAME, "status": "active", "model": MODEL_NAME}


@router.get("/health")
async def health():
    redis_ok = False
    if r is not None:
        try:
            redis_ok = bool(await r.ping())
        except Exception:
            pass

    return {
        "ok": True,
        "redis": redis_ok,
        "openai": client is not None,
        "realtime": True,
    }


@router.post("/chat")
async def chat(req: ChatRequest):
    answer = await ask_nexora(
        user_id=req.usuario,
        text=req.texto,
        channel="Web",
        session_id=req.session_id,
        room_id=req.room_id,
        site_id=req.site_id,
        visitor_id=req.visitor_id,
    )
    return {"respuesta": answer}


@router.post("/reset-web")
async def reset_web(req: ChatRequest):
    conversation_id = build_conversation_key(
        user_id=req.usuario,
        session_id=req.session_id,
        room_id=req.room_id,
        site_id=req.site_id,
        visitor_id=req.visitor_id,
    )
    await reset_memory(req.usuario, conversation_id=conversation_id)
    return {"ok": True, "mensaje": "Memoria reiniciada."}


@router.post("/whatsapp")
async def whatsapp_webhook(Body: str = Form(...), From: str = Form(...)):
    answer = await ask_nexora(user_id=From, text=Body, channel="WhatsApp")
    twiml = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Response>
    <Message>{html.escape(answer)}</Message>
</Response>"""
    return Response(content=twiml, media_type="application/xml")


@router.post("/tg/{token}")
async def tg_webhook(token: str, request: Request):
    return await telegram_webhook(token, request)
