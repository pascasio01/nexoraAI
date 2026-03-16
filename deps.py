from __future__ import annotations

import redis.asyncio as redis
from openai import AsyncOpenAI
from tavily import TavilyClient

from config import OPENAI_API_KEY, REDIS_URL, TAVILY_API_KEY, logger

client: AsyncOpenAI | None = None
r: redis.Redis | None = None
tavily: TavilyClient | None = None


async def init_dependencies() -> None:
    global client, r, tavily

    if OPENAI_API_KEY:
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    else:
        logger.warning("OPENAI_API_KEY is missing: AI replies will use safe fallback text.")

    if REDIS_URL:
        try:
            r = redis.from_url(REDIS_URL, decode_responses=True)
            await r.ping()
        except Exception as exc:
            logger.warning("Redis unavailable, memory disabled: %s", exc)
            r = None
    else:
        logger.warning("REDIS_URL is missing: memory features disabled.")

    if TAVILY_API_KEY:
        tavily = TavilyClient(api_key=TAVILY_API_KEY)
    else:
        logger.warning("TAVILY_API_KEY is missing: web search tool disabled.")


async def close_dependencies() -> None:
    global r
    if r:
        await r.close()
