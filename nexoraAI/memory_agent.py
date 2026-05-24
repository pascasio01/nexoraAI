from __future__ import annotations

from nexoraAI.agent_interface import AgentResult, AssistantAgent
from nexoraAI.memory_engine import MemoryEngine


class MemoryAgent(AssistantAgent):
    name = "memory_agent"

    def __init__(self, memory_engine: MemoryEngine):
        self.memory_engine = memory_engine

    async def run(self, payload: dict) -> AgentResult:
        context = self.memory_engine.get_memory_context(payload["user_id"])
        knowledge = context.get("knowledge", {})
        summary = (
            "Memory context loaded with "
            f"{len(context.get('short_term', []))} short-term items and "
            f"{context.get('mid_term_count', 0)} mid-term items. "
            f"Known preferences: {knowledge.get('preferences', []) or 'none'}."
        )
        return AgentResult(agent=self.name, output=summary, metadata=context)
