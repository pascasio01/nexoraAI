"""Tool implementations with per-user permissions and graceful fallbacks."""

from __future__ import annotations

from datetime import datetime, timezone

import httpx

from config import ACTION_WEBHOOK_URL
from deps import tavily_client
from memory import save_personal_item


async def search_web(query: str):
    if not tavily_client:
        return [{"error": "Tavily is not configured"}]
    try:
        result = tavily_client.search(query=query, max_results=3)
        return [
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("content", ""),
            }
            for item in result.get("results", [])
        ]
    except Exception as exc:
        return [{"error": f"Search failed: {exc}"}]


async def manage_note_task(user_id: str, kind: str, content: str):
    item = await save_personal_item(user_id=user_id, kind=kind, content=content)
    return {"ok": True, "item": item}


async def schedule_reminder(user_id: str, content: str, schedule_time: str):
    reminder = await save_personal_item(
        user_id=user_id,
        kind="reminder",
        content=f"{content} @ {schedule_time}",
    )
    return {"ok": True, "reminder": reminder}


async def execute_webhook(action_name: str, details: dict):
    if not ACTION_WEBHOOK_URL:
        return {"ok": False, "error": "ACTION_WEBHOOK_URL not configured"}

    payload = {
        "action": action_name,
        "data": details,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    try:
        async with httpx.AsyncClient(timeout=20) as client_http:
            res = await client_http.post(ACTION_WEBHOOK_URL, json=payload)
        return {"ok": res.is_success, "status_code": res.status_code}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
