from __future__ import annotations

import redis.asyncio as redis
from openai import AsyncOpenAI
from tavily import TavilyClient

from config import OPENAI_API_KEY, REDIS_URL, TAVILY_API_KEY, logger


client = None
if OPENAI_API_KEY:
    try:
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    except Exception as exc:
        logger.warning("OpenAI initialization failed: %s", exc)
else:
    logger.warning("OPENAI_API_KEY missing; AI chat disabled.")

r = None
if REDIS_URL:
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
    except Exception as exc:
        logger.warning("Redis initialization failed: %s", exc)
else:
    logger.warning("REDIS_URL missing; using in-memory fallback.")

tavily = None
if TAVILY_API_KEY:
    try:
        tavily = TavilyClient(api_key=TAVILY_API_KEY)
    except Exception as exc:
        logger.warning("Tavily initialization failed: %s", exc)
