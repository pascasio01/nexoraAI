from collections.abc import AsyncIterator

from config import APP_NAME, MODEL_NAME, logger
from deps import client
from memory import build_conversation_key, check_rate_limit, get_profile, load_chat_memory, save_chat_memory

SYSTEM_PROMPT = (
    f"Eres {APP_NAME}, una asistente personal en tiempo real. "
    "Responde en el idioma del usuario, con claridad y sin inventar hechos."
)


async def ask_nexora(
    user_id: str,
    text: str,
    channel: str,
    *,
    session_id: str | None = None,
    room_id: str | None = None,
    site_id: str | None = None,
    visitor_id: str | None = None,
) -> str:
    if not await check_rate_limit(user_id):
        return "⚠️ Límite de mensajes alcanzado. Espera un minuto."

    conversation_id = build_conversation_key(
        user_id=user_id,
        session_id=session_id,
        room_id=room_id,
        site_id=site_id,
        visitor_id=visitor_id,
    )
    history = await load_chat_memory(user_id=user_id, conversation_id=conversation_id)
    profile = await get_profile(user_id)

    if client is None:
        fallback = "⚠️ OpenAI no está configurado ahora mismo."
        await save_chat_memory(user_id, "user", text, conversation_id=conversation_id)
        await save_chat_memory(user_id, "assistant", fallback, conversation_id=conversation_id)
        return fallback

    sys_prompt = (
        f"{SYSTEM_PROMPT}\n"
        f"Perfil: {profile}\n"
        f"Canal: {channel}\n"
        f"Session: {session_id or 'n/a'} | Room: {room_id or 'n/a'} | Site: {site_id or 'n/a'}"
    )
    messages = [{"role": "system", "content": sys_prompt}, *history, {"role": "user", "content": text}]

    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            max_tokens=800,
        )
        answer = response.choices[0].message.content or "No pude generar una respuesta."
    except Exception as exc:
        logger.error("OpenAI request failed: %s", exc)
        answer = "⚠️ Hubo un problema generando la respuesta."

    await save_chat_memory(user_id, "user", text, conversation_id=conversation_id)
    await save_chat_memory(user_id, "assistant", answer, conversation_id=conversation_id)
    return answer


async def stream_nexora_response(
    user_id: str,
    text: str,
    channel: str,
    *,
    session_id: str | None = None,
    room_id: str | None = None,
    site_id: str | None = None,
    visitor_id: str | None = None,
) -> AsyncIterator[str]:
    """Streaming-ready interface. MVP emits one final chunk."""
    answer = await ask_nexora(
        user_id=user_id,
        text=text,
        channel=channel,
        session_id=session_id,
        room_id=room_id,
        site_id=site_id,
        visitor_id=visitor_id,
    )
    yield answer
