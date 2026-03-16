import json

import redis.asyncio as redis

from config import REDIS_URL, logger

MAX_CHAT_HISTORY = 12
RATE_LIMIT_PER_MINUTE = 8

r = None

if not REDIS_URL:
    logger.warning("REDIS_URL is not configured. Memory features are disabled.")
else:
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
    except Exception as exc:
        logger.warning("Redis initialization failed: %s", exc)
        r = None


async def check_rate_limit(user_id: str) -> bool:
    if r is None:
        return True
    try:
        key = f"rate_limit:{user_id}"
        count = await r.incr(key)
        if count == 1:
            await r.expire(key, 60)
        return count <= RATE_LIMIT_PER_MINUTE
    except Exception as exc:
        logger.warning("Rate limit check failed, allowing request: %s", exc)
        return True


async def save_chat_memory(user_id: str, role: str, content: str) -> None:
    if r is None:
        return
    try:
        await r.rpush(f"chat:{user_id}", json.dumps({"role": role, "content": content}))
        await r.ltrim(f"chat:{user_id}", -MAX_CHAT_HISTORY, -1)
    except Exception as exc:
        logger.warning("Failed to save chat memory: %s", exc)


async def load_chat_memory(user_id: str) -> list[dict]:
    if r is None:
        return []
    try:
        history_raw = await r.lrange(f"chat:{user_id}", 0, -1)
        return [json.loads(item) for item in history_raw]
    except Exception as exc:
        logger.warning("Failed to load chat memory: %s", exc)
        return []


async def reset_memory(user_id: str) -> None:
    if r is None:
        return
    try:
        await r.delete(f"chat:{user_id}")
    except Exception as exc:
        logger.warning("Failed to reset memory: %s", exc)


async def redis_healthcheck() -> bool:
    if r is None:
        return False
    try:
        await r.ping()
        return True
    except Exception:
        return False


async def close_redis() -> None:
    if r is None:
        return
    try:
        await r.aclose()
    except Exception as exc:
        logger.warning("Failed to close Redis cleanly: %s", exc)
