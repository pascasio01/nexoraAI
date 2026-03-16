from __future__ import annotations

from collections.abc import AsyncIterator

from config import APP_NAME, MODEL_NAME, logger
from deps import client
from events import build_event
from memory import check_rate_limit, load_chat_memory, save_chat_memory
from realtime_types import AssistantState, RealtimeContext

SYSTEM_PROMPT = (
    f"Eres {APP_NAME}, un asistente personal en tiempo real. "
    "Responde de forma clara, útil y breve."
)


async def ask_nexora(user_id: str, text: str, channel: str = "Web") -> str:
    if not await check_rate_limit(user_id):
        return "⚠️ Límite de mensajes alcanzado. Espera un minuto."

    history = await load_chat_memory(user_id)
    await save_chat_memory(user_id, "user", text)

    if not client:
        reply = (
            f"{APP_NAME} está activa en modo local. "
            "Configura OPENAI_API_KEY para respuestas generativas completas."
        )
        await save_chat_memory(user_id, "assistant", reply)
        return reply

    messages = [{"role": "system", "content": f"{SYSTEM_PROMPT} Canal: {channel}"}]
    messages.extend(history)
    messages.append({"role": "user", "content": text})

    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.5,
        )
        reply = (response.choices[0].message.content or "").strip() or "No pude responder todavía."
    except Exception as exc:
        logger.error("Assistant generation failed: %s", exc)
        reply = "Tuve un problema temporal generando la respuesta."

    await save_chat_memory(user_id, "assistant", reply)
    return reply


async def stream_assistant_events(
    context: RealtimeContext,
    user_text: str,
    channel: str = "WebSocket",
) -> AsyncIterator[dict]:
    yield build_event("assistant.state", context, {"state": AssistantState.LISTENING.value}).model_dump()
    yield build_event("assistant.state", context, {"state": AssistantState.THINKING.value}).model_dump()
    yield build_event("typing.start", context, {}).model_dump()

    answer = await ask_nexora(context.user_id, user_text, channel)

    yield build_event("assistant.state", context, {"state": AssistantState.RESPONDING.value}).model_dump()
    yield build_event(
        "message.assistant",
        context,
        {
            "text": answer,
            "chunk": answer,
            "chunk_index": 0,
            "is_final": True,
            "streaming": False,
        },
    ).model_dump()
    yield build_event("typing.stop", context, {}).model_dump()
    yield build_event("assistant.state", context, {"state": AssistantState.IDLE.value}).model_dump()
