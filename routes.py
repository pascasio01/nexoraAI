from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import JSONResponse

from ai_core import ask_nexora
from config import settings
from deps import get_service_status
from memory import (
    add_personal_memory,
    get_assistant_settings,
    list_personal_memory,
    reset_memory,
    update_assistant_settings,
)
from models import (
    AssistantSettingsRequest,
    ChatRequest,
    PersonalMemoryRequest,
    ResetRequest,
    ToolExecutionRequest,
)
from telegram_actor import telegram_is_active, telegram_webhook
from tools_impl import execute_tool_call

router = APIRouter()


@router.get("/")
async def home() -> dict:
    return {"app": settings.app_name, "status": "online", "model": settings.model_name}


@router.get("/health")
async def health() -> dict:
    service_status = await get_service_status()
    service_status["telegram"] = telegram_is_active()

    required_ok = service_status["openai"]
    optional_ok = service_status["redis"] or not settings.redis_url
    optional_ok = optional_ok and (service_status["tavily"] or not settings.tavily_api_key)
    optional_ok = optional_ok and (service_status["telegram"] or not (settings.bot_token and settings.base_url))
    overall = "ok" if required_ok and optional_ok else "degraded"

    return {
        "status": overall,
        "services": service_status,
        "config": {
            "redis_configured": bool(settings.redis_url),
            "openai_configured": bool(settings.openai_api_key),
            "tavily_configured": bool(settings.tavily_api_key),
            "telegram_configured": bool(settings.bot_token and settings.base_url),
        },
    }


@router.post("/chat")
async def chat(req: ChatRequest) -> dict:
    answer = await ask_nexora(
        user_id=req.user_id,
        text=req.text,
        channel=req.channel,
        assistant_id=req.assistant_id,
    )
    return {
        "user_id": req.user_id,
        "assistant_id": req.assistant_id,
        "response": answer,
    }


@router.post("/reset-web")
async def reset_web(req: ResetRequest) -> dict:
    await reset_memory(req.user_id, req.assistant_id)
    return {"status": "ok", "message": "Memoria reseteada"}


@router.post("/assistant-settings")
async def assistant_settings(payload: AssistantSettingsRequest) -> dict:
    updates = {
        "tone": payload.tone,
        "language": payload.language,
        "goals": payload.goals,
    }
    merged = await update_assistant_settings(payload.user_id, updates, payload.assistant_id)
    return {"status": "ok", "settings": merged}


@router.get("/assistant-settings")
async def assistant_settings_get(user_id: str, assistant_id: str = "default") -> dict:
    return {"status": "ok", "settings": await get_assistant_settings(user_id, assistant_id)}


@router.post("/personal-memory")
async def personal_memory_add(payload: PersonalMemoryRequest) -> dict:
    entry = await add_personal_memory(
        user_id=payload.user_id,
        assistant_id=payload.assistant_id,
        kind=payload.kind,
        content=payload.content,
    )
    return {"status": "ok", "entry": entry}


@router.get("/personal-memory")
async def personal_memory_list(user_id: str, assistant_id: str = "default") -> dict:
    return {"status": "ok", "items": await list_personal_memory(user_id, assistant_id)}


@router.post("/tools/execute")
async def tools_execute(req: ToolExecutionRequest) -> dict:
    result = await execute_tool_call(req.tool_name, req.arguments, req.user_id, req.assistant_id)
    return {"status": "ok", "result": result}


@router.post("/whatsapp")
async def whatsapp_webhook(body: str = Form(..., alias="Body"), from_number: str = Form(..., alias="From")) -> JSONResponse:
    response = await ask_nexora(user_id=from_number, text=body, channel="whatsapp")
    return JSONResponse({"reply": response})


@router.post("/tg/{token}")
async def tg_webhook(token: str, request: Request):
    return await telegram_webhook(token, request)
