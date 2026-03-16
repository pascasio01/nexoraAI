"""Memory helpers for user-scoped personal agents with Redis/in-memory fallback."""

from __future__ import annotations

import json
import time
from collections import defaultdict

from config import DEFAULT_AGENT_TOOLS, MAX_CHAT_HISTORY, RATE_LIMIT_PER_MINUTE
from deps import redis_client
from models import AgentDescriptor, AgentSettings

_in_memory_lists: dict[str, list[str]] = defaultdict(list)
_in_memory_values: dict[str, str] = {}
_in_memory_rate: dict[str, tuple[int, float]] = {}


async def _get(key: str) -> str | None:
    if redis_client:
        return await redis_client.get(key)
    return _in_memory_values.get(key)


async def _set(key: str, value: str) -> None:
    if redis_client:
        await redis_client.set(key, value)
        return
    _in_memory_values[key] = value


async def _delete(*keys: str) -> None:
    if redis_client:
        await redis_client.delete(*keys)
        return
    for key in keys:
        _in_memory_values.pop(key, None)
        _in_memory_lists.pop(key, None)


async def _rpush(key: str, value: str) -> None:
    if redis_client:
        await redis_client.rpush(key, value)
        return
    _in_memory_lists[key].append(value)


async def _lrange(key: str, start: int, end: int) -> list[str]:
    if redis_client:
        return await redis_client.lrange(key, start, end)
    values = _in_memory_lists.get(key, [])
    if end == -1:
        return values[start:]
    return values[start : end + 1]


async def _ltrim(key: str, start: int, end: int) -> None:
    if redis_client:
        await redis_client.ltrim(key, start, end)
        return
    values = _in_memory_lists.get(key, [])
    if end == -1:
        _in_memory_lists[key] = values[start:]
    else:
        _in_memory_lists[key] = values[start : end + 1]


async def check_rate_limit(user_id: str) -> bool:
    key = f"rate_limit:{user_id}"
    if redis_client:
        count = await redis_client.incr(key)
        if count == 1:
            await redis_client.expire(key, 60)
        return count <= RATE_LIMIT_PER_MINUTE

    now = time.time()
    count, ts = _in_memory_rate.get(key, (0, now))
    if now - ts > 60:
        count, ts = 0, now
    count += 1
    _in_memory_rate[key] = (count, ts)
    return count <= RATE_LIMIT_PER_MINUTE


async def get_profile(user_id: str) -> str:
    return await _get(f"profile:{user_id}") or "New user."


async def set_profile(user_id: str, profile_text: str) -> None:
    await _set(f"profile:{user_id}", profile_text)


async def get_summary(user_id: str) -> str:
    return await _get(f"summary:{user_id}") or ""


async def set_summary(user_id: str, summary: str) -> None:
    await _set(f"summary:{user_id}", summary)


async def save_chat_memory(user_id: str, role: str, content: str) -> None:
    await _rpush(f"chat:{user_id}", json.dumps({"role": role, "content": content}))
    await _ltrim(f"chat:{user_id}", -MAX_CHAT_HISTORY, -1)


async def load_chat_memory(user_id: str) -> list[dict[str, str]]:
    history_raw = await _lrange(f"chat:{user_id}", 0, -1)
    return [json.loads(m) for m in history_raw]


async def reset_memory(user_id: str) -> None:
    await _delete(f"chat:{user_id}", f"summary:{user_id}")


async def get_agent_settings(user_id: str) -> AgentSettings:
    raw = await _get(f"agent_settings:{user_id}")
    if not raw:
        return AgentSettings()
    return AgentSettings(**json.loads(raw))


async def set_agent_settings(user_id: str, settings: AgentSettings) -> AgentSettings:
    await _set(f"agent_settings:{user_id}", settings.model_dump_json())
    return settings


async def get_agent_descriptor(user_id: str) -> AgentDescriptor:
    key = f"agent_descriptor:{user_id}"
    raw = await _get(key)
    if raw:
        return AgentDescriptor(**json.loads(raw))

    descriptor = AgentDescriptor(
        user_id=user_id,
        agent_id=f"agent-{user_id}",
        endpoint=f"/agents/{user_id}",
        capabilities=["chat", "memory", "tools", "agent_communication"],
        tools=list(DEFAULT_AGENT_TOOLS),
        permissions={name: True for name in DEFAULT_AGENT_TOOLS},
        metadata={"vector_memory": "planned", "channels": ["web", "telegram", "whatsapp", "api"]},
    )
    await _set(key, descriptor.model_dump_json())
    return descriptor


async def set_agent_descriptor(user_id: str, descriptor: AgentDescriptor) -> AgentDescriptor:
    await _set(f"agent_descriptor:{user_id}", descriptor.model_dump_json())
    return descriptor


async def save_agent_event(event_payload: dict) -> None:
    to_agent_id = event_payload.get("to_agent_id", "unknown")
    await _rpush(f"agent_events:{to_agent_id}", json.dumps(event_payload))
    await _ltrim(f"agent_events:{to_agent_id}", -100, -1)


async def load_agent_events(agent_id: str) -> list[dict]:
    history_raw = await _lrange(f"agent_events:{agent_id}", 0, -1)
    return [json.loads(m) for m in history_raw]


async def save_personal_item(user_id: str, kind: str, content: str) -> dict:
    item = {"kind": kind, "content": content, "created_at": time.time()}
    await _rpush(f"personal_items:{user_id}", json.dumps(item))
    await _ltrim(f"personal_items:{user_id}", -200, -1)
    return item


async def load_personal_items(user_id: str) -> list[dict]:
    raw = await _lrange(f"personal_items:{user_id}", 0, -1)
    return [json.loads(v) for v in raw]
