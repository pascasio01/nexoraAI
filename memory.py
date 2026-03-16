from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class UserAssistantState:
    profile: str = ""
    settings: dict = field(default_factory=dict)
    conversation_history: list[dict] = field(default_factory=list)
    long_term_memory: list[str] = field(default_factory=list)
    notes: list[dict] = field(default_factory=list)
    tasks: list[dict] = field(default_factory=list)
    reminders: list[dict] = field(default_factory=list)


class AssistantMemoryStore:
    def __init__(self, max_history: int = 20):
        self.max_history = max_history
        self._state: dict[str, UserAssistantState] = defaultdict(UserAssistantState)

    def ensure_user(self, user_id: str) -> UserAssistantState:
        return self._state[user_id]

    def get_profile(self, user_id: str) -> str:
        return self.ensure_user(user_id).profile

    def set_profile(self, user_id: str, profile: str) -> None:
        self.ensure_user(user_id).profile = profile

    def get_settings(self, user_id: str) -> dict:
        return self.ensure_user(user_id).settings

    def update_settings(self, user_id: str, updates: dict) -> dict:
        state = self.ensure_user(user_id)
        state.settings.update(updates)
        return state.settings

    def add_message(self, user_id: str, role: str, content: str, channel: str) -> None:
        state = self.ensure_user(user_id)
        state.conversation_history.append(
            {"role": role, "content": content, "channel": channel}
        )
        if len(state.conversation_history) > self.max_history:
            state.conversation_history = state.conversation_history[-self.max_history :]

    def get_history(self, user_id: str) -> list[dict]:
        return list(self.ensure_user(user_id).conversation_history)

    def add_long_term_memory(self, user_id: str, memory: str) -> None:
        self.ensure_user(user_id).long_term_memory.append(memory)

    def get_long_term_memory(self, user_id: str) -> list[str]:
        return list(self.ensure_user(user_id).long_term_memory)

    def create_note(self, user_id: str, note: dict) -> dict:
        self.ensure_user(user_id).notes.append(note)
        return note

    def create_task(self, user_id: str, task: dict) -> dict:
        self.ensure_user(user_id).tasks.append(task)
        return task

    def create_reminder(self, user_id: str, reminder: dict) -> dict:
        self.ensure_user(user_id).reminders.append(reminder)
        return reminder

    def reset(self, user_id: str) -> None:
        self._state[user_id] = UserAssistantState()
