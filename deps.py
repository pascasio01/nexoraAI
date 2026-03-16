from __future__ import annotations

from typing import Optional

import redis.asyncio as redis
from openai import AsyncOpenAI
from tavily import TavilyClient

from config import OPENAI_API_KEY, REDIS_URL, TAVILY_API_KEY, logger

client: Optional[AsyncOpenAI] = None
r: Optional[redis.Redis] = None
tavily: Optional[TavilyClient] = None


async def init_services() -> None:
    global client, r, tavily

    client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

    if REDIS_URL:
        try:
            r = redis.from_url(REDIS_URL, decode_responses=True)
        except Exception as exc:
            logger.warning("Redis init failed: %s", exc)
            r = None
    else:
        r = None

    if TAVILY_API_KEY:
        try:
            tavily = TavilyClient(api_key=TAVILY_API_KEY)
        except Exception as exc:
            logger.warning("Tavily init failed: %s", exc)
            tavily = None
    else:
        tavily = None


async def shutdown_services() -> None:
    global r
    if r is not None:
        try:
            await r.aclose()
        except Exception as exc:
            logger.warning("Redis shutdown issue: %s", exc)


def get_openai_client() -> Optional[AsyncOpenAI]:
    return client


def get_redis() -> Optional[redis.Redis]:
    return r


def get_tavily() -> Optional[TavilyClient]:
    return tavily
