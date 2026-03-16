import json
import time
from collections import defaultdict, deque

from config import MAX_CHAT_HISTORY, RATE_LIMIT_PER_MINUTE
import deps

_memory = defaultdict(list)
_profiles = {}
_rate_limits = defaultdict(deque)


async def check_rate_limit(user_id: str) -> bool:
    if deps.r is not None:
        key = f"rate_limit:{user_id}"
        try:
            count = await deps.r.incr(key)
            if count == 1:
                await deps.r.expire(key, 60)
            return count <= RATE_LIMIT_PER_MINUTE
        except Exception:
            pass

    now = time.time()
    queue = _rate_limits[user_id]
    while queue and now - queue[0] > 60:
        queue.popleft()
    queue.append(now)
    return len(queue) <= RATE_LIMIT_PER_MINUTE


async def get_profile(user_id: str) -> str:
    if deps.r is not None:
        try:
            value = await deps.r.get(f"profile:{user_id}")
            if value:
                return value
        except Exception:
            pass
    return _profiles.get(user_id, "Usuario nuevo.")


async def set_profile(user_id: str, profile_text: str) -> None:
    if deps.r is not None:
        try:
            await deps.r.set(f"profile:{user_id}", profile_text)
            return
        except Exception:
            pass
    _profiles[user_id] = profile_text


async def save_chat_memory(user_id: str, role: str, content: str) -> None:
    message = {"role": role, "content": content}

    if deps.r is not None:
        try:
            await deps.r.rpush(f"chat:{user_id}", json.dumps(message))
            await deps.r.ltrim(f"chat:{user_id}", -MAX_CHAT_HISTORY, -1)
            return
        except Exception:
            pass

    _memory[user_id].append(message)
    if len(_memory[user_id]) > MAX_CHAT_HISTORY:
        _memory[user_id] = _memory[user_id][-MAX_CHAT_HISTORY:]


async def load_chat_memory(user_id: str) -> list[dict]:
    if deps.r is not None:
        try:
            history_raw = await deps.r.lrange(f"chat:{user_id}", 0, -1)
            return [json.loads(item) for item in history_raw]
        except Exception:
            pass
    return _memory.get(user_id, [])


async def reset_memory(user_id: str) -> None:
    if deps.r is not None:
        try:
            await deps.r.delete(f"chat:{user_id}")
        except Exception:
            pass
    _memory[user_id] = []
