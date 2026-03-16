from __future__ import annotations

import json
import time
from collections import defaultdict, deque
from typing import Deque, Dict, List

from config import MAX_CHAT_HISTORY, RATE_LIMIT_PER_MINUTE, logger
from deps import get_redis

_memory_store: Dict[str, Deque[dict]] = defaultdict(lambda: deque(maxlen=MAX_CHAT_HISTORY))
_profile_store: Dict[str, str] = {}
_rate_limit_store: Dict[str, Deque[int]] = defaultdict(deque)


def _chat_key(user_id: str) -> str:
    return f"chat:{user_id}"


def _profile_key(user_id: str) -> str:
    return f"profile:{user_id}"


async def check_rate_limit(user_id: str) -> bool:
    redis_client = get_redis()
    if redis_client:
        key = f"rate_limit:{user_id}"
        try:
            count = await redis_client.incr(key)
            if count == 1:
                await redis_client.expire(key, 60)
            return count <= RATE_LIMIT_PER_MINUTE
        except Exception as exc:
            logger.warning("Redis rate limit fallback for user %s: %s", user_id, exc)

    now = int(time.time())
    bucket = _rate_limit_store[user_id]
    while bucket and now - bucket[0] > 60:
        bucket.popleft()
    if len(bucket) >= RATE_LIMIT_PER_MINUTE:
        return False
    bucket.append(now)
    return True


async def save_chat_memory(user_id: str, role: str, content: str) -> None:
    redis_client = get_redis()
    payload = json.dumps({"role": role, "content": content})

    if redis_client:
        try:
            await redis_client.rpush(_chat_key(user_id), payload)
            await redis_client.ltrim(_chat_key(user_id), -MAX_CHAT_HISTORY, -1)
            return
        except Exception as exc:
            logger.warning("Redis save_chat_memory fallback for user %s: %s", user_id, exc)

    _memory_store[user_id].append({"role": role, "content": content})


async def load_chat_memory(user_id: str) -> List[dict]:
    redis_client = get_redis()
    if redis_client:
        try:
            history_raw = await redis_client.lrange(_chat_key(user_id), 0, -1)
            return [json.loads(item) for item in history_raw]
        except Exception as exc:
            logger.warning("Redis load_chat_memory fallback for user %s: %s", user_id, exc)

    return list(_memory_store[user_id])


async def reset_memory(user_id: str) -> None:
    redis_client = get_redis()
    if redis_client:
        try:
            await redis_client.delete(_chat_key(user_id), _profile_key(user_id), f"rate_limit:{user_id}")
            return
        except Exception as exc:
            logger.warning("Redis reset_memory fallback for user %s: %s", user_id, exc)

    _memory_store.pop(user_id, None)
    _profile_store.pop(user_id, None)
    _rate_limit_store.pop(user_id, None)


async def get_profile(user_id: str) -> str:
    redis_client = get_redis()
    if redis_client:
        try:
            return await redis_client.get(_profile_key(user_id)) or ""
        except Exception as exc:
            logger.warning("Redis get_profile fallback for user %s: %s", user_id, exc)
    return _profile_store.get(user_id, "")


async def set_profile(user_id: str, profile_text: str) -> None:
    redis_client = get_redis()
    if redis_client:
        try:
            await redis_client.set(_profile_key(user_id), profile_text)
            return
        except Exception as exc:
            logger.warning("Redis set_profile fallback for user %s: %s", user_id, exc)
    _profile_store[user_id] = profile_text
