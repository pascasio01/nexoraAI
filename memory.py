from collections import defaultdict, deque
from dataclasses import dataclass


@dataclass(slots=True)
class SessionMemory:
    room_id: str
    session_id: str
    user_id: str


class MemoryStore:
    """In-memory fallback compatible with future persistent memory adapters.

    Each user gets a bounded deque with up to ``max_messages`` role-tagged entries,
    preserving context while preventing unbounded memory growth.
    """

    def __init__(self, max_messages: int = 50) -> None:
        self._history: dict[str, deque[dict[str, str]]] = defaultdict(lambda: deque(maxlen=max_messages))
        self._sessions: dict[str, SessionMemory] = {}

    def add_message(self, user_id: str, role: str, content: str) -> None:
        self._history[user_id].append({"role": role, "content": content})

    def get_history(self, user_id: str) -> list[dict[str, str]]:
        return list(self._history[user_id])

    def bind_session(self, room_id: str, session_id: str, user_id: str) -> None:
        self._sessions[session_id] = SessionMemory(room_id=room_id, session_id=session_id, user_id=user_id)

    def get_session(self, session_id: str) -> SessionMemory | None:
        return self._sessions.get(session_id)


memory_store = MemoryStore()
