import httpx

from config import ACTION_WEBHOOK_URL, APP_NAME, logger
from deps import tavily


async def search_web(query: str):
    if not tavily:
        return [{"error": "Búsqueda web desactivada"}]
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
    except Exception as e:
        logger.warning(f"Error de búsqueda web: {e}")
        return [{"error": f"Error de búsqueda: {e}"}]


async def execute_action(action_name: str, details: dict):
    if not ACTION_WEBHOOK_URL:
        return "ACTION_WEBHOOK_URL no configurado."
    payload = {
        "action": action_name,
        "agent": APP_NAME,
        "data": details,
    }
    try:
        async with httpx.AsyncClient(timeout=20) as client_http:
            response = await client_http.post(ACTION_WEBHOOK_URL, json=payload)
            return f"Acción enviada. Estado: {response.status_code}"
    except Exception as e:
        return f"Error ejecutando acción: {e}"
