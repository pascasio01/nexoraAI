from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from config import logger
from deps import get_redis

_long_memory_fallback: Dict[str, List[str]] = defaultdict(list)


async def save_long_memory(user_id: str, memory: str) -> None:
    redis_client = get_redis()
    if redis_client:
        try:
            await redis_client.rpush(f"long_memory:{user_id}", memory)
            await redis_client.ltrim(f"long_memory:{user_id}", -50, -1)
            return
        except Exception as exc:
            logger.warning("Long memory Redis fallback for user %s: %s", user_id, exc)

    _long_memory_fallback[user_id].append(memory)
    _long_memory_fallback[user_id] = _long_memory_fallback[user_id][-50:]


async def load_long_memory(user_id: str) -> List[str]:
    redis_client = get_redis()
    if redis_client:
        try:
            return await redis_client.lrange(f"long_memory:{user_id}", 0, -1)
        except Exception as exc:
            logger.warning("Long memory Redis fallback for user %s: %s", user_id, exc)
    return _long_memory_fallback.get(user_id, [])
