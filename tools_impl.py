from __future__ import annotations

from datetime import datetime, timezone

import httpx

from config import ACTION_WEBHOOK_URL, APP_NAME, OWNER_ID
import deps
from memory import load_long_memory, save_long_memory


async def web_search(query: str) -> list[dict]:
    if not deps.tavily:
        return [{"error": "Web search is not configured."}]

    try:
        result = deps.tavily.search(query=query, max_results=3)
    except Exception as exc:
        return [{"error": f"Web search failed: {exc}"}]

    return [
        {
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "snippet": item.get("content", ""),
        }
        for item in result.get("results", [])
    ]


async def notes_tasks(user_id: str, operation: str, content: str = ""):
    if operation == "add":
        await save_long_memory(user_id, content)
        return {"status": "saved"}

    if operation == "list":
        memories = await load_long_memory(user_id, limit=10)
        return {"items": memories}

    return {"error": "Unsupported operation."}


async def webhook_action(action_name: str, details: dict | None = None):
    if not ACTION_WEBHOOK_URL:
        return {"error": "Webhook is not configured."}

    payload = {
        "action": action_name,
        "user_id": OWNER_ID,
        "agent": APP_NAME,
        "data": {**(details or {}), "generated_timestamp": datetime.now(timezone.utc).isoformat()},
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client_http:
            response = await client_http.post(ACTION_WEBHOOK_URL, json=payload)
        return {"status_code": response.status_code, "ok": response.is_success}
    except Exception as exc:
        return {"error": f"Webhook execution failed: {exc}"}
