import json

from config import MAX_CHAT_HISTORY, RATE_LIMIT_PER_MINUTE, logger
from deps import r


def build_conversation_key(
    user_id: str,
    session_id: str | None = None,
    room_id: str | None = None,
    site_id: str | None = None,
    visitor_id: str | None = None,
) -> str:
    segments = [f"user:{user_id or 'anonymous'}"]
    if session_id:
        segments.append(f"session:{session_id}")
    if room_id:
        segments.append(f"room:{room_id}")
    if site_id:
        segments.append(f"site:{site_id}")
    if visitor_id:
        segments.append(f"visitor:{visitor_id}")
    return "|".join(segments)


async def check_rate_limit(user_id: str) -> bool:
    if r is None:
        return True
    try:
        key = f"rate_limit:{user_id}"
        count = await r.incr(key)
        if count == 1:
            await r.expire(key, 60)
        return count <= RATE_LIMIT_PER_MINUTE
    except Exception as exc:
        logger.warning("Rate limit check failed, allowing request: %s", exc)
        return True


async def get_profile(user_id: str) -> str:
    if r is None:
        return "Usuario nuevo."
    try:
        return await r.get(f"profile:{user_id}") or "Usuario nuevo."
    except Exception as exc:
        logger.warning("Profile load failed: %s", exc)
        return "Usuario nuevo."


async def set_profile(user_id: str, profile_text: str) -> None:
    if r is None:
        return
    try:
        await r.set(f"profile:{user_id}", profile_text)
    except Exception as exc:
        logger.warning("Profile save failed: %s", exc)


async def save_chat_memory(user_id: str, role: str, content: str, conversation_id: str | None = None) -> None:
    if r is None:
        return
    key = f"chat:{conversation_id or user_id}"
    try:
        await r.rpush(key, json.dumps({"role": role, "content": content}))
        await r.ltrim(key, -MAX_CHAT_HISTORY, -1)
    except Exception as exc:
        logger.warning("Memory write failed: %s", exc)


async def load_chat_memory(user_id: str, conversation_id: str | None = None) -> list[dict]:
    if r is None:
        return []
    key = f"chat:{conversation_id or user_id}"
    try:
        history_raw = await r.lrange(key, 0, -1)
        return [json.loads(item) for item in history_raw]
    except Exception as exc:
        logger.warning("Memory read failed: %s", exc)
        return []


async def reset_memory(user_id: str, conversation_id: str | None = None) -> None:
    if r is None:
        return
    key = f"chat:{conversation_id or user_id}"
    try:
        await r.delete(key)
    except Exception as exc:
        logger.warning("Memory reset failed: %s", exc)


async def load_persistent_history(user_id: str, session_id: str | None = None) -> list[dict]:
    conversation_id = build_conversation_key(user_id=user_id, session_id=session_id)
    return await load_chat_memory(user_id=user_id, conversation_id=conversation_id)


async def save_persistent_history(
    user_id: str,
    role: str,
    content: str,
    session_id: str | None = None,
) -> None:
    conversation_id = build_conversation_key(user_id=user_id, session_id=session_id)
    await save_chat_memory(user_id=user_id, role=role, content=content, conversation_id=conversation_id)
