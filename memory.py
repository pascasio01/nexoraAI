import json

from config import MAX_CHAT_HISTORY, RATE_LIMIT_PER_MINUTE, logger
from deps import r


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
        logger.warning(f"Rate limit desactivado por error Redis: {exc}")
        return True


async def get_profile(user_id: str) -> str:
    if r is None:
        return "Usuario nuevo."
    try:
        return await r.get(f"profile:{user_id}") or "Usuario nuevo."
    except Exception as exc:
        logger.warning(f"No se pudo leer perfil: {exc}")
        return "Usuario nuevo."


async def set_profile(user_id: str, profile_text: str) -> None:
    if r is None:
        return
    try:
        await r.set(f"profile:{user_id}", profile_text)
    except Exception as exc:
        logger.warning(f"No se pudo guardar perfil: {exc}")


async def save_chat_memory(user_id: str, role: str, content: str) -> None:
    if r is None:
        return
    try:
        await r.rpush(f"chat:{user_id}", json.dumps({"role": role, "content": content}))
        await r.ltrim(f"chat:{user_id}", -MAX_CHAT_HISTORY, -1)
    except Exception as exc:
        logger.warning(f"No se pudo guardar memoria: {exc}")


async def load_chat_memory(user_id: str) -> list[dict]:
    if r is None:
        return []
    try:
        history_raw = await r.lrange(f"chat:{user_id}", 0, -1)
        return [json.loads(m) for m in history_raw]
    except Exception as exc:
        logger.warning(f"No se pudo cargar memoria: {exc}")
        return []


async def reset_memory(user_id: str) -> None:
    if r is None:
        return
    try:
        await r.delete(f"chat:{user_id}")
        await r.delete(f"profile:{user_id}")
    except Exception as exc:
        logger.warning(f"No se pudo reiniciar memoria: {exc}")
