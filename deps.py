"""Shared dependencies and lifecycle-safe initializers."""

from __future__ import annotations

from typing import Any

import redis.asyncio as redis
from openai import AsyncOpenAI
from tavily import TavilyClient

from config import OPENAI_API_KEY, REDIS_URL, TAVILY_API_KEY, logger
from memory import MemoryStore
from tools_impl import register_default_tools
from tools_schema import ToolRegistry

redis_client: Any | None = None
openai_client: AsyncOpenAI | None = None
tavily_client: TavilyClient | None = None
memory_store: MemoryStore | None = None
tool_registry: ToolRegistry | None = None
ai_core_service: Any | None = None
telegram_actor_service: Any | None = None


async def startup_dependencies() -> None:
    """Initialize optional clients without crashing application startup."""
    global redis_client, openai_client, tavily_client, memory_store, tool_registry

    if REDIS_URL:
        try:
            redis_client = redis.from_url(REDIS_URL, decode_responses=True)
            await redis_client.ping()
        except Exception as exc:
            logger.warning("Redis unavailable, using in-memory fallback: %s", exc)
            redis_client = None
    else:
        logger.info("REDIS_URL not configured, using in-memory fallback.")

    if OPENAI_API_KEY:
        try:
            openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        except Exception as exc:
            logger.warning("OpenAI unavailable, fallback replies enabled: %s", exc)
            openai_client = None
    else:
        logger.info("OPENAI_API_KEY not configured, fallback replies enabled.")

    if TAVILY_API_KEY:
        try:
            tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
        except Exception as exc:
            logger.warning("Tavily unavailable: %s", exc)
            tavily_client = None

    memory_store = MemoryStore(redis_client)
    tool_registry = ToolRegistry()
    register_default_tools(tool_registry, memory_store, tavily_client)


async def shutdown_dependencies() -> None:
    """Close optional clients safely."""
    global redis_client
    if redis_client:
        try:
            await redis_client.close()
        except Exception as exc:
            logger.warning("Error closing Redis client: %s", exc)


def get_memory_store() -> MemoryStore:
    assert memory_store is not None
    return memory_store


def get_tool_registry() -> ToolRegistry:
    assert tool_registry is not None
    return tool_registry


def get_ai_core() -> Any:
    global ai_core_service
    if ai_core_service is None:
        from ai_core import AICore

        ai_core_service = AICore(
            memory=get_memory_store(),
            tools=get_tool_registry(),
            openai_client=openai_client,
        )
    return ai_core_service


def get_telegram_actor() -> Any:
    global telegram_actor_service
    if telegram_actor_service is None:
        from telegram_actor import TelegramActor

        telegram_actor_service = TelegramActor(ai_core=get_ai_core())
    return telegram_actor_service
