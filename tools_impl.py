from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Dict, List

import httpx

from config import ACTION_WEBHOOK_URL, APP_NAME, OWNER_ID
from deps import get_tavily


async def search_web(query: str) -> List[Dict[str, str]]:
    tavily = get_tavily()
    if tavily is None:
        return [{"error": "TAVILY_API_KEY is not configured"}]

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
        return [{"error": f"Web search unavailable: {exc}"}]


async def manage_note(title: str = "", content: str = "") -> Dict[str, str]:
    safe_title = title.strip() or "Untitled"
    safe_content = content.strip()
    return {
        "status": "stored-locally",
        "title": safe_title,
        "content": safe_content,
        "note": "Notes/tasks backend can be connected later without changing tool contracts.",
    }


async def execute_action(action_name: str, details: Dict[str, Any]) -> str:
    if not ACTION_WEBHOOK_URL:
        return "ACTION_WEBHOOK_URL is not configured."

    payload = {
        "action": action_name,
        "agent": APP_NAME,
        "user_id": OWNER_ID,
        "timestamp": datetime.now(UTC).isoformat(),
        "data": details,
    }

    try:
        async with httpx.AsyncClient(timeout=20) as http_client:
            response = await http_client.post(ACTION_WEBHOOK_URL, json=payload)
        return f"Action '{action_name}' sent. Status: {response.status_code}"
    except Exception as exc:
        return f"Action dispatch failed: {exc}"
