from __future__ import annotations

import json
import time
from collections import defaultdict
from typing import Any

import deps
from config import MAX_CHAT_HISTORY, RATE_LIMIT_PER_MINUTE
from models import AgentEvent, AgentRecord, AgentSettings

_fallback_history: dict[str, list[dict[str, str]]] = defaultdict(list)
_fallback_profiles: dict[str, str] = {}
_fallback_summaries: dict[str, str] = {}
_fallback_settings: dict[str, AgentSettings] = {}
_fallback_agents: dict[str, AgentRecord] = {}
_fallback_events: dict[str, list[AgentEvent]] = defaultdict(list)
_fallback_rate_limits: dict[str, tuple[int, float]] = {}
_fallback_notes: dict[str, list[dict[str, Any]]] = defaultdict(list)
_fallback_tasks: dict[str, list[dict[str, Any]]] = defaultdict(list)


async def check_rate_limit(user_id: str) -> bool:
    """Enforce per-user chat rate limit with Redis or in-memory fallback."""
    redis_client = deps.redis_client
    if redis_client is not None:
        key = f"rate_limit:{user_id}"
        count = await redis_client.incr(key)
        if count == 1:
            await redis_client.expire(key, 60)
        return count <= RATE_LIMIT_PER_MINUTE

    now = time.time()
    count, ts = _fallback_rate_limits.get(user_id, (0, now))
    if now - ts >= 60:
        count, ts = 0, now
    count += 1
    _fallback_rate_limits[user_id] = (count, ts)
    return count <= RATE_LIMIT_PER_MINUTE


async def save_chat_memory(user_id: str, role: str, content: str) -> None:
    """Persist short conversation history per user."""
    redis_client = deps.redis_client
    message = {"role": role, "content": content}
    if redis_client is not None:
        key = f"chat:{user_id}"
        await redis_client.rpush(key, json.dumps(message))
        await redis_client.ltrim(key, -MAX_CHAT_HISTORY, -1)
        return

    _fallback_history[user_id].append(message)
    _fallback_history[user_id] = _fallback_history[user_id][-MAX_CHAT_HISTORY:]


async def load_chat_memory(user_id: str) -> list[dict[str, str]]:
    redis_client = deps.redis_client
    if redis_client is not None:
        raw = await redis_client.lrange(f"chat:{user_id}", 0, -1)
        return [json.loads(item) for item in raw]
    return list(_fallback_history.get(user_id, []))


async def reset_memory(user_id: str) -> None:
    redis_client = deps.redis_client
    if redis_client is not None:
        await redis_client.delete(f"chat:{user_id}", f"profile:{user_id}", f"summary:{user_id}")
    _fallback_history.pop(user_id, None)
    _fallback_profiles.pop(user_id, None)
    _fallback_summaries.pop(user_id, None)


async def get_profile(user_id: str) -> str:
    redis_client = deps.redis_client
    if redis_client is not None:
        return await redis_client.get(f"profile:{user_id}") or "Usuario nuevo."
    return _fallback_profiles.get(user_id, "Usuario nuevo.")


async def set_profile(user_id: str, profile_text: str) -> None:
    redis_client = deps.redis_client
    if redis_client is not None:
        await redis_client.set(f"profile:{user_id}", profile_text)
    _fallback_profiles[user_id] = profile_text


async def get_summary(user_id: str) -> str:
    redis_client = deps.redis_client
    if redis_client is not None:
        return await redis_client.get(f"summary:{user_id}") or ""
    return _fallback_summaries.get(user_id, "")


async def set_summary(user_id: str, summary_text: str) -> None:
    redis_client = deps.redis_client
    if redis_client is not None:
        await redis_client.set(f"summary:{user_id}", summary_text)
    _fallback_summaries[user_id] = summary_text


async def get_agent_settings(user_id: str) -> AgentSettings:
    redis_client = deps.redis_client
    if redis_client is not None:
        raw = await redis_client.get(f"agent_settings:{user_id}")
        if raw:
            return AgentSettings(**json.loads(raw))
    return _fallback_settings.get(user_id, AgentSettings())


async def set_agent_settings(user_id: str, settings: AgentSettings) -> None:
    redis_client = deps.redis_client
    if redis_client is not None:
        await redis_client.set(f"agent_settings:{user_id}", settings.model_dump_json())
    _fallback_settings[user_id] = settings


async def get_or_create_agent(user_id: str) -> AgentRecord:
    agent_id = f"agent:{user_id}"
    redis_client = deps.redis_client
    if redis_client is not None:
        raw = await redis_client.get(f"agent_registry:{agent_id}")
        if raw:
            return AgentRecord(**json.loads(raw))

    existing = _fallback_agents.get(agent_id)
    if existing:
        return existing

    agent = AgentRecord(
        user_id=user_id,
        agent_id=agent_id,
        endpoint=f"/agents/{agent_id}/events",
        metadata={"capabilities": ["chat", "tools", "events"], "vector_memory": "planned"},
        tools_allowed=["search_web", "manage_notes_tasks", "execute_webhook", "set_reminder"],
        permissions={"chat": True, "tools": True, "agent_messaging": True},
    )
    await save_agent(agent)
    return agent


async def save_agent(agent: AgentRecord) -> None:
    redis_client = deps.redis_client
    if redis_client is not None:
        await redis_client.set(f"agent_registry:{agent.agent_id}", agent.model_dump_json())
    _fallback_agents[agent.agent_id] = agent


async def list_agents() -> list[AgentRecord]:
    redis_client = deps.redis_client
    if redis_client is not None:
        items = []
        cursor = 0
        while True:
            cursor, keys = await redis_client.scan(cursor=cursor, match="agent_registry:agent:*", count=100)
            for key in keys:
                raw = await redis_client.get(key)
                if raw:
                    items.append(AgentRecord(**json.loads(raw)))
            if cursor == 0:
                break
        if items:
            return items
    return list(_fallback_agents.values())


async def save_agent_event(event: AgentEvent) -> None:
    redis_client = deps.redis_client
    if redis_client is not None:
        await redis_client.rpush(f"agent_events:{event.to_agent_id}", event.model_dump_json())
        await redis_client.ltrim(f"agent_events:{event.to_agent_id}", -100, -1)
    _fallback_events[event.to_agent_id].append(event)
    _fallback_events[event.to_agent_id] = _fallback_events[event.to_agent_id][-100:]


async def get_agent_events(agent_id: str, limit: int = 20) -> list[AgentEvent]:
    redis_client = deps.redis_client
    if redis_client is not None:
        raw = await redis_client.lrange(f"agent_events:{agent_id}", -limit, -1)
        if raw:
            return [AgentEvent(**json.loads(item)) for item in raw]
    return list(_fallback_events.get(agent_id, []))[-limit:]


async def save_note(user_id: str, note: dict[str, Any]) -> dict[str, Any]:
    _fallback_notes[user_id].append(note)
    return note


async def save_task(user_id: str, task: dict[str, Any]) -> dict[str, Any]:
    _fallback_tasks[user_id].append(task)
    return task


async def list_notes(user_id: str) -> list[dict[str, Any]]:
    return list(_fallback_notes.get(user_id, []))


async def list_tasks(user_id: str) -> list[dict[str, Any]]:
    return list(_fallback_tasks.get(user_id, []))
