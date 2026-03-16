from dataclasses import dataclass


@dataclass(slots=True)
class Decision:
    autonomy_level: int
    risk_score: int
    reason: str
    action: str


class DecisionEngine:
    SENSITIVE_KEYWORDS = ("transfer", "password", "delete", "borrar")
    ACTION_KEYWORDS = ("recordar", "remember", "task", "tarea")

    def evaluate(self, message: str) -> Decision:
        lowered = message.lower()
        if any(keyword in lowered for keyword in self.SENSITIVE_KEYWORDS):
            return Decision(autonomy_level=0, risk_score=9, reason="Acción sensible detectada.", action="suggest_only")
        if any(keyword in lowered for keyword in self.ACTION_KEYWORDS):
            return Decision(autonomy_level=1, risk_score=3, reason="Se requiere confirmación para crear acciones.", action="prepare_confirmation")
        return Decision(autonomy_level=2, risk_score=1, reason="Conversación informativa de bajo riesgo.", action="respond")
