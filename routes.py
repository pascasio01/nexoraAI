from __future__ import annotations

from fastapi import APIRouter, Form, Request

from models import ChatRequest, MemoryRequest, ProfileRequest, SettingsRequest, ToolRequest
from tools_schema import TOOLS_SCHEMA
from telegram_actor import telegram_webhook


router = APIRouter()


@router.get("/")
async def home():
    return {"status": "ok", "service": "NexoraAI"}


@router.get("/health")
async def health(request: Request):
    deps = request.app.state.dependencies
    return {
        "status": "ok",
        "openai": bool(deps["openai_client"]),
        "redis": bool(deps["redis_client"]),
        "telegram": bool(deps["telegram_enabled"]),
    }


@router.post("/chat")
async def chat(req: ChatRequest, request: Request):
    manager = request.app.state.agent_manager
    answer = await manager.route_request(user_id=req.user_id, message=req.message, channel=req.channel)
    return {"reply": answer}


@router.post("/assistant-profile")
async def assistant_profile(req: ProfileRequest, request: Request):
    memory_store = request.app.state.memory_store
    memory_store.set_profile(req.user_id, req.profile)
    return {"ok": True, "profile": memory_store.get_profile(req.user_id)}


@router.post("/assistant-settings")
async def assistant_settings(req: SettingsRequest, request: Request):
    memory_store = request.app.state.memory_store
    settings = memory_store.update_settings(req.user_id, req.settings)
    return {"ok": True, "settings": settings}


@router.post("/personal-memory")
async def personal_memory(req: MemoryRequest, request: Request):
    memory_store = request.app.state.memory_store
    memory_store.add_long_term_memory(req.user_id, req.memory)
    return {"ok": True, "memory_count": len(memory_store.get_long_term_memory(req.user_id))}


@router.get("/agents/{user_id}")
async def get_agent(user_id: str, request: Request):
    manager = request.app.state.agent_manager
    return manager.get_or_create_agent(user_id)


@router.get("/tools")
async def list_tools():
    return {"tools": TOOLS_SCHEMA}


@router.get("/channels")
async def channels():
    return {"supported": ["web", "telegram"], "future": ["mobile", "voice"]}


@router.post("/tools/execute")
async def execute_tool(req: ToolRequest, request: Request):
    manager = request.app.state.agent_manager
    result = await manager.execute_tool(req.user_id, req.tool_name, req.arguments)
    return result


@router.post("/whatsapp")
async def whatsapp_webhook(
    request: Request,
    body: str = Form(..., alias="Body"),
    from_field: str = Form(..., alias="From"),
):
    manager = request.app.state.agent_manager
    answer = await manager.route_request(user_id=from_field, message=body, channel="whatsapp")
    return {"ok": True, "reply": answer}


@router.post("/tg/{token}")
async def tg_webhook(token: str, request: Request):
    manager = request.app.state.agent_manager
    return await telegram_webhook(token=token, request=request, agent_manager=manager)
