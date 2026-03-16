import json

from config import APP_NAME, CREATOR_ALIAS, CREATOR_NAME, MODEL_NAME, logger
from deps import client
from memory import check_rate_limit, load_chat_memory, save_chat_memory
from tools_impl import consultar_biblioteca, execute_action, search_web
from tools_schema import tools

SYSTEM_PROMPT = f"""
Eres {APP_NAME}, una asistente de IA creada por {CREATOR_NAME} ({CREATOR_ALIAS}).
Responde en el idioma del usuario con claridad y utilidad.
""".strip()


async def _handle_tool(tool_name: str, args: dict):
    if tool_name == "search_web":
        return await search_web(args.get("query", ""))
    if tool_name == "consultar_biblioteca":
        return await consultar_biblioteca(args.get("query", ""))
    if tool_name == "execute_action":
        return await execute_action(args.get("action_name", ""), args.get("details", {}))
    return {"error": f"Unknown tool: {tool_name}"}


async def ask_nexora(user_id: str, user_text: str) -> str:
    if not await check_rate_limit(user_id):
        return "Límite de solicitudes alcanzado. Intenta de nuevo en un minuto."

    if client is None:
        return "OpenAI no está configurado en este entorno. Configura OPENAI_API_KEY para habilitar respuestas IA."

    history = await load_chat_memory(user_id)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, *history, {"role": "user", "content": user_text}]

    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.6,
        )

        message = response.choices[0].message
        content = message.content or ""

        if getattr(message, "tool_calls", None):
            for tool_call in message.tool_calls:
                name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments or "{}")
                tool_result = await _handle_tool(name, arguments)
                content += f"\n\n[{name}] {json.dumps(tool_result, ensure_ascii=False)}"

        if not content.strip():
            content = "No pude generar una respuesta útil en este momento."

        await save_chat_memory(user_id, "user", user_text)
        await save_chat_memory(user_id, "assistant", content)
        return content
    except Exception as exc:
        logger.warning("ask_nexora fallback active: %s", exc)
        return "El servicio de IA no está disponible temporalmente. Intenta nuevamente en unos segundos."
