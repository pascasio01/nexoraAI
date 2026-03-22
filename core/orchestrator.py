import json
import logging

logger = logging.getLogger("Nexora")
_AGENT_IMPORT_ERROR = None
_AGENT_FUNCS = None


def _load_agent_dependencies():
    global _AGENT_FUNCS, _AGENT_IMPORT_ERROR
    if _AGENT_FUNCS is not None or _AGENT_IMPORT_ERROR is not None:
        return
    try:
        from agents.supervisor import supervisor_agent
        from agents.research import research_agent
        from agents.creative import creative_agent
        from agents.verify import verify_agent
        from agents.memory import memory_agent
        from core.memory_store import save_long_memory, load_long_memory

        _AGENT_FUNCS = (
            supervisor_agent,
            research_agent,
            creative_agent,
            verify_agent,
            memory_agent,
            save_long_memory,
            load_long_memory,
        )
    except Exception as exc:
        _AGENT_IMPORT_ERROR = exc


async def run_agents(user_id: str, user_text: str):
    """
    Orquesta de forma asíncrona el flujo de agentes para generar respuestas.

    Si los módulos de agentes no están disponibles en este despliegue, devuelve
    un mensaje de fallback sin elevar excepciones de importación.
    """
    _load_agent_dependencies()
    if _AGENT_IMPORT_ERROR is not None or _AGENT_FUNCS is None:
        logger.warning("Pipeline de agentes no disponible: %s", _AGENT_IMPORT_ERROR)
        return "Pipeline de agentes no disponible en esta versión de despliegue."
    (
        supervisor_agent,
        research_agent,
        creative_agent,
        verify_agent,
        memory_agent,
        save_long_memory,
        load_long_memory,
    ) = _AGENT_FUNCS

    try:
        route = await supervisor_agent(user_text)

        research_data = None
        if route == "research":
            research_data = await research_agent(user_text)

        memories = await load_long_memory(user_id)
        memory_context = f"Memorias previas: {memories}" if memories else "Sin memorias previas."
        enhanced_prompt = f"{memory_context}\n\nPregunta actual: {user_text}"

        draft = await creative_agent(enhanced_prompt, research_data)
        final = await verify_agent(draft)

        mem_decision_raw = await memory_agent(user_text)

        try:
            mem_decision = json.loads(mem_decision_raw)
            if mem_decision.get("save") and mem_decision.get("memory"):
                await save_long_memory(user_id, mem_decision["memory"])
        except Exception as exc:
            logger.warning("Error procesando decisión de memoria: %s", exc)

        return final

    except Exception as exc:
        logger.error("Error en orquestador de agentes: %s", exc)
        return f"Error procesando consulta: {exc}"
