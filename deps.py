from __future__ import annotations

import redis.asyncio as redis
from openai import AsyncOpenAI
from tavily import TavilyClient

from config import logger, settings

_openai_client: AsyncOpenAI | None = None
_redis_client: redis.Redis | None = None
_tavily_client: TavilyClient | None = None


def get_openai_client() -> AsyncOpenAI | None:
    global _openai_client
    if _openai_client is None and settings.openai_api_key:
        try:
            _openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        except Exception as exc:
            logger.warning("No se pudo inicializar OpenAI: %s", exc)
            _openai_client = None
    return _openai_client


def get_redis_client() -> redis.Redis | None:
    global _redis_client
    if _redis_client is None and settings.redis_url:
        try:
            _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        except Exception as exc:
            logger.warning("No se pudo inicializar Redis: %s", exc)
            _redis_client = None
    return _redis_client


def get_tavily_client() -> TavilyClient | None:
    global _tavily_client
    if _tavily_client is None and settings.tavily_api_key:
        try:
            _tavily_client = TavilyClient(api_key=settings.tavily_api_key)
        except Exception as exc:
            logger.warning("No se pudo inicializar Tavily: %s", exc)
            _tavily_client = None
    return _tavily_client


async def close_connections() -> None:
    redis_client = get_redis_client()
    if redis_client is not None:
        try:
            await redis_client.close()
        except Exception as exc:
            logger.warning("Error cerrando Redis: %s", exc)


async def get_service_status() -> dict[str, bool]:
    redis_ok = False
    redis_client = get_redis_client()
    if redis_client is not None:
        try:
            await redis_client.ping()
            redis_ok = True
        except Exception as exc:
            logger.warning("Redis no disponible: %s", exc)

    return {
        "redis": redis_ok,
        "openai": get_openai_client() is not None,
        "tavily": get_tavily_client() is not None,
    }
