from datetime import datetime, timezone

import httpx

from config import ACTION_WEBHOOK_URL
import deps


async def search_web(query: str):
    if deps.tavily is None:
        return [{"error": "Web search is disabled"}]

    try:
        result = deps.tavily.search(query=query, max_results=3)
    except Exception as exc:
        return [{"error": f"Search error: {exc}"}]

    return [
        {
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "snippet": item.get("content", ""),
        }
        for item in result.get("results", [])
    ]


async def consultar_biblioteca(query: str):
    return {
        "status": "pending_index",
        "query": query,
        "message": "Private RAG memory is not indexed yet.",
    }


async def execute_action(action_name: str, details: dict, user_id: str):
    if not ACTION_WEBHOOK_URL:
        return {"ok": False, "message": "ACTION_WEBHOOK_URL not configured"}

    payload = {
        "action": action_name,
        "user_id": user_id,
        "data": details,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        async with httpx.AsyncClient(timeout=15) as http_client:
            response = await http_client.post(ACTION_WEBHOOK_URL, json=payload)
            return {"ok": response.is_success, "status_code": response.status_code}
    except Exception as exc:
        return {"ok": False, "message": str(exc)}
