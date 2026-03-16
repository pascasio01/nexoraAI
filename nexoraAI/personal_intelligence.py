from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, IntEnum
from typing import Any, Callable, Dict, List, Optional


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MemoryTier(str, Enum):
    SHORT = "short_term"
    MID = "mid_term"
    LONG = "long_term"


class AssistantState(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    RESPONDING = "responding"


class AutonomyLevel(IntEnum):
    LEVEL_0_SUGGEST_ONLY = 0
    LEVEL_1_PREPARE_CONFIRM = 1
    LEVEL_2_EXECUTE_AUTHORIZED = 2
    LEVEL_3_EXECUTE_AUTOMATIC = 3


@dataclass
class MemoryRecord:
    key: str
    value: str
    tier: MemoryTier = MemoryTier.SHORT
    importance: float = 0.5
    privacy: str = "private"
    tags: List[str] = field(default_factory=list)
    updated_at: str = field(default_factory=_utc_now)


class LifeMemoryEngine:
    def __init__(self) -> None:
        self._store: Dict[str, Dict[MemoryTier, Dict[str, MemoryRecord]]] = {}

    def _ensure_user(self, user_id: str) -> Dict[MemoryTier, Dict[str, MemoryRecord]]:
        if user_id not in self._store:
            self._store[user_id] = {
                MemoryTier.SHORT: {},
                MemoryTier.MID: {},
                MemoryTier.LONG: {},
            }
        return self._store[user_id]

    def upsert(self, user_id: str, record: MemoryRecord) -> MemoryRecord:
        user_mem = self._ensure_user(user_id)
        record.updated_at = _utc_now()
        user_mem[record.tier][record.key] = record
        return record

    def edit(self, user_id: str, tier: MemoryTier, key: str, value: str) -> Optional[MemoryRecord]:
        record = self._ensure_user(user_id)[tier].get(key)
        if not record:
            return None
        record.value = value
        record.updated_at = _utc_now()
        return record

    def delete(self, user_id: str, tier: MemoryTier, key: str) -> bool:
        user_mem = self._ensure_user(user_id)[tier]
        if key not in user_mem:
            return False
        del user_mem[key]
        return True

    def set_privacy(self, user_id: str, tier: MemoryTier, key: str, privacy: str) -> Optional[MemoryRecord]:
        record = self._ensure_user(user_id)[tier].get(key)
        if not record:
            return None
        record.privacy = privacy
        record.updated_at = _utc_now()
        return record

    def get(
        self,
        user_id: str,
        tier: Optional[MemoryTier] = None,
        include_private: bool = False,
    ) -> List[MemoryRecord]:
        user_mem = self._ensure_user(user_id)
        tiers = [tier] if tier else [MemoryTier.SHORT, MemoryTier.MID, MemoryTier.LONG]
        records: List[MemoryRecord] = []
        for current_tier in tiers:
            for record in user_mem[current_tier].values():
                if include_private or record.privacy != "private":
                    records.append(record)
        return sorted(records, key=lambda r: r.importance, reverse=True)

    def summarize(self, user_id: str, top_n: int = 5, include_private: bool = False) -> Dict[str, List[str]]:
        summary: Dict[str, List[str]] = {
            MemoryTier.SHORT.value: [],
            MemoryTier.MID.value: [],
            MemoryTier.LONG.value: [],
        }
        for tier in (MemoryTier.SHORT, MemoryTier.MID, MemoryTier.LONG):
            tier_records = self.get(user_id, tier=tier, include_private=include_private)[:top_n]
            summary[tier.value] = [f"{r.key}: {r.value}" for r in tier_records]
        return summary


@dataclass
class DecisionContext:
    user_id: str
    intent: str
    risk_score: float
    permissions: List[str]
    autonomy_level: AutonomyLevel
    priority: int = 1


@dataclass
class DecisionLogEntry:
    timestamp: str
    user_id: str
    intent: str
    autonomy_level: int
    mode: str
    reasoning: str


class DecisionEngine:
    def __init__(self) -> None:
        self.logs: List[DecisionLogEntry] = []

    def evaluate(self, context: DecisionContext) -> Dict[str, Any]:
        high_risk = context.risk_score >= 0.7
        if context.autonomy_level == AutonomyLevel.LEVEL_0_SUGGEST_ONLY:
            mode = "suggest"
            requires_confirmation = False
        elif context.autonomy_level == AutonomyLevel.LEVEL_1_PREPARE_CONFIRM:
            mode = "prepare"
            requires_confirmation = True
        elif context.autonomy_level == AutonomyLevel.LEVEL_2_EXECUTE_AUTHORIZED:
            mode = "prepare" if high_risk else "execute_authorized"
            requires_confirmation = high_risk
        else:
            mode = "prepare" if high_risk else "execute_automatic"
            requires_confirmation = high_risk

        reasoning = (
            f"Intent={context.intent}; risk={context.risk_score:.2f}; "
            f"autonomy={int(context.autonomy_level)}; mode={mode}"
        )
        self.logs.append(
            DecisionLogEntry(
                timestamp=_utc_now(),
                user_id=context.user_id,
                intent=context.intent,
                autonomy_level=int(context.autonomy_level),
                mode=mode,
                reasoning=reasoning,
            )
        )
        return {
            "mode": mode,
            "requires_confirmation": requires_confirmation,
            "reasoning": reasoning,
        }

    def explain_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        return [entry.__dict__ for entry in self.logs[-limit:]]


@dataclass
class AgentResult:
    agent: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class DomainAgent:
    def __init__(self, name: str) -> None:
        self.name = name

    def handle(self, user_text: str, context: Dict[str, Any]) -> AgentResult:
        return AgentResult(
            agent=self.name,
            content=f"{self.name} agent processed request: {user_text}",
            metadata={"context_keys": sorted(context.keys())},
        )


class MultiAgentSystem:
    def __init__(self) -> None:
        self._agents: Dict[str, DomainAgent] = {}

    def register(self, agent: DomainAgent) -> None:
        self._agents[agent.name] = agent

    def invoke(self, name: str, user_text: str, context: Dict[str, Any]) -> AgentResult:
        if name not in self._agents:
            raise KeyError(f"Agent '{name}' not registered")
        return self._agents[name].handle(user_text, context)

    def list_agents(self) -> List[str]:
        return sorted(self._agents.keys())


@dataclass
class ToolSpec:
    name: str
    required_permission: str
    handler: Callable[[Dict[str, Any]], Dict[str, Any]]


class ToolExecutionLayer:
    def __init__(self) -> None:
        self._tools: Dict[str, ToolSpec] = {}
        self.execution_log: List[Dict[str, Any]] = []

    def register(self, tool: ToolSpec) -> None:
        self._tools[tool.name] = tool

    def execute(self, tool_name: str, payload: Dict[str, Any], permissions: List[str]) -> Dict[str, Any]:
        if tool_name not in self._tools:
            raise KeyError(f"Tool '{tool_name}' not registered")
        tool = self._tools[tool_name]
        if tool.required_permission not in permissions:
            raise PermissionError(f"Missing permission '{tool.required_permission}' for tool '{tool_name}'")
        result = tool.handler(payload)
        self.execution_log.append(
            {
                "timestamp": _utc_now(),
                "tool": tool_name,
                "payload": payload,
                "result": result,
            }
        )
        return result


class CrossDevicePresence:
    def __init__(self) -> None:
        self._identities: Dict[str, Dict[str, str]] = {}

    def bind_device(self, user_id: str, device_id: str, channel: str) -> None:
        self._identities.setdefault(user_id, {})[device_id] = channel

    def get_devices(self, user_id: str) -> Dict[str, str]:
        return dict(self._identities.get(user_id, {}))


class RealtimeInteractionHub:
    def __init__(self) -> None:
        self._state: Dict[str, AssistantState] = {}
        self.events: List[Dict[str, Any]] = []

    def set_state(self, user_id: str, state: AssistantState) -> None:
        self._state[user_id] = state
        self.events.append({"type": "state", "user_id": user_id, "state": state.value, "timestamp": _utc_now()})

    def emit(self, user_id: str, event_type: str, payload: Dict[str, Any]) -> None:
        self.events.append(
            {
                "type": event_type,
                "user_id": user_id,
                "payload": payload,
                "state": self._state.get(user_id, AssistantState.IDLE).value,
                "timestamp": _utc_now(),
            }
        )


class PersonalSecurityLayer:
    _SCAM_KEYWORDS = (
        "otp",
        "pin",
        "bank transfer",
        "wire money",
        "gift card",
        "urgent payment",
    )

    def detect(self, user_text: str) -> Dict[str, Any]:
        lowered = user_text.lower()
        hits = [kw for kw in self._SCAM_KEYWORDS if kw in lowered]
        risk = min(1.0, 0.2 + 0.2 * len(hits)) if hits else 0.1
        return {
            "risk_score": risk,
            "flags": hits,
            "warning": bool(hits),
        }

    def guard_action(self, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = str(payload.get("url", ""))
        risky_webhook = action == "trigger_webhook" and url.startswith("http://")
        return {
            "allowed": not risky_webhook,
            "reason": "Webhook must use HTTPS" if risky_webhook else "ok",
        }


class PersonalIntelligenceOrchestrator:
    def __init__(
        self,
        memory: LifeMemoryEngine,
        decision_engine: DecisionEngine,
        agents: MultiAgentSystem,
        tools: ToolExecutionLayer,
        devices: CrossDevicePresence,
        realtime: RealtimeInteractionHub,
        security: PersonalSecurityLayer,
    ) -> None:
        self.memory = memory
        self.decision_engine = decision_engine
        self.agents = agents
        self.tools = tools
        self.devices = devices
        self.realtime = realtime
        self.security = security

    def _resolve_intent(self, user_text: str) -> str:
        lowered = user_text.lower()
        if any(k in lowered for k in ("schedule", "calendar", "meeting")):
            return "calendar_action"
        if any(k in lowered for k in ("budget", "expense", "finance")):
            return "finance_review"
        if any(k in lowered for k in ("health", "wellness", "sleep")):
            return "wellness_check"
        if "search" in lowered or "research" in lowered:
            return "research_query"
        return "general_assistance"

    def _route_agent(self, intent: str) -> str:
        if intent.startswith("calendar"):
            return "calendar"
        if intent.startswith("finance"):
            return "finance"
        if intent.startswith("wellness"):
            return "wellness"
        if intent.startswith("research"):
            return "research"
        return "communication"

    def handle_input(
        self,
        user_id: str,
        user_text: str,
        channel: str,
        device_id: str,
        permissions: Optional[List[str]] = None,
        autonomy_level: AutonomyLevel = AutonomyLevel.LEVEL_0_SUGGEST_ONLY,
    ) -> Dict[str, Any]:
        effective_permissions = permissions or []
        self.devices.bind_device(user_id, device_id, channel)

        self.realtime.set_state(user_id, AssistantState.LISTENING)
        self.realtime.set_state(user_id, AssistantState.THINKING)

        security_eval = self.security.detect(user_text)
        intent = self._resolve_intent(user_text)
        decision = self.decision_engine.evaluate(
            DecisionContext(
                user_id=user_id,
                intent=intent,
                risk_score=security_eval["risk_score"],
                permissions=effective_permissions,
                autonomy_level=autonomy_level,
            )
        )

        agent_name = self._route_agent(intent)
        agent_result = self.agents.invoke(
            agent_name,
            user_text,
            {
                "intent": intent,
                "memory_summary": self.memory.summarize(user_id, top_n=3, include_private=False),
                "security": security_eval,
            },
        )

        tool_result = None
        if intent == "calendar_action" and decision["mode"] in ("execute_authorized", "execute_automatic"):
            tool_result = self.tools.execute(
                "create_task",
                {"title": user_text, "source": channel},
                permissions=effective_permissions,
            )

        response = (
            f"[{agent_result.agent}] {agent_result.content}. "
            f"Decision mode: {decision['mode']}."
        )
        if security_eval["warning"]:
            response += " Security warning: potential scam indicators detected."
        if tool_result:
            response += f" Tool outcome: {tool_result.get('status', 'ok')}."

        self.realtime.set_state(user_id, AssistantState.RESPONDING)
        self.realtime.emit(
            user_id,
            "orchestrator_decision",
            {
                "intent": intent,
                "agent": agent_name,
                "decision_mode": decision["mode"],
                "tool_result": tool_result,
            },
        )
        self.realtime.set_state(user_id, AssistantState.IDLE)

        return {
            "response": response,
            "intent": intent,
            "agent": agent_name,
            "decision": decision,
            "security": security_eval,
            "devices": self.devices.get_devices(user_id),
        }


def _default_tool_result(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {"status": "accepted", "payload": payload}


def build_personal_intelligence_layer() -> PersonalIntelligenceOrchestrator:
    memory = LifeMemoryEngine()
    decision_engine = DecisionEngine()
    agents = MultiAgentSystem()
    tools = ToolExecutionLayer()
    devices = CrossDevicePresence()
    realtime = RealtimeInteractionHub()
    security = PersonalSecurityLayer()

    for name in (
        "memory",
        "research",
        "calendar",
        "finance",
        "wellness",
        "communication",
        "security",
        "device",
        "notification",
    ):
        agents.register(DomainAgent(name=name))

    tools.register(ToolSpec(name="search_web", required_permission="tool.search", handler=_default_tool_result))
    tools.register(ToolSpec(name="store_note", required_permission="tool.notes", handler=_default_tool_result))
    tools.register(ToolSpec(name="create_task", required_permission="tool.tasks", handler=_default_tool_result))
    tools.register(ToolSpec(name="schedule_event", required_permission="tool.calendar", handler=_default_tool_result))
    tools.register(ToolSpec(name="send_notification", required_permission="tool.notify", handler=_default_tool_result))
    tools.register(ToolSpec(name="call_api", required_permission="tool.api", handler=_default_tool_result))
    tools.register(ToolSpec(name="trigger_webhook", required_permission="tool.webhook", handler=_default_tool_result))

    return PersonalIntelligenceOrchestrator(
        memory=memory,
        decision_engine=decision_engine,
        agents=agents,
        tools=tools,
        devices=devices,
        realtime=realtime,
        security=security,
    )
