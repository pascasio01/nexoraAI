import asyncio
import json
import logging

from agents.creative import creative_agent
from agents.memory import memory_agent
from agents.research import research_agent
from agents.supervisor import supervisor_agent
from agents.verify import verify_agent
from core.memory_store import load_long_memory, save_long_memory

logger = logging.getLogger("Nexora")


async def run_agents_async(user_id: str, user_text: str):
    """Orquesta el flujo de agentes para generar respuestas contextuales."""
    try:
        route = await supervisor_agent(user_text)
        research_data = await research_agent(user_text) if route == "research" else None

        memories = await load_long_memory(user_id)
        memory_context = f"Memorias previas: {memories}" if memories else "Sin memorias previas."
        draft = await creative_agent(f"{memory_context}\n\nPregunta actual: {user_text}", research_data)
        final = await verify_agent(draft)

        mem_decision_raw = await memory_agent(user_text)
        try:
            mem_decision = json.loads(mem_decision_raw)
            if mem_decision.get("save") and mem_decision.get("memory"):
                await save_long_memory(user_id, mem_decision["memory"])
        except Exception as e:
            logger.warning(f"Error procesando decisión de memoria: {e}")

        return final
    except Exception as e:
        logger.error(f"Error en orquestador de agentes: {e}")
        return f"Error procesando consulta: {e}"


def run_agents(user_id: str, user_text: str):
    """
    Compatibilidad con llamadas síncronas existentes.
    """
    return asyncio.run(run_agents_async(user_id, user_text))
