from services.decision_engine.engine import DecisionEngine
from services.memory_engine.service import MemoryEngine

from .agents import (
    CalendarAgent,
    CommunicationAgent,
    DeviceAgent,
    FinanceAgent,
    MemoryAgent,
    NotificationAgent,
    ResearchAgent,
    SecurityAgent,
    WellnessAgent,
)


class Orchestrator:
    def __init__(self) -> None:
        self.decision_engine = DecisionEngine()
        self.memory_engine = MemoryEngine()
        self.agents = {
            "memory": MemoryAgent(),
            "calendar": CalendarAgent(),
            "finance": FinanceAgent(),
            "wellness": WellnessAgent(),
            "research": ResearchAgent(),
            "security": SecurityAgent(),
            "device": DeviceAgent(),
            "communication": CommunicationAgent(),
            "notification": NotificationAgent(),
        }

    def respond(self, message: str) -> tuple[str, dict]:
        decision = self.decision_engine.evaluate(message)
        candidate = self.memory_engine.extract(message)

        if decision.autonomy_level == 0:
            text = "Detecté una acción sensible. Te doy una recomendación y espero tu confirmación explícita."
        elif decision.autonomy_level == 1:
            text = "Puedo preparar esa acción. ¿Confirmas que la ejecute?"
        else:
            text = f"Entendido. Aquí va una respuesta inicial de NEXORA OMNI: {message}"

        meta = {
            "autonomy_level": decision.autonomy_level,
            "risk_score": decision.risk_score,
            "reason": decision.reason,
            "action": decision.action,
            "memory_candidate": candidate,
        }
        return text, meta
