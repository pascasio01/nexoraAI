from __future__ import annotations

from fastapi import APIRouter, Form, Request

from ai_core import (
    ask_nexora,
    configure_agent_permissions,
    execute_tool_for_agent,
    read_agent_inbox,
    send_agent_event,
)
from config import APP_NAME, MODEL_NAME
from deps import get_health_snapshot
from memory import get_agent_settings, get_or_create_agent, list_agents, reset_memory, set_agent_settings
from models import (
    AgentMessageRequest,
    AgentPermissionsUpdate,
    AgentSettingsUpdate,
    ChatRequest,
    ToolExecutionRequest,
)
from telegram_actor import telegram_is_ready, telegram_webhook

router = APIRouter()


@router.get("/")
async def home():
    return {"app": APP_NAME, "status": "active", "model": MODEL_NAME}


@router.get("/health")
async def health():
    health_data = await get_health_snapshot(telegram_ready=telegram_is_ready())
    return {"ok": health_data["status"] in {"ok", "degraded"}, **health_data}


@router.post("/chat")
async def chat(req: ChatRequest):
    answer = await ask_nexora(req.usuario or "web_user", req.texto, req.channel or "Web")
    return {"respuesta": answer}


@router.post("/reset-web")
async def reset_web(req: ChatRequest):
    await reset_memory(req.usuario or "web_user")
    return {"ok": True, "mensaje": "Memoria reiniciada."}


@router.post("/whatsapp")
async def whatsapp_webhook(Body: str = Form(...), From: str = Form(...)):
    sender = (From or "").strip()
    sender = sender.removeprefix("whatsapp:")
    user_id = sender or "wa_user"
    answer = await ask_nexora(user_id, Body, "WhatsApp")
    return {"ok": True, "respuesta": answer}


@router.post("/tg/{token}")
async def tg_webhook(token: str, request: Request):
    return await telegram_webhook(token, request)


@router.get("/agents/registry")
async def agents_registry():
    return {"agents": [agent.model_dump() for agent in await list_agents()]}


@router.get("/agents/{user_id}")
async def get_user_agent(user_id: str):
    agent = await get_or_create_agent(user_id)
    settings = await get_agent_settings(user_id)
    return {"agent": agent.model_dump(), "settings": settings.model_dump()}


@router.post("/agents/{user_id}/settings")
async def update_agent_settings(user_id: str, req: AgentSettingsUpdate):
    await set_agent_settings(user_id, req.settings)
    return {"ok": True, "settings": req.settings.model_dump()}


@router.post("/agents/{user_id}/permissions")
async def update_agent_permissions(user_id: str, req: AgentPermissionsUpdate):
    agent = await configure_agent_permissions(user_id, req.tools_allowed, req.permissions)
    return {"ok": True, "agent": agent.model_dump()}


@router.post("/agents/event")
async def post_agent_event(req: AgentMessageRequest):
    event = await send_agent_event(req.from_user_id, req.to_agent_id, req.event_type, req.payload)
    return {"ok": True, "event": event.model_dump()}


@router.get("/agents/{agent_id}/events")
async def get_agent_events(agent_id: str):
    events = await read_agent_inbox(agent_id)
    return {"events": [event.model_dump() for event in events]}


@router.post("/tools/execute")
async def tools_execute(req: ToolExecutionRequest):
    result = await execute_tool_for_agent(req.user_id, req.tool_name, req.args)
    return result
