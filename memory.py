from __future__ import annotations

import json

from config import LONG_TERM_MEMORY_LIMIT, MAX_CHAT_HISTORY, RATE_LIMIT_PER_MINUTE
import deps


async def check_rate_limit(user_id: str) -> bool:
    if not deps.r:
        return True

    key = f"rate_limit:{user_id}"
    count = await deps.r.incr(key)
    if count == 1:
        await deps.r.expire(key, 60)
    return count <= RATE_LIMIT_PER_MINUTE


async def get_profile(user_id: str) -> str:
    if not deps.r:
        return "Usuario nuevo."
    return await deps.r.get(f"profile:{user_id}") or "Usuario nuevo."


async def set_profile(user_id: str, profile_text: str) -> None:
    if deps.r:
        await deps.r.set(f"profile:{user_id}", profile_text)


async def get_assistant_settings(user_id: str) -> dict:
    default_settings = {
        "tone": "helpful",
        "language": "auto",
        "assistant_name": "Nexora",
    }
    if not deps.r:
        return default_settings

    raw = await deps.r.get(f"assistant_settings:{user_id}")
    if not raw:
        return default_settings

    try:
        return {**default_settings, **json.loads(raw)}
    except json.JSONDecodeError:
        return default_settings


async def set_assistant_settings(user_id: str, settings: dict) -> None:
    if deps.r:
        await deps.r.set(f"assistant_settings:{user_id}", json.dumps(settings, ensure_ascii=False))


async def save_chat_memory(user_id: str, role: str, content: str) -> None:
    if not deps.r:
        return

    await deps.r.rpush(f"chat:{user_id}", json.dumps({"role": role, "content": content}, ensure_ascii=False))
    await deps.r.ltrim(f"chat:{user_id}", -MAX_CHAT_HISTORY, -1)


async def load_chat_memory(user_id: str) -> list[dict]:
    if not deps.r:
        return []

    history_raw = await deps.r.lrange(f"chat:{user_id}", 0, -1)
    history: list[dict] = []
    for message in history_raw:
        try:
            history.append(json.loads(message))
        except json.JSONDecodeError:
            continue
    return history


async def save_long_memory(user_id: str, memory_text: str) -> None:
    if not deps.r or not memory_text.strip():
        return

    await deps.r.rpush(f"long_memory:{user_id}", memory_text.strip())
    await deps.r.ltrim(f"long_memory:{user_id}", -LONG_TERM_MEMORY_LIMIT, -1)


async def load_long_memory(user_id: str, limit: int = 5) -> list[str]:
    if not deps.r:
        return []
    return await deps.r.lrange(f"long_memory:{user_id}", -max(limit, 1), -1)


async def reset_memory(user_id: str) -> None:
    if deps.r:
        await deps.r.delete(f"chat:{user_id}")
