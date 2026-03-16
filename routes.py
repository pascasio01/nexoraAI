import html

from fastapi import APIRouter, Form, Header, Request, Response

from ai_core import ask_nexora, resolve_user_id
from config import APP_NAME, MODEL_NAME
from deps import client, r, tavily
from memory import (
    get_assistant_settings,
    get_profile,
    get_user_session,
    reset_memory,
    set_assistant_settings,
    set_profile,
)
from models import AssistantSettingsUpdate, ChannelContext, ChannelName, ChatRequest, UserProfileUpdate
from telegram_actor import telegram_webhook, tg_app

router = APIRouter()


@router.get("/")
async def home():
    return {"app": APP_NAME, "status": "online", "model": MODEL_NAME}


@router.get("/health")
async def health():
    redis_ok = False
    if r is not None:
        try:
            redis_ok = bool(await r.ping())
        except Exception:
            redis_ok = False
    return {
        "status": "ok",
        "redis": redis_ok,
        "openai": client is not None,
        "tavily": tavily is not None,
        "telegram": tg_app is not None,
    }


@router.post("/chat")
async def chat(req: ChatRequest, authorization: str | None = Header(default=None)):
    user_id = resolve_user_id(req.usuario, authorization)
    answer = await ask_nexora(user_id, req.texto, req.channel.value)
    return {"respuesta": answer, "user_id": user_id}


@router.post("/reset-web")
async def reset_web(req: ChatRequest, authorization: str | None = Header(default=None)):
    user_id = resolve_user_id(req.usuario, authorization)
    await reset_memory(user_id)
    return {"ok": True, "mensaje": "Memoria reiniciada.", "user_id": user_id}


@router.get("/profile")
async def profile_get(usuario: str, authorization: str | None = Header(default=None)):
    user_id = resolve_user_id(usuario, authorization)
    return {"user_id": user_id, "profile": await get_profile(user_id)}


@router.post("/profile")
async def profile_set(payload: UserProfileUpdate, usuario: str, authorization: str | None = Header(default=None)):
    user_id = resolve_user_id(usuario, authorization)
    await set_profile(user_id, payload.profile)
    return {"ok": True, "user_id": user_id}


@router.get("/assistant-settings")
async def assistant_settings_get(usuario: str, authorization: str | None = Header(default=None)):
    user_id = resolve_user_id(usuario, authorization)
    return {"user_id": user_id, "settings": await get_assistant_settings(user_id)}


@router.post("/assistant-settings")
async def assistant_settings_set(payload: AssistantSettingsUpdate, usuario: str, authorization: str | None = Header(default=None)):
    user_id = resolve_user_id(usuario, authorization)
    settings = await set_assistant_settings(user_id, payload.model_dump())
    return {"ok": True, "user_id": user_id, "settings": settings}


@router.get("/personal-memory")
async def personal_memory(usuario: str, authorization: str | None = Header(default=None)):
    user_id = resolve_user_id(usuario, authorization)
    return {"user_id": user_id, "session": await get_user_session(user_id)}


@router.get("/channels/capabilities")
async def channel_capabilities():
    channels = [
        ChannelContext(name=ChannelName.web),
        ChannelContext(name=ChannelName.mobile),
        ChannelContext(name=ChannelName.whatsapp),
        ChannelContext(name=ChannelName.telegram, supports_voice_input=True),
        ChannelContext(name=ChannelName.voice, supports_voice_input=True, supports_voice_output=True),
        ChannelContext(name=ChannelName.avatar, supports_voice_input=True, supports_voice_output=True, supports_avatar=True),
    ]
    return {"channels": [c.model_dump() for c in channels]}


@router.get("/voice/capabilities")
async def voice_capabilities():
    return {
        "prepared": True,
        "transcription": client is not None,
        "synthesis": False,
        "wake_phrase": "not_implemented",
    }


@router.get("/avatar/capabilities")
async def avatar_capabilities():
    return {
        "prepared": True,
        "floating_widget": "not_implemented",
        "presence_sync": "not_implemented",
        "lip_sync": "not_implemented",
    }


@router.post("/whatsapp")
async def whatsapp_webhook(Body: str = Form(...), From: str = Form(...)):
    answer = await ask_nexora(From, Body, "whatsapp")
    twiml = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Response>
    <Message>{html.escape(answer)}</Message>
</Response>"""
    return Response(content=twiml, media_type="application/xml")


@router.post("/tg/{token}")
async def tg_webhook(token: str, request: Request):
    return await telegram_webhook(token, request)
