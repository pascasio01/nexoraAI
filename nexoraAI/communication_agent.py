from __future__ import annotations

from nexoraAI.agent_interface import AgentResult, AssistantAgent


class CommunicationAgent(AssistantAgent):
    name = "communication_agent"

    async def run(self, payload: dict) -> AgentResult:
        return AgentResult(
            agent=self.name,
            output="Communication draft prepared with clear tone, structure, and user context awareness.",
        )

