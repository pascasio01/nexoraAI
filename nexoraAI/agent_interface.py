from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class AgentResult:
    agent: str
    output: str
    success: bool = True
    metadata: Dict[str, Any] | None = None


class AssistantAgent:
    name = "assistant"

    async def run(self, payload: Dict[str, Any]) -> AgentResult:  # pragma: no cover - interface only
        raise NotImplementedError
