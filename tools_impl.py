"""Default tool implementations."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from config import ACTION_WEBHOOK_URL
from memory import MemoryStore
from tools_schema import ToolRegistry, function_tool


async def _search_web(user_id: str, args: dict[str, Any], tavily_client: Any | None) -> str:
    query = args.get("query", "")
    if not query:
        return "Falta query para buscar en web."
    if not tavily_client:
        return "Búsqueda web no disponible: TAVILY_API_KEY no configurada."
    try:
        result = tavily_client.search(query=query, max_results=3)
        items = result.get("results", [])
        if not items:
            return "No encontré resultados."
        return "\n".join(f"- {item.get('title','Sin título')}: {item.get('url','')}" for item in items)
    except Exception as exc:
        return f"Error en búsqueda web: {exc}"


async def _create_note(user_id: str, args: dict[str, Any], memory: MemoryStore) -> str:
    note = {
        "title": args.get("title", "Nota"),
        "content": args.get("content", ""),
        "created_at": datetime.utcnow().isoformat(),
    }
    await memory.add_note(user_id, note)
    return f"Nota guardada: {note['title']}"


async def _list_notes(user_id: str, args: dict[str, Any], memory: MemoryStore) -> str:
    notes = await memory.list_notes(user_id)
    if not notes:
        return "No hay notas guardadas."
    return "\n".join(f"- {n.get('title', 'Nota')}: {n.get('content', '')}" for n in notes[-10:])


async def _execute_webhook(user_id: str, args: dict[str, Any]) -> str:
    if not ACTION_WEBHOOK_URL:
        return "Webhook automation no disponible: ACTION_WEBHOOK_URL no configurada."

    payload = {
        "user_id": user_id,
        "action": args.get("action", "custom"),
        "data": args.get("data", {}),
        "timestamp": datetime.utcnow().isoformat(),
    }
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(ACTION_WEBHOOK_URL, json=payload)
        return f"Webhook ejecutado con estado {response.status_code}."
    except Exception as exc:
        return f"Error ejecutando webhook: {exc}"


async def _set_reminder(user_id: str, args: dict[str, Any], memory: MemoryStore) -> str:
    content = args.get("content", "")
    schedule_time = args.get("schedule_time", "sin fecha")
    note = {
        "title": f"Reminder ({schedule_time})",
        "content": content,
        "created_at": datetime.utcnow().isoformat(),
    }
    await memory.add_note(user_id, note)
    return f"Recordatorio creado para {schedule_time}."


def register_default_tools(registry: ToolRegistry, memory: MemoryStore, tavily_client: Any | None) -> None:
    """Register built-in tools and keep plugin entrypoint open."""

    registry.register(
        name="search_web",
        schema=function_tool(
            "search_web",
            "Busca información actualizada en internet.",
            {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        ),
        handler=lambda user_id, args: _search_web(user_id, args, tavily_client),
    )

    registry.register(
        name="create_note",
        schema=function_tool(
            "create_note",
            "Guarda una nota persistente del usuario.",
            {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["content"],
            },
        ),
        handler=lambda user_id, args: _create_note(user_id, args, memory),
    )

    registry.register(
        name="list_notes",
        schema=function_tool(
            "list_notes",
            "Lista notas del usuario.",
            {"type": "object", "properties": {}, "required": []},
        ),
        handler=lambda user_id, args: _list_notes(user_id, args, memory),
    )

    registry.register(
        name="set_reminder",
        schema=function_tool(
            "set_reminder",
            "Crea un recordatorio para el usuario.",
            {
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "schedule_time": {"type": "string"},
                },
                "required": ["content"],
            },
        ),
        handler=lambda user_id, args: _set_reminder(user_id, args, memory),
    )

    registry.register(
        name="execute_webhook",
        schema=function_tool(
            "execute_webhook",
            "Dispara automatizaciones vía webhook.",
            {
                "type": "object",
                "properties": {
                    "action": {"type": "string"},
                    "data": {"type": "object"},
                },
                "required": ["action"],
            },
        ),
        handler=lambda user_id, args: _execute_webhook(user_id, args),
    )
