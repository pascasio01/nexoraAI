from __future__ import annotations

import asyncio
import json

from config import APP_NAME, CREATOR_ALIAS, CREATOR_NAME, MODEL_NAME, logger
from deps import client
from memory import (
    check_rate_limit,
    get_profile,
    load_chat_memory,
    save_chat_memory,
    set_profile,
)
from tools_impl import consultar_biblioteca, execute_action, search_web
from tools_schema import tools

SYSTEM_PROMPT = f"""
Eres {APP_NAME}, una asistente de IA modular creada por {CREATOR_NAME} ({CREATOR_ALIAS}).
Prioriza precisión, seguridad y claridad.
Si una capacidad no está activa, dilo explícitamente.
Puedes usar tools para web, biblioteca y acciones.
""".strip()


async def update_user_profile(user_id: str, last_interaction: str):
    if client is None:
        return
    try:
        old_profile = await get_profile(user_id)
        prompt = (
            f"Perfil actual: {old_profile}\n"
            f"Interacción: {last_interaction}\n"
            "Actualiza el perfil del usuario con hechos estables y útiles."
        )
        res = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=120,
        )
        content = res.choices[0].message.content
        if content:
            await set_profile(user_id, content)
    except Exception as exc:
        logger.warning("Failed to update user profile: %s", exc)


async def _run_tool(name: str, args: dict):
    if name == "search_web":
        return await search_web(args.get("query", ""))
    if name == "consultar_biblioteca":
        return await consultar_biblioteca(args.get("query", ""))
    if name == "execute_action":
        return await execute_action(args.get("action_name", ""), args.get("details", {}))
    return {"error": f"Herramienta no soportada: {name}"}


async def ask_nexora(user_id: str, text: str, channel: str) -> str:
    if client is None:
        return "⚠️ OpenAI no configurado."

    if not await check_rate_limit(user_id):
        return "⚠️ Límite de mensajes alcanzado. Espera un minuto."

    history = await load_chat_memory(user_id)
    profile = await get_profile(user_id)

    messages = [
        {"role": "system", "content": f"{SYSTEM_PROMPT}\nPerfil: {profile}\nCanal: {channel}"},
        *history,
        {"role": "user", "content": text},
    ]

    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=800,
        )
        msg = response.choices[0].message
    except Exception as exc:
        logger.error("OpenAI error: %s", exc)
        return "⚠️ Hubo un problema generando la respuesta."

    answer = msg.content or "No pude generar una respuesta."
    if msg.tool_calls:
        messages.append(msg)
        for tool_call in msg.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments or "{}")
            tool_result = await _run_tool(name, args)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": name,
                    "content": json.dumps(tool_result, ensure_ascii=False)
                    if not isinstance(tool_result, str)
                    else tool_result,
                }
            )

        try:
            final = await client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                max_tokens=800,
            )
            answer = final.choices[0].message.content or answer
        except Exception as exc:
            logger.warning("Final response generation after tools failed: %s", exc)

    await save_chat_memory(user_id, "user", text)
    await save_chat_memory(user_id, "assistant", answer)
    asyncio.create_task(update_user_profile(user_id, f"User: {text} | Nexora: {answer}"))
    return answer
