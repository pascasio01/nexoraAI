from __future__ import annotations

import json
from typing import Any

from config import APP_NAME, CREATOR_ALIAS, CREATOR_NAME, MODEL_NAME, logger
from deps import client
from memory import (
    check_rate_limit,
    get_agent_events,
    get_agent_settings,
    get_or_create_agent,
    get_profile,
    get_summary,
    load_chat_memory,
    save_agent_event,
    save_agent,
    save_chat_memory,
    set_profile,
    set_summary,
)
from models import AgentEvent, AgentRecord
from tools_impl import execute_webhook, manage_notes_tasks, search_web, set_reminder

SYSTEM_PROMPT = f"""
Eres {APP_NAME}, asistente de IA personal creada por {CREATOR_NAME} ({CREATOR_ALIAS}).
Reglas:
- Responde en el idioma del usuario.
- Prioriza datos del perfil y memoria del usuario.
- Si una integración opcional no está disponible, dilo claramente.
- Estructura las respuestas para facilitar coordinación entre agentes.
""".strip()
PROFILE_SEED_CHARS = 120


async def _update_profile_and_summary(user_id: str, user_text: str, answer: str) -> None:
    """Maintain lightweight profile and summary memory without strict model dependency."""
    profile = await get_profile(user_id)
    if profile == "Usuario nuevo.":
        await set_profile(user_id, f"Initial preference seed: {user_text[:PROFILE_SEED_CHARS]}")
    summary = await get_summary(user_id)
    merged = f"{summary}\n- U: {user_text[:140]}\n- A: {answer[:140]}".strip()
    await set_summary(user_id, merged[-1000:])


async def ask_nexora(user_id: str, text: str, channel: str) -> str:
    """Main AI orchestration entrypoint shared by all channels."""
    agent = await get_or_create_agent(user_id)
    if not await check_rate_limit(user_id):
        return "⚠️ Límite de mensajes alcanzado. Espera un minuto."

    history = await load_chat_memory(user_id)
    profile = await get_profile(user_id)
    summary = await get_summary(user_id)
    settings = await get_agent_settings(user_id)

    system = (
        f"{SYSTEM_PROMPT}\n"
        f"Agent ID: {agent.agent_id}\n"
        f"Canal: {channel}\n"
        f"Perfil: {profile}\n"
        f"Resumen: {summary}\n"
        f"Capacidades: {json.dumps(agent.metadata, ensure_ascii=False)}"
    )
    if settings.system_prompt_suffix:
        system = f"{system}\n{settings.system_prompt_suffix}"

    messages = [{"role": "system", "content": system}] + history + [{"role": "user", "content": text}]

    await save_chat_memory(user_id, "user", text)

    if client is None:
        answer = (
            f"Modo local activo (OpenAI no configurado).\n"
            f"Tu agente personal {agent.agent_id} recibió: {text}\n"
            f"Canal: {channel}. Puedes usar /tools/execute para acciones."
        )
        await save_chat_memory(user_id, "assistant", answer)
        await _update_profile_and_summary(user_id, text, answer)
        return answer

    try:
        completion = await client.chat.completions.create(
            model=settings.model_name or MODEL_NAME,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            messages=messages,
        )
        answer = completion.choices[0].message.content or ""
    except Exception as exc:
        logger.warning("OpenAI unavailable, using fallback response: %s", exc)
        answer = "No pude consultar el modelo en este momento, pero tu agente sigue activo."

    await save_chat_memory(user_id, "assistant", answer)
    await _update_profile_and_summary(user_id, text, answer)
    return answer


async def execute_tool_for_agent(user_id: str, tool_name: str, args: dict[str, Any]) -> dict:
    """Execute allowed tools on behalf of a user's personal agent."""
    agent = await get_or_create_agent(user_id)
    if tool_name not in agent.tools_allowed:
        return {"ok": False, "error": f"Tool '{tool_name}' no permitido para {agent.agent_id}"}

    if tool_name == "search_web":
        return {"ok": True, "results": await search_web(args.get("query", ""))}
    if tool_name == "manage_notes_tasks":
        result = await manage_notes_tasks(
            user_id=user_id,
            action=args.get("action", ""),
            content=args.get("content", ""),
            title=args.get("title", ""),
        )
        return result
    if tool_name == "execute_webhook":
        return await execute_webhook(
            action_name=args.get("action_name", "custom_action"),
            details=args.get("details", {}),
            user_id=user_id,
            agent_id=agent.agent_id,
        )
    if tool_name == "set_reminder":
        return await set_reminder(
            user_id=user_id,
            reminder_text=args.get("reminder_text", ""),
            when=args.get("when", ""),
        )

    return {"ok": False, "error": f"Tool no implementado: {tool_name}"}


async def send_agent_event(from_user_id: str, to_agent_id: str, event_type: str, payload: dict[str, Any]) -> AgentEvent:
    """Send structured JSON event from one personal agent to another."""
    from_agent: AgentRecord = await get_or_create_agent(from_user_id)
    event = AgentEvent(
        from_agent_id=from_agent.agent_id,
        to_agent_id=to_agent_id,
        event_type=event_type,
        payload=payload,
    )
    await save_agent_event(event)
    return event


async def read_agent_inbox(agent_id: str) -> list[AgentEvent]:
    """Read recent events for an agent."""
    return await get_agent_events(agent_id)


async def configure_agent_permissions(user_id: str, tools_allowed: list[str], permissions: dict[str, bool]) -> AgentRecord:
    """Update per-user agent tool and permission policy."""
    agent = await get_or_create_agent(user_id)
    agent.tools_allowed = tools_allowed
    agent.permissions = permissions
    await save_agent(agent)
    return agent
