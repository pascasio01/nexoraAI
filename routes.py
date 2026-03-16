import html

from fastapi import APIRouter, Form, Response

from ai_core import ask_nexora
from config import APP_NAME, MODEL_NAME
from memory import reset_memory
from models import AssistantSettings, ChatRequest

router = APIRouter()


@router.get("/")
async def home():
    return {"app": APP_NAME, "status": "active", "model": MODEL_NAME}


@router.get("/health")
async def health():
    return {"ok": True, "realtime": True}


@router.post("/chat")
async def chat(req: ChatRequest):
    answer = await ask_nexora(req.usuario, req.texto, "Web")
    return {"respuesta": answer}


@router.post("/reset-web")
async def reset_web(req: ChatRequest):
    await reset_memory(req.usuario)
    return {"ok": True, "mensaje": "Memoria reiniciada."}


@router.get("/assistant-settings", response_model=AssistantSettings)
async def assistant_settings() -> AssistantSettings:
    return AssistantSettings(model=MODEL_NAME, app=APP_NAME)


@router.get("/realtime/events")
async def realtime_events_contract():
    return {
        "envelope": {
            "event": "message.user | message.assistant | assistant.state | typing.start | typing.stop | error",
            "timestamp": "ISO-8601",
            "user_id": "string",
            "session_id": "string",
            "room_id": "string|null",
            "site_id": "string|null",
            "visitor_id": "string|null",
            "data": "object",
        }
    }


@router.post("/whatsapp")
async def whatsapp_webhook(Body: str = Form(...), From: str = Form(...)):
    answer = await ask_nexora(From, Body, "WhatsApp")
    safe_answer = html.escape(answer)
    twiml = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Response>
    <Message>{safe_answer}</Message>
</Response>"""
    return Response(content=twiml, media_type="application/xml")
