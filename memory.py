"""Memory layer with Redis + in-process fallback."""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from config import MAX_CHAT_HISTORY, RATE_LIMIT_PER_MINUTE


class MemoryStore:
    """Handles conversation memory, profile memory and session state."""

    def __init__(self, redis_client: Any | None = None) -> None:
        self.redis = redis_client
        self._chat: dict[str, list[dict[str, str]]] = defaultdict(list)
        self._profiles: dict[str, str] = {}
        self._assistant_cfg: dict[str, dict[str, Any]] = {}
        self._rate_limit: dict[str, int] = {}
        self._notes: dict[str, list[dict[str, Any]]] = defaultdict(list)

    @staticmethod
    def _chat_key(user_id: str, session_id: str) -> str:
        return f"chat:{user_id}:{session_id}"

    async def check_rate_limit(self, user_id: str) -> bool:
        if self.redis:
            key = f"rate_limit:{user_id}"
            count = await self.redis.incr(key)
            if count == 1:
                await self.redis.expire(key, 60)
            return count <= RATE_LIMIT_PER_MINUTE

        self._rate_limit[user_id] = self._rate_limit.get(user_id, 0) + 1
        return self._rate_limit[user_id] <= RATE_LIMIT_PER_MINUTE

    async def save_chat_message(self, user_id: str, session_id: str, role: str, content: str) -> None:
        message = {"role": role, "content": content}
        if self.redis:
            key = self._chat_key(user_id, session_id)
            await self.redis.rpush(key, json.dumps(message))
            await self.redis.ltrim(key, -MAX_CHAT_HISTORY, -1)
            return

        key = self._chat_key(user_id, session_id)
        self._chat[key].append(message)
        self._chat[key] = self._chat[key][-MAX_CHAT_HISTORY:]

    async def load_chat_history(self, user_id: str, session_id: str) -> list[dict[str, str]]:
        if self.redis:
            key = self._chat_key(user_id, session_id)
            records = await self.redis.lrange(key, 0, -1)
            return [json.loads(item) for item in records]

        return list(self._chat[self._chat_key(user_id, session_id)])

    async def reset_session(self, user_id: str, session_id: str) -> None:
        if self.redis:
            await self.redis.delete(self._chat_key(user_id, session_id))
            return
        self._chat.pop(self._chat_key(user_id, session_id), None)

    async def get_user_profile(self, user_id: str) -> str:
        if self.redis:
            return await self.redis.get(f"profile:{user_id}") or "Usuario nuevo."
        return self._profiles.get(user_id, "Usuario nuevo.")

    async def set_user_profile(self, user_id: str, profile_text: str) -> None:
        if self.redis:
            await self.redis.set(f"profile:{user_id}", profile_text)
            return
        self._profiles[user_id] = profile_text

    async def get_memory_summary(self, user_id: str) -> str:
        if self.redis:
            return await self.redis.get(f"summary:{user_id}") or ""
        return self._profiles.get(f"summary:{user_id}", "")

    async def set_memory_summary(self, user_id: str, summary: str) -> None:
        if self.redis:
            await self.redis.set(f"summary:{user_id}", summary)
            return
        self._profiles[f"summary:{user_id}"] = summary

    async def get_assistant_config(self, user_id: str) -> dict[str, Any]:
        if self.redis:
            raw = await self.redis.get(f"assistant_cfg:{user_id}")
            return json.loads(raw) if raw else {}
        return dict(self._assistant_cfg.get(user_id, {}))

    async def set_assistant_config(self, user_id: str, config: dict[str, Any]) -> None:
        if self.redis:
            await self.redis.set(f"assistant_cfg:{user_id}", json.dumps(config))
            return
        self._assistant_cfg[user_id] = dict(config)

    async def add_note(self, user_id: str, note: dict[str, Any]) -> None:
        if self.redis:
            key = f"notes:{user_id}"
            await self.redis.rpush(key, json.dumps(note))
            return
        self._notes[user_id].append(note)

    async def list_notes(self, user_id: str) -> list[dict[str, Any]]:
        if self.redis:
            key = f"notes:{user_id}"
            items = await self.redis.lrange(key, 0, -1)
            return [json.loads(item) for item in items]
        return list(self._notes[user_id])
