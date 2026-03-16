from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Protocol


AgentHandler = Callable[[str, Dict[str, Any]], str]
ToolHandler = Callable[[Dict[str, Any]], Any]
ChannelSender = Callable[[str, str], Any]
AutomationAction = Callable[[Dict[str, Any]], Any]


class Plugin(Protocol):
    name: str

    def setup(self, orchestrator: "Orchestrator") -> None:
        ...


@dataclass(frozen=True)
class AutomationRule:
    trigger: str
    action: AutomationAction


class Orchestrator:
    """
    Minimal modular foundation for the NexoraAI AI Operating System.

    This MVP supports personal agents, long-term memory, tools, automations,
    multi-channel communication, and a plugin extension point.
    """

    def __init__(self):
        self._agents: Dict[str, AgentHandler] = {}
        self._personal_agents: Dict[str, str] = {}
        self._memory: Dict[str, List[str]] = {}
        self._tools: Dict[str, ToolHandler] = {}
        self._automations: List[AutomationRule] = []
        self._channels: Dict[str, ChannelSender] = {}
        self._plugins: Dict[str, Plugin] = {}

    # Agents
    def register_agent(self, name: str, handler: AgentHandler) -> None:
        self._agents[name] = handler

    def set_personal_agent(self, user_id: str, agent_name: str) -> None:
        if agent_name not in self._agents:
            raise ValueError(f"Agent '{agent_name}' is not registered")
        self._personal_agents[user_id] = agent_name

    def run_personal_agent(self, user_id: str, user_text: str) -> str:
        agent_name = self._personal_agents.get(user_id)
        if not agent_name:
            raise ValueError(f"No personal agent configured for user '{user_id}'")
        history = self.recall(user_id)
        context = {"user_id": user_id, "history": history}
        response = self._agents[agent_name](user_text, context)
        self.remember(user_id, f"user:{user_text}")
        self.remember(user_id, f"assistant:{response}")
        self.trigger_automation("message_processed", {"user_id": user_id, "text": user_text})
        return response

    # Memory
    def remember(self, user_id: str, item: str) -> None:
        self._memory.setdefault(user_id, []).append(item)

    def recall(self, user_id: str, limit: Optional[int] = None) -> List[str]:
        memories = self._memory.get(user_id, [])
        if limit is None:
            return list(memories)
        if limit <= 0:
            return []
        return memories[-limit:]

    # Tools
    def register_tool(self, name: str, handler: ToolHandler) -> None:
        self._tools[name] = handler

    def execute_tool(self, name: str, payload: Optional[Dict[str, Any]] = None) -> Any:
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' is not registered")
        return self._tools[name](payload or {})

    # Automation
    def register_automation(self, trigger: str, action: AutomationAction) -> None:
        self._automations.append(AutomationRule(trigger=trigger, action=action))

    def trigger_automation(self, trigger: str, payload: Optional[Dict[str, Any]] = None) -> None:
        event_payload = payload or {}
        for rule in self._automations:
            if rule.trigger == trigger:
                rule.action(event_payload)

    # Multi-channel communication
    def register_channel(self, name: str, sender: ChannelSender) -> None:
        self._channels[name] = sender

    def send_message(self, channel: str, user_id: str, message: str) -> Any:
        if channel not in self._channels:
            raise ValueError(f"Channel '{channel}' is not registered")
        return self._channels[channel](user_id, message)

    # Plugins
    def register_plugin(self, plugin: Plugin) -> None:
        if plugin.name in self._plugins:
            raise ValueError(f"Plugin '{plugin.name}' is already registered")
        plugin.setup(self)
        self._plugins[plugin.name] = plugin

    def registered_plugins(self) -> List[str]:
        return sorted(self._plugins.keys())
