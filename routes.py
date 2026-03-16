import html

from fastapi import APIRouter, Form, Request, Response
from pydantic import BaseModel, Field

from ai_core import ask_nexora, save_personal_note
from config import APP_NAME, MODEL_NAME
from memory import (
    get_assistant_settings,
    get_profile,
    normalize_user_id,
    reset_memory,
    set_assistant_settings,
    set_profile,
)
from telegram_actor import telegram_webhook

router = APIRouter()


class ChatRequest(BaseModel):
    texto: str = Field(min_length=1)
    user_id: str | None = None
    usuario: str | None = None


class ProfileRequest(BaseModel):
    user_id: str
    profile: str


class SettingsRequest(BaseModel):
    user_id: str
    settings: dict


class PersonalMemoryRequest(BaseModel):
    user_id: str
    note: str


def _resolve_user_id(req: ChatRequest) -> str:
    return normalize_user_id(req.user_id or req.usuario)


@router.get("/")
async def home():
    return {"app": APP_NAME, "status": "active", "model": MODEL_NAME}


@router.get("/health")
async def health():
    return {"ok": True}


@router.post("/chat")
async def chat(req: ChatRequest):
    user_id = _resolve_user_id(req)
    answer = await ask_nexora(user_id=user_id, text=req.texto, channel="Web")
    return {"respuesta": answer, "user_id": user_id}


@router.post("/reset-web")
async def reset_web(req: ChatRequest):
    user_id = _resolve_user_id(req)
    await reset_memory(user_id)
    return {"ok": True, "mensaje": "Memoria reiniciada.", "user_id": user_id}


@router.get("/profile/{user_id}")
async def read_profile(user_id: str):
    return {"user_id": user_id, "profile": await get_profile(user_id)}


@router.post("/profile")
async def update_profile(req: ProfileRequest):
    await set_profile(req.user_id, req.profile)
    return {"ok": True, "user_id": req.user_id}


@router.get("/assistant-settings/{user_id}")
async def read_assistant_settings(user_id: str):
    return {"user_id": user_id, "settings": await get_assistant_settings(user_id)}


@router.post("/assistant-settings")
async def update_assistant_settings(req: SettingsRequest):
    settings = await set_assistant_settings(req.user_id, req.settings)
    return {"ok": True, "user_id": req.user_id, "settings": settings}


@router.post("/personal-memory")
async def add_personal_memory(req: PersonalMemoryRequest):
    await save_personal_note(req.user_id, req.note)
    return {"ok": True, "user_id": req.user_id}


@router.post("/whatsapp")
async def whatsapp_webhook(
    body: str = Form(..., alias="Body"), sender: str = Form(..., alias="From")
):
    answer = await ask_nexora(user_id=sender, text=body, channel="WhatsApp")
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{html.escape(answer)}</Message>
</Response>"""
    return Response(content=twiml, media_type="application/xml")


@router.post("/tg/{token}")
async def tg_webhook(token: str, request: Request):
    return await telegram_webhook(token, request)
