"""HTTP routes across channels using the shared AI core."""

from __future__ import annotations

import html

from fastapi import APIRouter, Form, Request
from fastapi.responses import Response

from ai_core import ask_nexora, get_personal_agent, send_agent_message, update_agent_permissions
from config import APP_NAME, MODEL_NAME
from deps import openai_client, redis_client, tavily_client
from memory import get_agent_settings, reset_memory, set_agent_settings
from models import AgentMessageEvent, AgentPermissionUpdate, AgentSettings, AgentSettingsUpdate, ChatRequest
from telegram_actor import telegram_status, telegram_webhook

router = APIRouter()


@router.get("/")
async def home():
    return {"app": APP_NAME, "status": "active", "model": MODEL_NAME}


@router.get("/health")
async def health():
    redis_ok = False
    redis_error = None
    if redis_client:
        try:
            redis_ok = bool(await redis_client.ping())
        except Exception as exc:
            redis_error = str(exc)

    services = {
        "redis": {"configured": redis_client is not None, "ok": redis_ok, "error": redis_error},
        "openai": {"configured": openai_client is not None, "ok": openai_client is not None},
        "tavily": {"configured": tavily_client is not None, "ok": tavily_client is not None},
        "telegram": telegram_status(),
    }

    overall_ok = all(
        entry.get("ok", False)
        for entry in services.values()
        if entry.get("configured", False)
    )
    return {
        "ok": overall_ok,
        "overall": "healthy" if overall_ok else "degraded",
        "services": services,
    }


@router.post("/chat")
async def chat(req: ChatRequest):
    answer = await ask_nexora(user_id=req.usuario, text=req.texto, channel=req.channel)
    agent = await get_personal_agent(req.usuario)
    return {"respuesta": answer, "agent_id": agent.agent_id}


@router.post("/reset-web")
async def reset_web(req: ChatRequest):
    await reset_memory(req.usuario)
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
async def tg_route(token: str, request: Request):
    return await telegram_webhook(token=token, request=request)


@router.get("/agents/{user_id}")
async def get_agent(user_id: str):
    descriptor = await get_personal_agent(user_id)
    settings = await get_agent_settings(user_id)
    return {"agent": descriptor.model_dump(), "settings": settings.model_dump()}


@router.patch("/agents/{user_id}/settings")
async def patch_agent_settings(user_id: str, payload: AgentSettingsUpdate):
    current = await get_agent_settings(user_id)
    new_settings = AgentSettings(
        model=payload.model or current.model,
        temperature=payload.temperature if payload.temperature is not None else current.temperature,
        system_prompt=payload.system_prompt if payload.system_prompt is not None else current.system_prompt,
    )
    saved = await set_agent_settings(user_id, new_settings)
    return {"ok": True, "settings": saved.model_dump()}


@router.patch("/agents/{user_id}/permissions")
async def patch_agent_permissions(user_id: str, payload: AgentPermissionUpdate):
    descriptor = await update_agent_permissions(
        user_id=user_id,
        tools_list=payload.tools,
        permissions=payload.permissions,
    )
    return {"ok": True, "agent": descriptor.model_dump()}


@router.post("/agents/message")
async def agent_message(event: AgentMessageEvent):
    result = await send_agent_message(event)
    return result
