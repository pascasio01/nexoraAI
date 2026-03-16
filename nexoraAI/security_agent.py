from __future__ import annotations

from nexoraAI.agent_interface import AgentResult, AssistantAgent


class SecurityAgent(AssistantAgent):
    name = "security_agent"

    async def run(self, payload: dict) -> AgentResult:
        decision = payload.get("decision", {})
        return AgentResult(
            agent=self.name,
            output=(
                "Security evaluation complete. "
                f"Execution={decision.get('should_execute', False)}, mode={decision.get('mode', 'unknown')}."
            ),
        )

