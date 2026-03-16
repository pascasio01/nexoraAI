from __future__ import annotations

import json
import time
from collections import defaultdict, deque

from config import MAX_CHAT_HISTORY, RATE_LIMIT_PER_MINUTE
from deps import get_redis

_chat_memory_local: dict[str, deque[dict[str, str]]] = defaultdict(lambda: deque(maxlen=MAX_CHAT_HISTORY))
_profile_local: dict[str, str] = {}
_rate_local: dict[str, deque[float]] = defaultdict(deque)


async def check_rate_limit(user_id: str) -> bool:
    r = get_redis()
    if r is not None:
        key = f"rate_limit:{user_id}"
        try:
            count = await r.incr(key)
            if count == 1:
                await r.expire(key, 60)
            return count <= RATE_LIMIT_PER_MINUTE
        except Exception:
            pass

    now = time.time()
    bucket = _rate_local[user_id]
    while bucket and now - bucket[0] > 60:
        bucket.popleft()
    if len(bucket) >= RATE_LIMIT_PER_MINUTE:
        return False
    bucket.append(now)
    return True


async def save_chat_memory(user_id: str, role: str, content: str) -> None:
    r = get_redis()
    payload = json.dumps({"role": role, "content": content})

    if r is not None:
        try:
            await r.rpush(f"chat:{user_id}", payload)
            await r.ltrim(f"chat:{user_id}", -MAX_CHAT_HISTORY, -1)
            return
        except Exception:
            pass

    _chat_memory_local[user_id].append({"role": role, "content": content})


async def load_chat_memory(user_id: str) -> list[dict[str, str]]:
    r = get_redis()
    if r is not None:
        try:
            history_raw = await r.lrange(f"chat:{user_id}", 0, -1)
            return [json.loads(item) for item in history_raw]
        except Exception:
            pass

    return list(_chat_memory_local[user_id])


async def reset_memory(user_id: str) -> None:
    r = get_redis()
    if r is not None:
        try:
            await r.delete(f"chat:{user_id}")
        except Exception:
            pass

    _chat_memory_local.pop(user_id, None)


async def get_profile(user_id: str) -> str:
    r = get_redis()
    if r is not None:
        try:
            profile = await r.get(f"profile:{user_id}")
            if profile:
                return profile
        except Exception:
            pass
    return _profile_local.get(user_id, "")


async def set_profile(user_id: str, profile_text: str) -> None:
    r = get_redis()
    if r is not None:
        try:
            await r.set(f"profile:{user_id}", profile_text)
            return
        except Exception:
            pass

    _profile_local[user_id] = profile_text
