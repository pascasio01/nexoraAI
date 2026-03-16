from .types import MemoryCandidate


class MemoryEngine:
    def extract(self, message: str) -> MemoryCandidate | None:
        lowered = message.lower()
        markers = ["me gusta", "prefiero", "my preference", "recuerda que"]
        if any(marker in lowered for marker in markers):
            return MemoryCandidate(
                tier="mid_term",
                content=message,
                summary="Preferencia detectada del usuario",
                importance=3,
                sensitive=False,
            )
        return None
