from __future__ import annotations

from typing import Any

from openai import AsyncOpenAI
from tavily import TavilyClient

from config import OPENAI_API_KEY, REDIS_URL, TAVILY_API_KEY, logger

try:
    import redis.asyncio as redis
except Exception:  # pragma: no cover - optional dependency import guard
    redis = None

client: AsyncOpenAI | None = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
tavily: TavilyClient | None = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None
redis_client: Any | None = None


async def initialize_optional_services() -> None:
    """Initialize optional services with graceful fallbacks."""
    global redis_client
    if not REDIS_URL or redis is None:
        logger.info("Redis disabled (missing REDIS_URL or redis package).")
        redis_client = None
        return

    try:
        candidate = redis.from_url(REDIS_URL, decode_responses=True)
        await candidate.ping()
        redis_client = candidate
        logger.info("Redis connection initialized.")
    except Exception as exc:
        logger.warning("Redis unavailable, using in-memory fallback: %s", exc)
        redis_client = None


async def shutdown_optional_services() -> None:
    """Close optional network clients gracefully."""
    global redis_client
    if redis_client is not None:
        try:
            await redis_client.close()
        except Exception as exc:
            logger.warning("Error closing Redis client: %s", exc)
    redis_client = None


async def get_redis_status() -> bool:
    """Return redis health status without raising."""
    if redis_client is None:
        return False
    try:
        await redis_client.ping()
        return True
    except Exception:
        return False


async def get_health_snapshot(telegram_ready: bool) -> dict:
    """Provide health and observability details for optional integrations."""
    redis_ok = await get_redis_status()
    openai_ok = client is not None
    tavily_ok = tavily is not None
    status = "ok" if (openai_ok or redis_ok or tavily_ok or telegram_ready) else "degraded"
    return {
        "status": status,
        "redis": redis_ok,
        "openai": openai_ok,
        "tavily": tavily_ok,
        "telegram": telegram_ready,
    }
