"""HTTP routes for web/API clients and channel webhooks."""

from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import JSONResponse

from config import APP_NAME, MODEL_NAME
from deps import get_ai_core, get_memory_store, get_telegram_actor, openai_client, redis_client, tavily_client
from models import AssistantConfig, ChatRequest, ChatResponse, ToolRegistrationRequest

router = APIRouter()


@router.get("/")
async def home() -> dict[str, str]:
    return {"app": APP_NAME, "status": "online", "model": MODEL_NAME}


@router.get("/health")
async def health() -> dict[str, object]:
    redis_ok = False
    if redis_client:
        try:
            await redis_client.ping()
            redis_ok = True
        except Exception:
            redis_ok = False

    telegram_actor = get_telegram_actor()
    return {
        "status": "ok",
        "server": True,
        "redis": redis_ok,
        "openai": openai_client is not None,
        "tavily": tavily_client is not None,
        "telegram": telegram_actor.app is not None if telegram_actor else False,
    }


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    core = get_ai_core()
    reply = await core.ask(user_id=req.user_id, session_id=req.session_id, text=req.text, channel=req.channel)
    return ChatResponse(reply=reply, user_id=req.user_id, session_id=req.session_id, channel=req.channel)


@router.post("/reset-web")
async def reset_web(req: ChatRequest) -> dict[str, str]:
    memory = get_memory_store()
    await memory.reset_session(req.user_id, req.session_id)
    return {"status": "ok", "message": "Session memory reset"}


@router.post("/users/{user_id}/assistant-config")
async def set_assistant_config(user_id: str, config: AssistantConfig) -> dict[str, object]:
    memory = get_memory_store()
    payload = config.model_dump()
    if not payload.get("enabled_tools"):
        payload["enabled_tools"] = []
    await memory.set_assistant_config(user_id, payload)
    return {"status": "ok", "user_id": user_id, "config": payload}


@router.get("/users/{user_id}/profile")
async def get_profile(user_id: str) -> dict[str, str]:
    memory = get_memory_store()
    profile = await memory.get_user_profile(user_id)
    summary = await memory.get_memory_summary(user_id)
    return {"user_id": user_id, "profile": profile, "summary": summary}


@router.post("/whatsapp")
async def whatsapp_webhook(Body: str = Form(...), From: str = Form(...)) -> JSONResponse:  # noqa: N803
    core = get_ai_core()
    reply = await core.ask(user_id=From, session_id="whatsapp", text=Body, channel="whatsapp")
    return JSONResponse({"reply": reply})


@router.post("/tg/{token}")
async def telegram_webhook(token: str, request: Request) -> dict[str, bool]:
    telegram = get_telegram_actor()
    await telegram.webhook(token, request)
    return {"ok": True}


@router.post("/plugins/register-tool")
async def register_plugin_tool(payload: ToolRegistrationRequest) -> dict[str, object]:
    registry = get_ai_core().tools
    metadata_schema = {
        "type": "function",
        "function": {
            "name": payload.tool_name,
            "description": payload.description,
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    }

    async def _placeholder_tool_handler(user_id: str, args: dict) -> str:
        return (
            f"Tool '{payload.tool_name}' from plugin '{payload.plugin_name}' "
            "was registered as a placeholder."
        )

    registry.register(payload.tool_name, metadata_schema, _placeholder_tool_handler, plugin_name=payload.plugin_name)
    return {"status": "ok", "plugins": registry.plugin_index()}
