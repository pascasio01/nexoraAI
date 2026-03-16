from __future__ import annotations

import json
from collections import defaultdict, deque

from config import MAX_CHAT_HISTORY, RATE_LIMIT_PER_MINUTE
from deps import r

_local_chat: dict[str, deque[dict[str, str]]] = defaultdict(lambda: deque(maxlen=MAX_CHAT_HISTORY))
_local_profile: dict[str, str] = {}
_local_rate_count: dict[str, int] = defaultdict(int)


async def check_rate_limit(user_id: str) -> bool:
    if r:
        key = f"rate_limit:{user_id}"
        count = await r.incr(key)
        if count == 1:
            await r.expire(key, 60)
        return count <= RATE_LIMIT_PER_MINUTE

    _local_rate_count[user_id] += 1
    return _local_rate_count[user_id] <= RATE_LIMIT_PER_MINUTE


async def get_profile(user_id: str) -> str:
    if r:
        return await r.get(f"profile:{user_id}") or "Usuario nuevo."
    return _local_profile.get(user_id, "Usuario nuevo.")


async def set_profile(user_id: str, profile_text: str) -> None:
    if r:
        await r.set(f"profile:{user_id}", profile_text)
        return
    _local_profile[user_id] = profile_text


async def save_chat_memory(user_id: str, role: str, content: str) -> None:
    if r:
        await r.rpush(f"chat:{user_id}", json.dumps({"role": role, "content": content}))
        await r.ltrim(f"chat:{user_id}", -MAX_CHAT_HISTORY, -1)
        return

    _local_chat[user_id].append({"role": role, "content": content})


async def load_chat_memory(user_id: str) -> list[dict[str, str]]:
    if r:
        history_raw = await r.lrange(f"chat:{user_id}", 0, -1)
        return [json.loads(item) for item in history_raw]

    return list(_local_chat[user_id])


async def reset_memory(user_id: str) -> None:
    if r:
        await r.delete(f"chat:{user_id}")
        await r.delete(f"profile:{user_id}")
        await r.delete(f"rate_limit:{user_id}")
        return

    _local_chat.pop(user_id, None)
    _local_profile.pop(user_id, None)
    _local_rate_count.pop(user_id, None)
