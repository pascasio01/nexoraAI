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
Eres {APP_NAME}, una asistente de IA avanzada creada por {CREATOR_NAME}, también conocido como {CREATOR_ALIAS}.

Reglas:
- Responde en el idioma del usuario.
- No inventes información.
- Si una función no está realmente activa, dilo claramente.
- Puedes usar herramientas para buscar en internet, consultar biblioteca y ejecutar acciones.
- Si el usuario pide guardar algo o recordar algo, puedes usar execute_action.
- Si el usuario pide datos actuales, usa search_web.
- Sé clara, útil, breve y elegante.
""".strip()


async def update_user_profile(user_id: str, last_interaction: str) -> None:
    if client is None:
        return

    try:
        old_profile = await get_profile(user_id)
        prompt = (
            f"Perfil actual: {old_profile}\n"
            f"Interacción: {last_interaction}\n"
            "Actualiza el perfil con hechos útiles y relativamente estables del usuario. "
            "No inventes. Sé breve."
        )

        res = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=120,
        )
        updated_profile = res.choices[0].message.content
        if updated_profile:
            await set_profile(user_id, updated_profile)
    except Exception as exc:
        logger.error(f"Error actualizando perfil: {exc}")


async def ask_nexora(user_id: str, text: str, channel: str) -> str:
    if client is None:
        return "⚠️ OpenAI no está configurado ahora mismo."

    if not await check_rate_limit(user_id):
        return "⚠️ Límite de mensajes alcanzado. Espera un minuto."

    history = await load_chat_memory(user_id)
    profile = await get_profile(user_id)

    sys_prompt = f"{SYSTEM_PROMPT}\nPerfil del usuario: {profile}\nCanal: {channel}"
    messages = [{"role": "system", "content": sys_prompt}] + history + [{"role": "user", "content": text}]

    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=800,
        )
    except Exception as exc:
        logger.error(f"Error OpenAI: {exc}")
        return "⚠️ Hubo un problema generando la respuesta."

    msg = response.choices[0].message

    if msg.tool_calls:
        messages.append(msg)

        for tool_call in msg.tool_calls:
            name = tool_call.function.name
            try:
                args = json.loads(tool_call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}

            if name == "search_web":
                res = await search_web(args.get("query", ""))
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": "search_web",
                        "content": json.dumps(res, ensure_ascii=False),
                    }
                )
            elif name == "consultar_biblioteca":
                res = await consultar_biblioteca(args.get("query", ""))
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": "consultar_biblioteca",
                        "content": json.dumps(res, ensure_ascii=False),
                    }
                )
            elif name == "execute_action":
                res = await execute_action(args.get("action_name", ""), args.get("details", {}))
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": "execute_action",
                        "content": res,
                    }
                )

        final = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            max_tokens=800,
        )
        answer = final.choices[0].message.content or "No pude generar una respuesta."
    else:
        answer = msg.content or "No pude generar una respuesta."

    await save_chat_memory(user_id, "user", text)
    await save_chat_memory(user_id, "assistant", answer)

    asyncio.create_task(update_user_profile(user_id, f"User: {text} | Nexora: {answer}"))
    return answer
