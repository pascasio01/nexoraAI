from nexoraAI.personal_intelligence import (
    AutonomyLevel,
    PersonalIntelligenceOrchestrator,
    build_personal_intelligence_layer,
)
from typing import Any, Dict, List, Optional


class Orchestrator:
    def __init__(self) -> None:
        self._runtime: PersonalIntelligenceOrchestrator = build_personal_intelligence_layer()
        self._running = False

    def start(self) -> None:
        self._running = True

    def stop(self) -> None:
        self._running = False

    def handle(
        self,
        user_id: str,
        text: str,
        channel: str = "web",
        device_id: str = "default-device",
        permissions: Optional[List[str]] = None,
        autonomy_level: AutonomyLevel = AutonomyLevel.LEVEL_0_SUGGEST_ONLY,
    ) -> Dict[str, Any]:
        if not self._running:
            self.start()
        return self._runtime.handle_input(
            user_id=user_id,
            user_text=text,
            channel=channel,
            device_id=device_id,
            permissions=permissions,
            autonomy_level=autonomy_level,
        )
