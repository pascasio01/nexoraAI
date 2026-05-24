from __future__ import annotations

from nexoraAI.agent_interface import AgentResult, AssistantAgent


class CalendarAgent(AssistantAgent):
    name = "calendar_agent"

    async def run(self, payload: dict) -> AgentResult:
        mode = payload["decision"]["mode"]
        return AgentResult(
            agent=self.name,
            output=f"Calendar plan generated in mode '{mode}' for: {payload.get('user_input', '')}.",
        )

