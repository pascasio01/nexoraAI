import json
import time
import asyncio
from uuid import uuid4
from collections import defaultdict

import redis.asyncio as redis

from config import (
    MAX_CHAT_HISTORY,
    MAX_PERSONAL_NOTES,
    RATE_LIMIT_PER_MINUTE,
    REDIS_URL,
    logger,
)

r = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None

_chat_memory = defaultdict(list)
_profiles = defaultdict(lambda: "Usuario nuevo.")
_settings = defaultdict(dict)
_personal_memory = defaultdict(list)
_rate_limit = defaultdict(list)
_rate_limit_lock = asyncio.Lock()


def normalize_user_id(user_id: str | None) -> str:
    value = (user_id or "").strip()
    return value or f"anonymous:{uuid4().hex}"


async def check_rate_limit(user_id: str) -> bool:
    user_id = normalize_user_id(user_id)
    if r is None:
        async with _rate_limit_lock:
            now = time.time()
            window_start = now - 60
            _rate_limit[user_id] = [t for t in _rate_limit[user_id] if t >= window_start]
            _rate_limit[user_id].append(now)
            return len(_rate_limit[user_id]) <= RATE_LIMIT_PER_MINUTE
    try:
        key = f"rate_limit:{user_id}"
        count = await r.incr(key)
        if count == 1:
            await r.expire(key, 60)
        return count <= RATE_LIMIT_PER_MINUTE
    except Exception as exc:
        logger.warning(f"Rate limit in-memory fallback: {exc}")
        async with _rate_limit_lock:
            now = time.time()
            window_start = now - 60
            _rate_limit[user_id] = [t for t in _rate_limit[user_id] if t >= window_start]
            _rate_limit[user_id].append(now)
            return len(_rate_limit[user_id]) <= RATE_LIMIT_PER_MINUTE


async def get_profile(user_id: str) -> str:
    user_id = normalize_user_id(user_id)
    if r is None:
        return _profiles[user_id]
    value = await r.get(f"profile:{user_id}")
    return value or "Usuario nuevo."


async def set_profile(user_id: str, profile_text: str) -> None:
    user_id = normalize_user_id(user_id)
    if r is None:
        _profiles[user_id] = profile_text
        return
    await r.set(f"profile:{user_id}", profile_text)


async def get_assistant_settings(user_id: str) -> dict:
    user_id = normalize_user_id(user_id)
    if r is None:
        return dict(_settings[user_id])
    raw = await r.get(f"assistant_settings:{user_id}")
    return json.loads(raw) if raw else {}


async def set_assistant_settings(user_id: str, settings: dict) -> dict:
    user_id = normalize_user_id(user_id)
    if r is None:
        _settings[user_id].update(settings or {})
        return dict(_settings[user_id])
    existing = await get_assistant_settings(user_id)
    existing.update(settings or {})
    await r.set(f"assistant_settings:{user_id}", json.dumps(existing))
    return existing


async def append_personal_memory(user_id: str, note: str) -> None:
    user_id = normalize_user_id(user_id)
    if not note:
        return
    if r is None:
        _personal_memory[user_id].append(note)
        _personal_memory[user_id] = _personal_memory[user_id][-MAX_PERSONAL_NOTES:]
        return
    await r.rpush(f"personal_memory:{user_id}", note)
    await r.ltrim(f"personal_memory:{user_id}", -MAX_PERSONAL_NOTES, -1)


async def load_personal_memory(user_id: str) -> list[str]:
    user_id = normalize_user_id(user_id)
    if r is None:
        return list(_personal_memory[user_id])
    return await r.lrange(f"personal_memory:{user_id}", 0, -1)


async def save_chat_memory(user_id: str, role: str, content: str) -> None:
    user_id = normalize_user_id(user_id)
    item = {"role": role, "content": content}
    if r is None:
        _chat_memory[user_id].append(item)
        _chat_memory[user_id] = _chat_memory[user_id][-MAX_CHAT_HISTORY:]
        return
    await r.rpush(f"chat:{user_id}", json.dumps(item))
    await r.ltrim(f"chat:{user_id}", -MAX_CHAT_HISTORY, -1)


async def load_chat_memory(user_id: str) -> list[dict]:
    user_id = normalize_user_id(user_id)
    if r is None:
        return list(_chat_memory[user_id])
    history_raw = await r.lrange(f"chat:{user_id}", 0, -1)
    return [json.loads(m) for m in history_raw]


async def reset_memory(user_id: str) -> None:
    user_id = normalize_user_id(user_id)
    if r is None:
        _chat_memory[user_id].clear()
        _personal_memory[user_id].clear()
        return
    await r.delete(f"chat:{user_id}")
    await r.delete(f"personal_memory:{user_id}")


async def get_user_context(user_id: str) -> dict:
    user_id = normalize_user_id(user_id)
    return {
        "user_id": user_id,
        "profile": await get_profile(user_id),
        "assistant_settings": await get_assistant_settings(user_id),
        "personal_memory": await load_personal_memory(user_id),
    }
