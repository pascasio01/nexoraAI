from __future__ import annotations

from datetime import datetime, timezone

import httpx

from config import ACTION_WEBHOOK_URL
from deps import tavily
from memory import list_notes, list_tasks, save_note, save_task


async def search_web(query: str) -> list[dict]:
    """Search internet through Tavily when available."""
    if not tavily:
        return [{"error": "Tavily no configurado", "query": query}]
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
    except Exception as exc:
        return [{"error": f"Error de búsqueda: {exc}", "query": query}]


async def manage_notes_tasks(user_id: str, action: str, content: str = "", title: str = "") -> dict:
    """Manage user notes and tasks for personal agent automations."""
    if action == "note":
        note = {
            "title": title or "Nota",
            "content": content,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await save_note(user_id, note)
        return {"ok": True, "type": "note", "item": note}

    if action == "task":
        task = {
            "title": title or "Tarea",
            "content": content,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await save_task(user_id, task)
        return {"ok": True, "type": "task", "item": task}

    if action == "list_notes":
        return {"ok": True, "type": "notes", "items": await list_notes(user_id)}

    if action == "list_tasks":
        return {"ok": True, "type": "tasks", "items": await list_tasks(user_id)}

    return {"ok": False, "error": f"Acción no soportada: {action}"}


async def execute_webhook(action_name: str, details: dict, user_id: str, agent_id: str = "") -> dict:
    """Execute outbound webhook automation with safe fallback."""
    if not ACTION_WEBHOOK_URL:
        return {"ok": False, "error": "ACTION_WEBHOOK_URL no configurado"}

    payload = {
        "action": action_name,
        "user_id": user_id,
        "agent_id": agent_id,
        "data": details,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client_http:
            response = await client_http.post(ACTION_WEBHOOK_URL, json=payload)
        return {"ok": response.is_success, "status_code": response.status_code, "payload": payload}
    except Exception as exc:
        return {"ok": False, "error": f"Error ejecutando webhook: {exc}", "payload": payload}


async def set_reminder(user_id: str, reminder_text: str, when: str) -> dict:
    """Store reminder as a pending task."""
    return await manage_notes_tasks(
        user_id=user_id,
        action="task",
        content=f"{reminder_text} @ {when}",
        title="Recordatorio",
    )
