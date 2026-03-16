from __future__ import annotations

import json
from collections import defaultdict, deque

from config import MAX_CHAT_HISTORY, RATE_LIMIT_PER_MINUTE, logger
from deps import r

_chat_fallback: dict[str, deque[str]] = defaultdict(lambda: deque(maxlen=MAX_CHAT_HISTORY))
_profile_fallback: dict[str, str] = {}
_rate_fallback: dict[str, int] = defaultdict(int)


async def check_rate_limit(user_id: str) -> bool:
    if r is None:
        _rate_fallback[user_id] += 1
        return _rate_fallback[user_id] <= RATE_LIMIT_PER_MINUTE
    try:
        key = f"rate_limit:{user_id}"
        count = await r.incr(key)
        if count == 1:
            await r.expire(key, 60)
        return count <= RATE_LIMIT_PER_MINUTE
    except Exception as exc:
        logger.warning("Redis rate limit failed; allowing request: %s", exc)
        return True


async def get_profile(user_id: str) -> str:
    if r is None:
        return _profile_fallback.get(user_id, "Usuario nuevo.")
    try:
        return await r.get(f"profile:{user_id}") or "Usuario nuevo."
    except Exception as exc:
        logger.warning("Profile load failed: %s", exc)
        return "Usuario nuevo."


async def set_profile(user_id: str, profile_text: str):
    if r is None:
        _profile_fallback[user_id] = profile_text
        return
    try:
        await r.set(f"profile:{user_id}", profile_text)
    except Exception as exc:
        logger.warning("Profile save failed: %s", exc)


async def save_chat_memory(user_id: str, role: str, content: str):
    item = json.dumps({"role": role, "content": content})
    if r is None:
        _chat_fallback[user_id].append(item)
        return
    try:
        await r.rpush(f"chat:{user_id}", item)
        await r.ltrim(f"chat:{user_id}", -MAX_CHAT_HISTORY, -1)
    except Exception as exc:
        logger.warning("Chat memory save failed: %s", exc)


async def load_chat_memory(user_id: str):
    if r is None:
        return [json.loads(item) for item in _chat_fallback[user_id]]
    try:
        history_raw = await r.lrange(f"chat:{user_id}", 0, -1)
        return [json.loads(m) for m in history_raw]
    except Exception as exc:
        logger.warning("Chat memory load failed: %s", exc)
        return []


async def reset_memory(user_id: str):
    if r is None:
        _chat_fallback.pop(user_id, None)
        _profile_fallback.pop(user_id, None)
        return
    try:
        await r.delete(f"chat:{user_id}")
        await r.delete(f"profile:{user_id}")
    except Exception as exc:
        logger.warning("Memory reset failed: %s", exc)
