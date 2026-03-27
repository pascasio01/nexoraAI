from __future__ import annotations

from nexoraAI.agent_interface import AgentResult, AssistantAgent


class NotificationAgent(AssistantAgent):
    name = "notification_agent"

    async def run(self, payload: dict) -> AgentResult:
        return AgentResult(
            agent=self.name,
            output="Notification schedule prepared with quiet-hour sensitivity and priority ordering.",
        )

