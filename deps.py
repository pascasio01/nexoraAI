from typing import Optional

import redis.asyncio as redis
from openai import AsyncOpenAI
from tavily import TavilyClient

from config import OPENAI_API_KEY, REDIS_URL, TAVILY_API_KEY, logger

client: Optional[AsyncOpenAI] = None
r = None
tavily: Optional[TavilyClient] = None

if OPENAI_API_KEY:
    try:
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    except Exception as exc:  # pragma: no cover - defensive init
        logger.warning("OpenAI init failed: %s", exc)
else:
    logger.warning("OPENAI_API_KEY missing. Assistant responses will run in fallback mode.")

if REDIS_URL:
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
    except Exception as exc:  # pragma: no cover - defensive init
        logger.warning("Redis init failed: %s", exc)
else:
    logger.warning("REDIS_URL missing. Memory and rate limit are in-memory fallback mode.")

if TAVILY_API_KEY:
    try:
        tavily = TavilyClient(api_key=TAVILY_API_KEY)
    except Exception as exc:  # pragma: no cover - defensive init
        logger.warning("Tavily init failed: %s", exc)


async def close_deps() -> None:
    if r is not None:
        try:
            await r.aclose()
        except Exception as exc:  # pragma: no cover - defensive shutdown
            logger.warning("Redis close failed: %s", exc)
