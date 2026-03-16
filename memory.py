import json
from typing import Any

from config import MAX_CHAT_HISTORY, RATE_LIMIT_PER_MINUTE, logger
from deps import r

_in_memory_store: dict[str, Any] = {}


def _fallback_get(key: str, default: Any = None) -> Any:
    return _in_memory_store.get(key, default)


def _fallback_set(key: str, value: Any) -> None:
    _in_memory_store[key] = value


async def check_rate_limit(user_id: str) -> bool:
    key = f"rate_limit:{user_id}"
    if r is None:
        count = int(_fallback_get(key, 0)) + 1
        _fallback_set(key, count)
        return count <= RATE_LIMIT_PER_MINUTE
    try:
        count = await r.incr(key)
        if count == 1:
            await r.expire(key, 60)
        return count <= RATE_LIMIT_PER_MINUTE
    except Exception as e:
        logger.warning(f"Rate limit fallback activo: {e}")
        return True


async def load_chat_memory(user_id: str):
    key = f"chat:{user_id}"
    if r is None:
        return _fallback_get(key, [])
    try:
        history_raw = await r.lrange(key, 0, -1)
        return [json.loads(m) for m in history_raw]
    except Exception as e:
        logger.warning(f"No se pudo cargar memoria, usando fallback: {e}")
        return _fallback_get(key, [])


async def save_chat_memory(user_id: str, role: str, content: str) -> None:
    key = f"chat:{user_id}"
    payload = {"role": role, "content": content}
    if r is None:
        history = _fallback_get(key, [])
        history.append(payload)
        _fallback_set(key, history[-MAX_CHAT_HISTORY:])
        return
    try:
        await r.rpush(key, json.dumps(payload))
        await r.ltrim(key, -MAX_CHAT_HISTORY, -1)
    except Exception as e:
        logger.warning(f"No se pudo guardar memoria, usando fallback: {e}")
        history = _fallback_get(key, [])
        history.append(payload)
        _fallback_set(key, history[-MAX_CHAT_HISTORY:])


async def reset_memory(user_id: str) -> None:
    key = f"chat:{user_id}"
    if r is None:
        _in_memory_store.pop(key, None)
        return
    try:
        await r.delete(key)
    except Exception as e:
        logger.warning(f"No se pudo reiniciar memoria en Redis: {e}")
        _in_memory_store.pop(key, None)


async def get_profile(user_id: str) -> str:
    key = f"profile:{user_id}"
    if r is None:
        return _fallback_get(key, "Usuario nuevo.")
    try:
        return await r.get(key) or "Usuario nuevo."
    except Exception as e:
        logger.warning(f"No se pudo cargar perfil, usando fallback: {e}")
        return _fallback_get(key, "Usuario nuevo.")


async def set_profile(user_id: str, profile_text: str) -> None:
    key = f"profile:{user_id}"
    if r is None:
        _fallback_set(key, profile_text)
        return
    try:
        await r.set(key, profile_text)
    except Exception as e:
        logger.warning(f"No se pudo guardar perfil, usando fallback: {e}")
        _fallback_set(key, profile_text)


async def get_assistant_settings(user_id: str) -> dict[str, Any]:
    key = f"assistant_settings:{user_id}"
    default = {
        "tone": "premium",
        "response_length": "balanced",
        "voice_enabled": False,
        "avatar_enabled": False,
    }
    if r is None:
        return _fallback_get(key, default)
    try:
        raw = await r.get(key)
        return json.loads(raw) if raw else default
    except Exception as e:
        logger.warning(f"No se pudo cargar assistant settings, usando fallback: {e}")
        return _fallback_get(key, default)


async def set_assistant_settings(user_id: str, settings: dict[str, Any]) -> dict[str, Any]:
    key = f"assistant_settings:{user_id}"
    if r is None:
        _fallback_set(key, settings)
        return settings
    try:
        await r.set(key, json.dumps(settings, ensure_ascii=False))
        return settings
    except Exception as e:
        logger.warning(f"No se pudo guardar assistant settings, usando fallback: {e}")
        _fallback_set(key, settings)
        return settings


async def get_user_session(user_id: str) -> dict[str, Any]:
    key = f"session:{user_id}"
    default = {"assistant_id": f"assistant::{user_id}", "mode": "personal"}
    if r is None:
        return _fallback_get(key, default)
    try:
        raw = await r.get(key)
        return json.loads(raw) if raw else default
    except Exception as e:
        logger.warning(f"No se pudo cargar sesión, usando fallback: {e}")
        return _fallback_get(key, default)
