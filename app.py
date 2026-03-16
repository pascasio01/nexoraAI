from __future__ import annotations

from fastapi import FastAPI

from ai_core import AgentManager
from config import settings
from deps import get_openai_client, get_redis_client, get_tavily_client
from memory import AssistantMemoryStore
from routes import router
from telegram_actor import telegram_shutdown, telegram_startup
from tools_impl import ToolExecutor


app = FastAPI(title=f"{settings.app_name} AI OS")
app.include_router(router)


@app.on_event("startup")
async def startup() -> None:
    openai_client = get_openai_client()
    redis_client = get_redis_client()
    tavily_client = get_tavily_client()

    memory_store = AssistantMemoryStore(max_history=settings.max_chat_history)
    tool_executor = ToolExecutor(memory_store=memory_store, tavily_client=tavily_client)
    agent_manager = AgentManager(
        memory_store=memory_store,
        openai_client=openai_client,
        tool_executor=tool_executor,
    )

    app.state.memory_store = memory_store
    app.state.agent_manager = agent_manager
    app.state.dependencies = {
        "openai_client": openai_client,
        "redis_client": redis_client,
        "telegram_enabled": bool(settings.bot_token),
    }

    await telegram_startup()


@app.on_event("shutdown")
async def shutdown() -> None:
    await telegram_shutdown()
