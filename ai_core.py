import json
import asyncio
from datetime import datetime

import httpx

from config import (
    client,
    tavily,
    MODEL_NAME,
    APP_NAME,
    CREATOR_NAME,
    CREATOR_ALIAS,
    ACTION_WEBHOOK_URL,
    OWNER_ID,
    logger,
)
from memory import (
    check_rate_limit,
    load_chat_memory,
    save_chat_memory,
    get_profile,
    set_profile,
)

# =========================
# SYSTEM PROMPT
# =========================
SYSTEM_PROMPT = (
    f"Eres {APP_NAME}, una asistente de IA avanzada creada por {CREATOR_NAME}, "
    f"también conocido como {CREATOR_ALIAS}.\n\n"
    "Reglas:\n"
    "- Responde en el idioma del usuario.\n"
    "- No inventes información.\n"
    "- Si una función no está realmente activa, dilo claramente.\n"
    "- Puedes usar herramientas para buscar en internet, consultar biblioteca y ejecutar acciones.\n"
    "- Si el usuario pide guardar algo o recordar algo, puedes usar execute_action.\n"
    "- Si el usuario pide datos actuales, usa search_web.\n"
    "- Sé clara, útil, breve y elegante."
)

# =========================
# TOOLS SCHEMA
# =========================
_tools = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Busca en tiempo real en internet.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_action",
            "description": "Guarda notas, crea recordatorios, agenda eventos o genera reportes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action_name": {
                        "type": "string",
                        "enum": [
                            "save_note",
                            "set_reminder",
                            "set_calendar_event",
                            "send_report",
                            "location_alarm",
                        ],
                    },
                    "details": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "content": {"type": "string"},
                            "category": {
                                "type": "string",
                                "enum": [
                                    "Trabajo",
                                    "Personal",
                                    "Idea",
                                    "Finanzas",
                                    "Estudio",
                                    "Seguridad",
                                    "Otro",
                                ],
                            },
                            "priority": {
                                "type": "string",
                                "enum": ["Alta", "Media", "Baja"],
                            },
                            "schedule_time": {"type": "string"},
                            "destination": {"type": "string"},
                            "report_type": {
                                "type": "string",
                                "enum": ["diario", "semanal", "ideas", "tasks", "mixed"],
                            },
                        },
                        "required": ["content"],
                    },
                },
                "required": ["action_name", "details"],
            },
        },
    },
]


# =========================
# WEB SEARCH
# =========================
async def search_web(query: str):
    if tavily is None:
        return [{"error": "Búsqueda web desactivada"}]
    try:
        result = tavily.search(query=query, max_results=3)
        return [
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("content", ""),
            }
            for item in result.get("results", [])
        ]
    except Exception as e:
        logger.warning(f"Error buscando en web: {e}")
        return [{"error": f"Error de búsqueda: {e}"}]


# =========================
# EXECUTE ACTION
# =========================
async def execute_action(action_name: str, details: dict) -> str:
    if not ACTION_WEBHOOK_URL:
        return "ACTION_WEBHOOK_URL no configurado."
    try:
        async with httpx.AsyncClient(timeout=20) as http:
            payload = {
                "action": action_name,
                "user_id": OWNER_ID,
                "agent": APP_NAME,
                "data": {**details, "timestamp": datetime.utcnow().isoformat()},
            }
            res = await http.post(ACTION_WEBHOOK_URL, json=payload)
            return f"Acción '{action_name}' enviada. Estado: {res.status_code}"
    except Exception as e:
        return f"Error ejecutando acción: {e}"


# =========================
# PROFILE UPDATER
# =========================
async def _update_user_profile(user_id: str, last_interaction: str) -> None:
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
        await set_profile(user_id, res.choices[0].message.content)
    except Exception as e:
        logger.error(f"Error actualizando perfil: {e}")


# =========================
# MAIN AI FUNCTION
# =========================
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
            tools=_tools,
            tool_choice="auto",
            max_tokens=800,
        )
    except Exception as e:
        logger.error(f"Error OpenAI: {e}")
        return "⚠️ Hubo un problema generando la respuesta."

    msg = response.choices[0].message

    if msg.tool_calls:
        messages.append(msg)

        for tool_call in msg.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments or "{}")

            if name == "search_web":
                result = await search_web(args.get("query", ""))
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": "search_web",
                    "content": json.dumps(result, ensure_ascii=False),
                })
            elif name == "execute_action":
                result = await execute_action(args.get("action_name", ""), args.get("details", {}))
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": "execute_action",
                    "content": result,
                })

        try:
            final = await client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                max_tokens=800,
            )
            answer = final.choices[0].message.content or "No pude generar una respuesta."
        except Exception as e:
            logger.error(f"Error OpenAI (tool follow-up): {e}")
            return "⚠️ Hubo un problema generando la respuesta."
    else:
        answer = msg.content or "No pude generar una respuesta."

    await save_chat_memory(user_id, "user", text)
    await save_chat_memory(user_id, "assistant", answer)

    asyncio.create_task(_update_user_profile(user_id, f"User: {text} | Nexora: {answer}"))
    return answer
