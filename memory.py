from __future__ import annotations

import json
import time
from collections import defaultdict

from config import logger, settings
from deps import get_redis_client

_in_memory_chat: dict[str, list[dict[str, str]]] = defaultdict(list)
_in_memory_profiles: dict[str, str] = {}
_in_memory_settings: dict[str, dict] = {}
_in_memory_personal: dict[str, list[dict]] = defaultdict(list)
_in_memory_tasks: dict[str, list[dict]] = defaultdict(list)
_in_memory_rate_limit: dict[str, list[float]] = defaultdict(list)

DEFAULT_ASSISTANT_SETTINGS = {
    "tone": "helpful",
    "language": "es",
    "goals": [],
}


def _scope(user_id: str, assistant_id: str = "default") -> str:
    return f"u:{user_id}:a:{assistant_id}"


async def check_rate_limit(user_id: str) -> bool:
    key = f"rate:{user_id}"
    redis_client = get_redis_client()
    if redis_client is not None:
        try:
            count = await redis_client.incr(key)
            if count == 1:
                await redis_client.expire(key, 60)
            return count <= settings.rate_limit_per_minute
        except Exception as exc:
            logger.warning("Rate limit en Redis falló, uso fallback en memoria: %s", exc)

    now = time.time()
    one_minute_ago = now - 60
    bucket = [t for t in _in_memory_rate_limit[user_id] if t > one_minute_ago]
    bucket.append(now)
    _in_memory_rate_limit[user_id] = bucket
    return len(bucket) <= settings.rate_limit_per_minute


async def get_profile(user_id: str, assistant_id: str = "default") -> str:
    scoped = _scope(user_id, assistant_id)
    redis_client = get_redis_client()
    if redis_client is not None:
        try:
            profile = await redis_client.get(f"{scoped}:profile")
            if profile:
                return profile
        except Exception as exc:
            logger.warning("No se pudo leer profile en Redis: %s", exc)
    return _in_memory_profiles.get(scoped, "Usuario nuevo.")


async def set_profile(user_id: str, profile_text: str, assistant_id: str = "default") -> None:
    scoped = _scope(user_id, assistant_id)
    redis_client = get_redis_client()
    if redis_client is not None:
        try:
            await redis_client.set(f"{scoped}:profile", profile_text)
        except Exception as exc:
            logger.warning("No se pudo guardar profile en Redis: %s", exc)
    _in_memory_profiles[scoped] = profile_text


async def load_chat_memory(user_id: str, assistant_id: str = "default") -> list[dict[str, str]]:
    scoped = _scope(user_id, assistant_id)
    redis_client = get_redis_client()
    if redis_client is not None:
        try:
            raw = await redis_client.lrange(f"{scoped}:chat", 0, -1)
            if raw:
                return [json.loads(item) for item in raw]
        except Exception as exc:
            logger.warning("No se pudo leer chat en Redis: %s", exc)
    return list(_in_memory_chat.get(scoped, []))


async def save_chat_memory(
    user_id: str,
    role: str,
    content: str,
    assistant_id: str = "default",
) -> None:
    scoped = _scope(user_id, assistant_id)
    payload = {"role": role, "content": content}
    redis_client = get_redis_client()
    if redis_client is not None:
        try:
            await redis_client.rpush(f"{scoped}:chat", json.dumps(payload, ensure_ascii=False))
            await redis_client.ltrim(f"{scoped}:chat", -settings.max_chat_history, -1)
        except Exception as exc:
            logger.warning("No se pudo guardar chat en Redis: %s", exc)

    history = _in_memory_chat[scoped]
    history.append(payload)
    _in_memory_chat[scoped] = history[-settings.max_chat_history :]


async def reset_memory(user_id: str, assistant_id: str = "default") -> None:
    scoped = _scope(user_id, assistant_id)
    redis_client = get_redis_client()
    if redis_client is not None:
        try:
            await redis_client.delete(f"{scoped}:chat")
        except Exception as exc:
            logger.warning("No se pudo resetear chat en Redis: %s", exc)
    _in_memory_chat.pop(scoped, None)


async def get_assistant_settings(user_id: str, assistant_id: str = "default") -> dict:
    scoped = _scope(user_id, assistant_id)
    redis_client = get_redis_client()
    if redis_client is not None:
        try:
            raw = await redis_client.get(f"{scoped}:settings")
            if raw:
                return {**DEFAULT_ASSISTANT_SETTINGS, **json.loads(raw)}
        except Exception as exc:
            logger.warning("No se pudo leer settings en Redis: %s", exc)
    return {**DEFAULT_ASSISTANT_SETTINGS, **_in_memory_settings.get(scoped, {})}


async def update_assistant_settings(user_id: str, updates: dict, assistant_id: str = "default") -> dict:
    scoped = _scope(user_id, assistant_id)
    current = await get_assistant_settings(user_id, assistant_id)
    clean_updates = {k: v for k, v in updates.items() if v is not None}
    merged = {**current, **clean_updates}

    redis_client = get_redis_client()
    if redis_client is not None:
        try:
            await redis_client.set(f"{scoped}:settings", json.dumps(merged, ensure_ascii=False))
        except Exception as exc:
            logger.warning("No se pudo guardar settings en Redis: %s", exc)

    _in_memory_settings[scoped] = merged
    return merged


async def add_personal_memory(user_id: str, kind: str, content: str, assistant_id: str = "default") -> dict:
    scoped = _scope(user_id, assistant_id)
    entry = {"kind": kind, "content": content, "created_at": int(time.time())}
    redis_client = get_redis_client()
    if redis_client is not None:
        try:
            await redis_client.rpush(f"{scoped}:personal", json.dumps(entry, ensure_ascii=False))
        except Exception as exc:
            logger.warning("No se pudo guardar memoria personal en Redis: %s", exc)

    _in_memory_personal[scoped].append(entry)
    return entry


async def list_personal_memory(user_id: str, assistant_id: str = "default") -> list[dict]:
    scoped = _scope(user_id, assistant_id)
    redis_client = get_redis_client()
    if redis_client is not None:
        try:
            raw = await redis_client.lrange(f"{scoped}:personal", 0, -1)
            if raw:
                return [json.loads(item) for item in raw]
        except Exception as exc:
            logger.warning("No se pudo leer memoria personal en Redis: %s", exc)
    return list(_in_memory_personal.get(scoped, []))


async def add_task(user_id: str, task: dict, assistant_id: str = "default") -> dict:
    scoped = _scope(user_id, assistant_id)
    entry = {
        "id": f"t-{int(time.time() * 1000)}",
        "status": "pending",
        **task,
    }
    redis_client = get_redis_client()
    if redis_client is not None:
        try:
            await redis_client.rpush(f"{scoped}:tasks", json.dumps(entry, ensure_ascii=False))
        except Exception as exc:
            logger.warning("No se pudo guardar task en Redis: %s", exc)

    _in_memory_tasks[scoped].append(entry)
    return entry


async def list_tasks(user_id: str, assistant_id: str = "default") -> list[dict]:
    scoped = _scope(user_id, assistant_id)
    redis_client = get_redis_client()
    if redis_client is not None:
        try:
            raw = await redis_client.lrange(f"{scoped}:tasks", 0, -1)
            if raw:
                return [json.loads(item) for item in raw]
        except Exception as exc:
            logger.warning("No se pudo leer tasks en Redis: %s", exc)
    return list(_in_memory_tasks.get(scoped, []))
