from __future__ import annotations

import redis.asyncio as redis
from openai import AsyncOpenAI
from tavily import TavilyClient

from config import OPENAI_API_KEY, REDIS_URL, TAVILY_API_KEY, logger

_openai_client: AsyncOpenAI | None = None
_redis_client: redis.Redis | None = None
_tavily_client: TavilyClient | None = None


async def startup_dependencies() -> None:
    global _openai_client, _redis_client, _tavily_client

    if OPENAI_API_KEY:
        try:
            _openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        except Exception as exc:
            logger.warning("OpenAI init failed: %s", exc)
            _openai_client = None
    else:
        logger.info("OPENAI_API_KEY not configured; chat model fallback enabled")

    if REDIS_URL:
        try:
            _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
            await _redis_client.ping()
        except Exception as exc:
            logger.warning("Redis unavailable, using in-memory fallback: %s", exc)
            _redis_client = None
    else:
        logger.info("REDIS_URL not configured; using in-memory memory store")

    if TAVILY_API_KEY:
        try:
            _tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
        except Exception as exc:
            logger.warning("Tavily init failed: %s", exc)
            _tavily_client = None
    else:
        logger.info("TAVILY_API_KEY not configured; web search disabled")


async def shutdown_dependencies() -> None:
    global _redis_client

    if _redis_client is not None:
        try:
            await _redis_client.aclose()
        except Exception as exc:
            logger.warning("Redis shutdown warning: %s", exc)


def get_openai() -> AsyncOpenAI | None:
    return _openai_client


def get_redis() -> redis.Redis | None:
    return _redis_client


def get_tavily() -> TavilyClient | None:
    return _tavily_client


def get_integrations_status() -> dict[str, bool]:
    return {
        "openai": _openai_client is not None,
        "redis": _redis_client is not None,
        "tavily": _tavily_client is not None,
    }
