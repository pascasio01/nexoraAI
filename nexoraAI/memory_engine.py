from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List


@dataclass
class StructuredKnowledge:
    preferences: List[str] = field(default_factory=list)
    habits: List[str] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)
    tasks: List[str] = field(default_factory=list)
    important_facts: List[str] = field(default_factory=list)
    relationships: List[str] = field(default_factory=list)


class MemoryEngine:
    MAX_RECENT_KNOWLEDGE_ITEMS = 3

    def __init__(self, short_capacity: int = 8, mid_capacity: int = 30):
        self.short_term: Dict[str, Deque[dict]] = defaultdict(lambda: deque(maxlen=short_capacity))
        self.mid_term: Dict[str, Deque[dict]] = defaultdict(lambda: deque(maxlen=mid_capacity))
        self.long_term: Dict[str, StructuredKnowledge] = defaultdict(StructuredKnowledge)

    def _extract_structured_knowledge(self, text: str) -> StructuredKnowledge:
        lower = text.lower()
        knowledge = StructuredKnowledge()

        if any(trigger in lower for trigger in ("i prefer", "prefiero", "me gusta")):
            knowledge.preferences.append(text)
        if any(trigger in lower for trigger in ("every day", "daily", "cada día", "cada dia", "habit")):
            knowledge.habits.append(text)
        if any(trigger in lower for trigger in ("my goal", "mi objetivo", "quiero lograr")):
            knowledge.goals.append(text)
        if any(trigger in lower for trigger in ("remember to", "recuerda", "todo:", "task:")):
            knowledge.tasks.append(text)
        if any(trigger in lower for trigger in ("my name is", "mi nombre es", "important", "importante")):
            knowledge.important_facts.append(text)
        if any(trigger in lower for trigger in ("my wife", "my husband", "my friend", "mi pareja", "mi amigo")):
            knowledge.relationships.append(text)

        return knowledge

    def record_interaction(self, user_id: str, user_text: str, assistant_text: str) -> None:
        interaction = {"user": user_text, "assistant": assistant_text}
        self.short_term[user_id].append(interaction)
        self.mid_term[user_id].append(interaction)
        extracted = self._extract_structured_knowledge(user_text)
        current = self.long_term[user_id]
        current.preferences.extend(extracted.preferences)
        current.habits.extend(extracted.habits)
        current.goals.extend(extracted.goals)
        current.tasks.extend(extracted.tasks)
        current.important_facts.extend(extracted.important_facts)
        current.relationships.extend(extracted.relationships)

    def get_memory_context(self, user_id: str) -> dict:
        knowledge = self.long_term[user_id]
        return {
            "short_term": list(self.short_term[user_id]),
            "mid_term_count": len(self.mid_term[user_id]),
            "knowledge": {
                "preferences": knowledge.preferences[-self.MAX_RECENT_KNOWLEDGE_ITEMS :],
                "habits": knowledge.habits[-self.MAX_RECENT_KNOWLEDGE_ITEMS :],
                "goals": knowledge.goals[-self.MAX_RECENT_KNOWLEDGE_ITEMS :],
                "tasks": knowledge.tasks[-self.MAX_RECENT_KNOWLEDGE_ITEMS :],
                "important_facts": knowledge.important_facts[-self.MAX_RECENT_KNOWLEDGE_ITEMS :],
                "relationships": knowledge.relationships[-self.MAX_RECENT_KNOWLEDGE_ITEMS :],
            },
        }
