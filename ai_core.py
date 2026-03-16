from __future__ import annotations

import asyncio
import json

from config import logger, settings
from deps import get_openai_client
from memory import (
    check_rate_limit,
    get_assistant_settings,
    get_profile,
    load_chat_memory,
    save_chat_memory,
    set_profile,
)
from tools_impl import execute_tool_call
from tools_schema import tools

SYSTEM_PROMPT = (
    "Eres Nexora, un asistente personal modular. "
    "Usa herramientas cuando aporten valor y sé transparente si un servicio no está activo."
)


async def update_user_profile(user_id: str, interaction: str, assistant_id: str = "default") -> None:
    client = get_openai_client()
    if client is None:
        return

    try:
        current_profile = await get_profile(user_id, assistant_id)
        prompt = (
            f"Perfil actual: {current_profile}\n"
            f"Interacción: {interaction}\n"
            "Actualiza solo hechos estables y útiles en formato breve."
        )
        completion = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=120,
        )
        new_profile = completion.choices[0].message.content or current_profile
        await set_profile(user_id, new_profile, assistant_id)
    except Exception as exc:
        logger.warning("No se pudo actualizar perfil de usuario: %s", exc)


async def ask_nexora(user_id: str, text: str, channel: str, assistant_id: str = "default") -> str:
    if not await check_rate_limit(user_id):
        return "⚠️ Alcanzaste el límite temporal de mensajes. Intenta de nuevo en un minuto."

    history = await load_chat_memory(user_id, assistant_id)
    profile = await get_profile(user_id, assistant_id)
    assistant_settings = await get_assistant_settings(user_id, assistant_id)

    client = get_openai_client()
    if client is None:
        fallback = (
            "OpenAI no está configurado todavía. "
            "Define OPENAI_API_KEY para habilitar respuestas inteligentes."
        )
        await save_chat_memory(user_id, "user", text, assistant_id)
        await save_chat_memory(user_id, "assistant", fallback, assistant_id)
        return fallback

    context_prompt = (
        f"{SYSTEM_PROMPT}\n"
        f"Canal: {channel}\n"
        f"Perfil de usuario: {profile}\n"
        f"Configuración asistente: {json.dumps(assistant_settings, ensure_ascii=False)}"
    )
    messages = [{"role": "system", "content": context_prompt}] + history + [{"role": "user", "content": text}]

    try:
        response = await client.chat.completions.create(
            model=settings.model_name,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=700,
        )

        message = response.choices[0].message
        if message.tool_calls:
            messages.append(message)
            for tool_call in message.tool_calls:
                name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments or "{}")
                tool_result = await execute_tool_call(name, arguments, user_id, assistant_id)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": name,
                        "content": json.dumps(tool_result, ensure_ascii=False),
                    }
                )

            final_response = await client.chat.completions.create(
                model=settings.model_name,
                messages=messages,
                max_tokens=700,
            )
            answer = final_response.choices[0].message.content or "No pude generar una respuesta ahora."
        else:
            answer = message.content or "No pude generar una respuesta ahora."

    except Exception as exc:
        logger.warning("Error consultando OpenAI, se aplica fallback: %s", exc)
        answer = "Tu asistente está temporalmente degradado, pero sigue en línea. Intenta nuevamente en unos segundos."

    await save_chat_memory(user_id, "user", text, assistant_id)
    await save_chat_memory(user_id, "assistant", answer, assistant_id)
    asyncio.create_task(update_user_profile(user_id, f"User: {text} | Assistant: {answer}", assistant_id))
    return answer
