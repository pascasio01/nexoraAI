import html
import time

from fastapi import APIRouter, Form, Response

from ai_core import ask_nexora
from config import APP_NAME, ENVIRONMENT, MODEL_NAME
from deps import redis_healthy, service_flags
from memory import reset_memory
from models import ChatRequest
import telegram_actor

router = APIRouter()
_started_at = time.time()


@router.get("/")
async def home():
    return {"app": APP_NAME, "status": "online", "model": MODEL_NAME}


@router.get("/health")
async def health():
    flags = service_flags()
    flags["redis"] = await redis_healthy()
    flags["telegram"] = telegram_actor.tg_app is not None

    return {
        "status": "ok",
        "environment": ENVIRONMENT,
        "uptime_seconds": round(time.time() - _started_at, 2),
        "services": flags,
    }


@router.post("/chat")
async def chat(req: ChatRequest):
    user_id = req.usuario or "web_user"
    answer = await ask_nexora(user_id, req.texto, "web")
    return {"respuesta": answer}


@router.post("/reset-web")
async def reset_web(req: ChatRequest):
    await reset_memory(req.usuario or "web_user")
    return {"ok": True, "mensaje": "Memoria reiniciada."}


@router.post("/whatsapp")
async def whatsapp_webhook(Body: str = Form(...), From: str = Form(...)):
    try:
        answer = await ask_nexora(From, Body, "whatsapp")
        twiml = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Response>
    <Message>{html.escape(answer)}</Message>
</Response>"""
    except Exception as exc:
        twiml = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Response>
    <Message>{html.escape(str(exc))}</Message>
</Response>"""
    return Response(content=twiml, media_type="application/xml")


@router.post("/tg/{token}")
async def tg_webhook(token: str, request):
    return await telegram_actor.telegram_webhook(token, request)
