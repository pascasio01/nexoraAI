class BaseAgent:
    name = "base"

    def run(self, message: str) -> str:
        return ""


class MemoryAgent(BaseAgent):
    name = "memory"


class CalendarAgent(BaseAgent):
    name = "calendar"


class FinanceAgent(BaseAgent):
    name = "finance"


class WellnessAgent(BaseAgent):
    name = "wellness"


class ResearchAgent(BaseAgent):
    name = "research"


class SecurityAgent(BaseAgent):
    name = "security"


class DeviceAgent(BaseAgent):
    name = "device"


class CommunicationAgent(BaseAgent):
    name = "communication"


class NotificationAgent(BaseAgent):
    name = "notification"
