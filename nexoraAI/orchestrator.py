import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


def _utc_iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AgentEvent:
    event_type: str
    source_user_id: str
    target_user_id: str
    payload: dict
    event_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=_utc_iso_now)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, raw_event: str) -> "AgentEvent":
        event_data = json.loads(raw_event)
        return cls(**event_data)


class PersonalAgent:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.received_events = []

    def receive_event(self, event: AgentEvent) -> AgentEvent:
        if event.target_user_id != self.user_id:
            raise ValueError(
                f"Event intended for user {event.target_user_id} cannot be delivered to agent for user {self.user_id}"
            )
        self.received_events.append(event)
        return event


class Orchestrator:
    def __init__(self):
        self._agents_by_user = {}
        self._is_running = False

    def start(self):
        self._is_running = True
        return self._is_running

    def stop(self):
        self._is_running = False
        return self._is_running

    def get_or_create_agent(self, user_id: str) -> PersonalAgent:
        agent = self._agents_by_user.get(user_id)
        if agent is None:
            agent = PersonalAgent(user_id=user_id)
            self._agents_by_user[user_id] = agent
        return agent

    def send_event(self, event: AgentEvent) -> AgentEvent:
        if not self._is_running:
            raise RuntimeError("Cannot send event: Orchestrator must be started before sending events. Call start() first.")
        target_agent = self.get_or_create_agent(event.target_user_id)
        return target_agent.receive_event(event)

    def send_message(self, source_user_id: str, target_user_id: str, event_type: str, payload: dict) -> AgentEvent:
        event = AgentEvent(
            event_type=event_type,
            source_user_id=source_user_id,
            target_user_id=target_user_id,
            payload=payload,
        )
        return self.send_event(event)

    def request_task(self, source_user_id: str, target_user_id: str, task_name: str, task_payload: dict) -> AgentEvent:
        return self.send_message(
            source_user_id=source_user_id,
            target_user_id=target_user_id,
            event_type="task.requested",
            payload={"task_name": task_name, "task_payload": task_payload},
        )
