from __future__ import annotations

from nexoraAI.agent_interface import AgentResult, AssistantAgent


class ResearchAgent(AssistantAgent):
    name = "research_agent"

    async def run(self, payload: dict) -> AgentResult:
        question = payload.get("user_input", "")
        output = (
            "Research module prepared a fact-finding brief for: "
            f"'{question}'. If live tools are unavailable, this fallback still preserves flow."
        )
        return AgentResult(agent=self.name, output=output)

