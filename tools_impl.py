from __future__ import annotations

from datetime import datetime, timezone

import httpx

from config import ACTION_WEBHOOK_URL, APP_NAME, OWNER_ID
from deps import tavily


async def search_web(query: str):
    if not tavily:
        return [{"error": "Búsqueda web no configurada"}]
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
        return [{"error": f"Error de búsqueda: {exc}"}]


async def consultar_biblioteca(query: str):
    return {
        "resultado": "Módulo de biblioteca listo para indexación futura (RAG).",
        "query": query,
    }


async def execute_action(action_name: str, details: dict):
    if not ACTION_WEBHOOK_URL:
        return "ACTION_WEBHOOK_URL no configurado."

    payload = {
        "action": action_name,
        "user_id": OWNER_ID,
        "agent": APP_NAME,
        "data": {**details, "timestamp": datetime.now(timezone.utc).isoformat()},
    }
    try:
        async with httpx.AsyncClient(timeout=20) as client_http:
            res = await client_http.post(ACTION_WEBHOOK_URL, json=payload)
            return f"Acción '{action_name}' enviada. Estado: {res.status_code}"
    except Exception as exc:
        return f"Error ejecutando acción: {exc}"
