from xml.sax.saxutils import escape

from fastapi import APIRouter, Form, Request, Response
from pydantic import BaseModel

from ai_core import ask_nexora
from config import APP_NAME, MODEL_NAME
from deps import client, r, tavily
from memory import reset_memory
from telegram_actor import telegram_status, telegram_webhook

router = APIRouter()


class ChatRequest(BaseModel):
    user_id: str
    text: str = ""


@router.get("/")
async def home():
    return {"app": APP_NAME, "status": "online", "model": MODEL_NAME}


@router.get("/health")
async def health():
    redis_connected = False
    if r is not None:
        try:
            redis_connected = bool(await r.ping())
        except Exception:
            redis_connected = False

    telegram = await telegram_status()

    services = {
        "redis": {"enabled": r is not None, "connected": redis_connected},
        "openai": {"enabled": client is not None},
        "tavily": {"enabled": tavily is not None},
        "telegram": telegram,
    }

    overall = "ok"
    if client is None:
        overall = "degraded"

    return {"status": overall, "services": services}


@router.post("/chat")
async def chat(req: ChatRequest):
    response = await ask_nexora(req.user_id, req.text)
    return {"response": response}


@router.post("/reset-web")
async def reset_web(req: ChatRequest):
    cleared = await reset_memory(req.user_id)
    message = "Memoria reiniciada" if cleared else "Memoria desactivada o no disponible"
    return {"ok": cleared, "message": message}


@router.post("/whatsapp")
async def whatsapp_webhook(message_body: str = Form(..., alias="Body"), sender: str = Form(..., alias="From")):
    response_text = await ask_nexora(sender, message_body)
    twiml = f"<Response><Message>{escape(response_text)}</Message></Response>"
    return Response(content=twiml, media_type="application/xml")


@router.post("/tg/{token}")
async def tg_webhook(token: str, request: Request):
    return await telegram_webhook(token, request)
