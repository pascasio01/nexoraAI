import json

from config import r, logger, MAX_CHAT_HISTORY, RATE_LIMIT_PER_MINUTE


# =========================
# RATE LIMIT
# =========================
async def check_rate_limit(user_id: str) -> bool:
    if r is None:
        return True
    try:
        key = f"rate_limit:{user_id}"
        count = await r.incr(key)
        if count == 1:
            await r.expire(key, 60)
        return count <= RATE_LIMIT_PER_MINUTE
    except Exception as e:
        logger.warning(f"Rate limit desactivado por error Redis: {e}")
        return True


# =========================
# CHAT MEMORY
# =========================
async def save_chat_memory(user_id: str, role: str, content: str) -> None:
    if r is None:
        return
    try:
        await r.rpush(f"chat:{user_id}", json.dumps({"role": role, "content": content}))
        await r.ltrim(f"chat:{user_id}", -MAX_CHAT_HISTORY, -1)
    except Exception as e:
        logger.warning(f"No se pudo guardar memoria: {e}")


async def load_chat_memory(user_id: str):
    if r is None:
        return []
    try:
        history_raw = await r.lrange(f"chat:{user_id}", 0, -1)
        return [json.loads(m) for m in history_raw]
    except Exception as e:
        logger.warning(f"No se pudo cargar memoria: {e}")
        return []


async def reset_memory(user_id: str) -> None:
    if r is None:
        return
    try:
        await r.delete(f"chat:{user_id}")
    except Exception as e:
        logger.warning(f"No se pudo reiniciar memoria: {e}")


# =========================
# USER PROFILE
# =========================
async def get_profile(user_id: str) -> str:
    if r is None:
        return "Usuario nuevo."
    try:
        return await r.get(f"profile:{user_id}") or "Usuario nuevo."
    except Exception as e:
        logger.warning(f"No se pudo obtener perfil: {e}")
        return "Usuario nuevo."


async def set_profile(user_id: str, profile_text: str) -> None:
    if r is None:
        return
    try:
        await r.set(f"profile:{user_id}", profile_text)
    except Exception as e:
        logger.warning(f"No se pudo guardar perfil: {e}")
