import asyncio
import json

from config import APP_NAME, CREATOR_ALIAS, CREATOR_NAME, MODEL_NAME, logger
import deps
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
You are {APP_NAME}, a long-term personal AI assistant platform created by {CREATOR_NAME} ({CREATOR_ALIAS}).

Guidelines:
- Be helpful, precise, and safe.
- Keep responses in the same language used by the user.
- Do not invent facts.
- Use tools when real-time data or actions are required.
- Be transparent when any service is disabled.
""".strip()


async def _update_user_profile(user_id: str, last_interaction: str) -> None:
    if deps.client is None:
        return

    previous_profile = await get_profile(user_id)
    prompt = (
        f"Current profile: {previous_profile}\n"
        f"New interaction: {last_interaction}\n"
        "Return an updated short profile with stable user facts only."
    )

    try:
        completion = await deps.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=120,
        )
        updated = completion.choices[0].message.content
        if updated:
            await set_profile(user_id, updated)
    except Exception:
        return


async def ask_nexora(user_id: str, text: str, channel: str) -> str:
    if not await check_rate_limit(user_id):
        return "⚠️ Límite de mensajes alcanzado. Espera un minuto."

    if deps.client is None:
        return "⚠️ OpenAI no está configurado en este entorno."

    history = await load_chat_memory(user_id)
    profile = await get_profile(user_id)

    messages = [
        {
            "role": "system",
            "content": f"{SYSTEM_PROMPT}\nUser profile: {profile}\nChannel: {channel}",
        },
        *history,
        {"role": "user", "content": text},
    ]

    try:
        first = await deps.client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=450,
        )
    except Exception as exc:
        logger.error(f"OpenAI request failed: {exc}")
        return "⚠️ Hubo un problema generando la respuesta."

    message = first.choices[0].message
    tool_calls = getattr(message, "tool_calls", None) or []

    if tool_calls:
        messages.append(
            {
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [call.model_dump() for call in tool_calls],
            }
        )

        for call in tool_calls:
            name = call.function.name
            try:
                args = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}

            if name == "search_web":
                result = await search_web(args.get("query", ""))
            elif name == "consultar_biblioteca":
                result = await consultar_biblioteca(args.get("query", ""))
            elif name == "execute_action":
                result = await execute_action(
                    args.get("action_name", "unknown"),
                    args.get("details", {}),
                    user_id,
                )
            else:
                result = {"error": f"Unknown tool: {name}"}

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "name": name,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

        try:
            final = await deps.client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                max_tokens=450,
            )
            answer = final.choices[0].message.content or "No pude generar respuesta."
        except Exception as exc:
            logger.error(f"OpenAI follow-up failed: {exc}")
            answer = "⚠️ Hubo un problema procesando herramientas."
    else:
        answer = message.content or "No pude generar respuesta."

    await save_chat_memory(user_id, "user", text)
    await save_chat_memory(user_id, "assistant", answer)
    asyncio.create_task(_update_user_profile(user_id, text))
    return answer
