import json
import logging

logger = logging.getLogger("Nexora")


async def run_agents(user_id: str, user_text: str):
    """Placeholder async orchestrator for future multi-agent expansion."""
    try:
        return json.dumps({"user_id": user_id, "response": user_text})
    except Exception as exc:
        logger.error(f"Orchestrator error: {exc}")
        return f"Error procesando consulta: {exc}"
