from datetime import datetime, timezone

import httpx

from config import ACTION_WEBHOOK_URL, APP_NAME, OWNER_ID
from deps import tavily


async def search_web(query: str):
    if not tavily:
        return [{"error": "TAVILY_API_KEY no configurada"}]

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
        "resultado": "Sistema RAG listo para indexar PDFs y documentos. Búsqueda privada aún en fase inicial.",
        "query": query,
    }


async def execute_action(action_name: str, details: dict):
    if not ACTION_WEBHOOK_URL:
        return "ACTION_WEBHOOK_URL no configurado."

    try:
        async with httpx.AsyncClient(timeout=20) as client_http:
            payload = {
                "action": action_name,
                "user_id": OWNER_ID,
                "agent": APP_NAME,
                "data": {
                    **details,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            }
            res = await client_http.post(ACTION_WEBHOOK_URL, json=payload)
            return f"Acción '{action_name}' enviada. Estado: {res.status_code}"
    except Exception as exc:
        return f"Error ejecutando acción: {exc}"
