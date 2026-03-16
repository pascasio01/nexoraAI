from __future__ import annotations

from nexoraAI.agent_interface import AgentResult, AssistantAgent


class WellnessAgent(AssistantAgent):
    name = "wellness_agent"

    async def run(self, payload: dict) -> AgentResult:
        return AgentResult(
            agent=self.name,
            output="Wellness guidance drafted with focus on sustainable routines and recovery balance.",
        )

