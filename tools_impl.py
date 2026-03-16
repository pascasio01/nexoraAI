from __future__ import annotations

from datetime import datetime, timezone

import httpx

from config import logger, settings
from deps import get_tavily_client
from memory import add_personal_memory, add_task, list_tasks


async def save_note(user_id: str, assistant_id: str, content: str, category: str = "general") -> dict:
    return await add_personal_memory(
        user_id=user_id,
        assistant_id=assistant_id,
        kind=f"note:{category}",
        content=content,
    )


async def create_task(
    user_id: str,
    assistant_id: str,
    title: str,
    priority: str = "medium",
    due_at: str | None = None,
) -> dict:
    return await add_task(
        user_id=user_id,
        assistant_id=assistant_id,
        task={
            "title": title,
            "priority": priority,
            "due_at": due_at,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )


async def web_search(query: str) -> dict:
    tavily = get_tavily_client()
    if tavily is None:
        return {
            "status": "disabled",
            "message": "La búsqueda web está desactivada (falta TAVILY_API_KEY).",
            "results": [],
        }

    try:
        result = tavily.search(query=query, max_results=3)
        return {
            "status": "ok",
            "results": [
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("content", ""),
                }
                for item in result.get("results", [])
            ],
        }
    except Exception as exc:
        logger.warning("Error en web_search: %s", exc)
        return {"status": "error", "message": f"No se pudo buscar en web: {exc}", "results": []}


async def webhook_action(action: str, payload: dict | None = None) -> dict:
    if not settings.action_webhook_url:
        return {
            "status": "disabled",
            "message": "Acciones por webhook desactivadas (falta ACTION_WEBHOOK_URL).",
        }

    try:
        body = {
            "action": action,
            "payload": payload or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        async with httpx.AsyncClient(timeout=20) as client_http:
            response = await client_http.post(settings.action_webhook_url, json=body)
        return {"status": "ok", "status_code": response.status_code}
    except Exception as exc:
        logger.warning("Error enviando webhook_action: %s", exc)
        return {"status": "error", "message": f"No se pudo ejecutar webhook: {exc}"}


async def execute_tool_call(tool_name: str, arguments: dict, user_id: str, assistant_id: str) -> dict:
    if tool_name == "save_note":
        return await save_note(
            user_id=user_id,
            assistant_id=assistant_id,
            content=str(arguments.get("content", "")).strip(),
            category=str(arguments.get("category", "general")),
        )
    if tool_name == "create_task":
        return await create_task(
            user_id=user_id,
            assistant_id=assistant_id,
            title=str(arguments.get("title", "")).strip(),
            priority=str(arguments.get("priority", "medium")),
            due_at=arguments.get("due_at"),
        )
    if tool_name == "list_tasks":
        return {"status": "ok", "tasks": await list_tasks(user_id=user_id, assistant_id=assistant_id)}
    if tool_name == "web_search":
        return await web_search(query=str(arguments.get("query", "")).strip())
    if tool_name == "webhook_action":
        return await webhook_action(
            action=str(arguments.get("action", "")).strip(),
            payload=arguments.get("payload", {}),
        )

    return {"status": "error", "message": f"Herramienta no soportada: {tool_name}"}
