import json

from config import APP_NAME, MODEL_NAME, OPENAI_API_KEY, logger
from memory import (
    append_personal_memory,
    check_rate_limit,
    get_user_context,
    load_chat_memory,
    normalize_user_id,
    save_chat_memory,
)

try:
    from openai import AsyncOpenAI
except ImportError:  # pragma: no cover
    AsyncOpenAI = None

client = AsyncOpenAI(api_key=OPENAI_API_KEY) if (AsyncOpenAI and OPENAI_API_KEY) else None


def _context_to_system_prompt(context: dict, channel: str) -> str:
    settings = json.dumps(context.get("assistant_settings", {}), ensure_ascii=False)
    personal_memory = json.dumps(context.get("personal_memory", []), ensure_ascii=False)
    return (
        f"Eres {APP_NAME}. Canal: {channel}. "
        f"Perfil del usuario: {context.get('profile', 'Usuario nuevo.')}. "
        f"Preferencias de asistente: {settings}. "
        f"Memoria personal: {personal_memory}. "
        "Usa este contexto para personalizar sin mezclar usuarios."
    )


async def ask_nexora(user_id: str, text: str, channel: str) -> str:
    user_id = normalize_user_id(user_id)

    if not await check_rate_limit(user_id):
        return "⚠️ Límite de mensajes alcanzado. Espera un minuto."

    history = await load_chat_memory(user_id)
    user_context = await get_user_context(user_id)

    messages = [{"role": "system", "content": _context_to_system_prompt(user_context, channel)}]
    messages.extend(history)
    messages.append({"role": "user", "content": text})

    if client is None:
        answer = "⚠️ AI service is currently unavailable."
    else:
        try:
            response = await client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                max_tokens=500,
            )
            answer = response.choices[0].message.content or "No pude generar respuesta."
        except Exception as exc:
            logger.warning(f"OpenAI fallback: {exc}")
            answer = "⚠️ AI service is currently unavailable."

    await save_chat_memory(user_id, "user", text)
    await save_chat_memory(user_id, "assistant", answer)
    return answer


async def save_personal_note(user_id: str, note: str) -> None:
    await append_personal_memory(user_id, note)
