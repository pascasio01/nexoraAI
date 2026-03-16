from dataclasses import dataclass


@dataclass(slots=True)
class MemoryCandidate:
    tier: str
    content: str
    summary: str
    importance: int
    sensitive: bool
