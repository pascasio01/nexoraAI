from __future__ import annotations

from nexoraAI.agent_interface import AgentResult, AssistantAgent


class DeviceAgent(AssistantAgent):
    name = "device_agent"

    async def run(self, payload: dict) -> AgentResult:
        return AgentResult(
            agent=self.name,
            output="Device diagnostics plan prepared with conservative, reversible actions only.",
        )
