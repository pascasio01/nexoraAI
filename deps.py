from __future__ import annotations

from typing import Optional

import redis.asyncio as redis
from openai import AsyncOpenAI

from config import OPENAI_API_KEY, REDIS_URL, logger

client: Optional[AsyncOpenAI] = None
if OPENAI_API_KEY:
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
else:
    logger.warning("OPENAI_API_KEY not configured. Falling back to local assistant replies.")

r: Optional[redis.Redis] = None
if REDIS_URL:
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
    except Exception as exc:
        logger.warning("Redis init failed. Falling back to in-memory state. error=%s", exc)
else:
    logger.warning("REDIS_URL not configured. Using in-memory state.")
