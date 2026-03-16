from __future__ import annotations

from typing import Any

import redis.asyncio as redis
from openai import AsyncOpenAI
from tavily import TavilyClient

from config import settings


def get_openai_client() -> AsyncOpenAI | None:
    if not settings.openai_api_key:
        return None
    return AsyncOpenAI(api_key=settings.openai_api_key)


def get_redis_client() -> Any | None:
    if not settings.redis_url:
        return None
    return redis.from_url(settings.redis_url, decode_responses=True)


def get_tavily_client() -> TavilyClient | None:
    if not settings.tavily_api_key:
        return None
    return TavilyClient(api_key=settings.tavily_api_key)
