import json
import logging

logger = logging.getLogger("Nexora")

async def run_agents(user_id: str, user_text: str):
    """Orquesta en modo async el flujo de agentes para generar respuestas contextuales."""
    try:
        from agents.supervisor import supervisor_agent
        from agents.research import research_agent
        from agents.creative import creative_agent
        from agents.verify import verify_agent
        from agents.memory import memory_agent
        from core.memory_store import save_long_memory, load_long_memory

        # 1. Supervisor decide si necesita investigación
        route = await supervisor_agent(user_text)
        
        research_data = None
        if route == "research":
            research_data = await research_agent(user_text)
        
        # 2. Cargar memoria a largo plazo del usuario
        memories = await load_long_memory(user_id)
        
        # 3. Creative agent genera respuesta considerando memoria
        memory_context = f"Memorias previas: {memories}" if memories else "Sin memorias previas."
        enhanced_prompt = f"{memory_context}\n\nPregunta actual: {user_text}"
        
        draft = await creative_agent(enhanced_prompt, research_data)
        
        # 4. Verify agent mejora la respuesta
        final = await verify_agent(draft)
        
        # 5. Memory agent decide qué guardar
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
