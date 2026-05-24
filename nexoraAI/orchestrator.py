from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

from nexoraAI.agent_interface import AgentResult, AssistantAgent
from nexoraAI.calendar_agent import CalendarAgent
from nexoraAI.communication_agent import CommunicationAgent
from nexoraAI.decision_engine import AutonomyLevel, DecisionContext, DecisionEngine
from nexoraAI.device_agent import DeviceAgent
from nexoraAI.memory_agent import MemoryAgent
from nexoraAI.memory_engine import MemoryEngine
from nexoraAI.notification_agent import NotificationAgent
from nexoraAI.research_agent import ResearchAgent
from nexoraAI.security_agent import SecurityAgent
from nexoraAI.wellness_agent import WellnessAgent

logger = logging.getLogger(__name__)


@dataclass
class OrchestrationResponse:
    intent: str
    autonomy_mode: str
    should_execute: bool
    priority: int
    response: str
    agent_outputs: Dict[str, str] = field(default_factory=dict)


class Orchestrator:
    def __init__(
        self,
        memory_engine: Optional[MemoryEngine] = None,
        decision_engine: Optional[DecisionEngine] = None,
        agents: Optional[Dict[str, AssistantAgent]] = None,
    ):
        self.memory_engine = memory_engine or MemoryEngine()
        self.decision_engine = decision_engine or DecisionEngine()
        self.agents = agents or self._build_default_agents()

    def _build_default_agents(self) -> Dict[str, AssistantAgent]:
        return {
            "memory": MemoryAgent(self.memory_engine),
            "research": ResearchAgent(),
            "calendar": CalendarAgent(),
            "wellness": WellnessAgent(),
            "communication": CommunicationAgent(),
            "notification": NotificationAgent(),
            "security": SecurityAgent(),
            "device": DeviceAgent(),
        }

    def detect_intent(self, user_input: str) -> str:
        text = user_input.lower()
        intent_map = {
            "calendar": ("calendar", "meeting", "schedule", "agenda", "evento", "reunion", "reunión"),
            "wellness": ("wellness", "salud", "exercise", "sleep", "stress", "hábitos"),
            "communication": ("email", "message", "reply", "whatsapp", "telegram", "comunicar", "communicate"),
            "notification": ("notify", "remind", "alert", "recordatorio", "notificación"),
            "security": ("password", "security", "risk", "2fa", "fraud", "phishing"),
            "device": ("device", "wifi", "bluetooth", "screen", "laptop", "phone"),
            "research": ("research", "investigate", "find", "buscar", "analiza", "web"),
            "memory": ("remember", "recuerda", "profile", "prefer", "memoria"),
        }
        for intent, keywords in intent_map.items():
            if any(keyword in text for keyword in keywords):
                return intent
        return "research"

    def _select_agents(self, intent: str) -> Iterable[AssistantAgent]:
        selected: List[AssistantAgent] = []
        primary = self.agents.get(intent)
        if primary:
            selected.append(primary)
        elif self.agents.get("research"):
            selected.append(self.agents["research"])
        if intent != "memory" and self.agents.get("memory"):
            selected.insert(0, self.agents["memory"])
        return selected

    async def process(
        self,
        user_id: str,
        user_input: str,
        autonomy_level: AutonomyLevel = AutonomyLevel.LEVEL_0_SUGGEST_ONLY,
        permissions: Optional[Dict[str, bool]] = None,
        risk: int = 1,
        priority: int = 5,
        has_prior_permission: bool = False,
    ) -> OrchestrationResponse:
        intent = self.detect_intent(user_input)
        permission_map = permissions or {}
        decision = self.decision_engine.evaluate(
            requested_action=intent,
            context=DecisionContext(
                permissions=permission_map,
                autonomy_level=autonomy_level,
                risk=risk,
                priority=priority,
                has_prior_permission=has_prior_permission,
            ),
        )

        memory_context = self.memory_engine.get_memory_context(user_id)
        payload = {
            "user_id": user_id,
            "intent": intent,
            "user_input": user_input,
            "memory_context": memory_context,
            "decision": {
                "mode": decision.mode,
                "should_execute": decision.should_execute,
                "reason": decision.reason,
            },
        }

        results: List[AgentResult] = []
        for agent in self._select_agents(intent):
            try:
                results.append(await agent.run(payload))
            except Exception as exc:
                logger.exception("Agent '%s' failed: %s", getattr(agent, "name", "unknown"), exc)
                results.append(
                    AgentResult(
                        agent=agent.name,
                        output="Unavailable right now. Using graceful fallback.",
                        success=False,
                    )
                )

        combined_parts = [f"Intent detected: {intent}.", decision.reason]
        combined_parts.extend(result.output for result in results if result.output)
        combined_response = " ".join(part.strip() for part in combined_parts if part).strip()

        self.memory_engine.record_interaction(
            user_id=user_id,
            user_text=user_input,
            assistant_text=combined_response,
        )

        return OrchestrationResponse(
            intent=intent,
            autonomy_mode=decision.mode,
            should_execute=decision.should_execute,
            priority=decision.priority,
            response=combined_response,
            agent_outputs={result.agent: result.output for result in results},
        )
