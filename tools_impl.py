from datetime import datetime, timezone

import httpx

from config import ACTION_WEBHOOK_URL, APP_NAME, OWNER_ID, logger
from deps import tavily


async def search_web(query: str) -> list[dict]:
    if tavily is None:
        return [{"error": "Web search is disabled: TAVILY_API_KEY is missing."}]

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
        logger.warning("Web search failed: %s", exc)
        return [{"error": "Web search is temporarily unavailable."}]


async def consultar_biblioteca(query: str) -> dict:
    return {
        "resultado": "Módulo de biblioteca privada preparado para futura indexación multi-tenant.",
        "query": query,
    }


async def execute_action(action_name: str, details: dict) -> str:
    if not ACTION_WEBHOOK_URL:
        return "Action webhook is disabled: ACTION_WEBHOOK_URL is missing."

    payload = {
        "action": action_name,
        "user_id": OWNER_ID,
        "agent": APP_NAME,
        "data": {**details, "timestamp": datetime.now(timezone.utc).isoformat()},
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client_http:
            response = await client_http.post(ACTION_WEBHOOK_URL, json=payload)
            return f"Action '{action_name}' sent. Status: {response.status_code}"
    except Exception as exc:
        logger.warning("Action webhook failed: %s", exc)
        return "Action webhook is temporarily unavailable."
