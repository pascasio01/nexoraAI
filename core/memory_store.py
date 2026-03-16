_store: dict[str, list[str]] = {}


async def save_long_memory(user_id: str, memory: str) -> None:
    _store.setdefault(user_id, []).append(memory)


async def load_long_memory(user_id: str) -> list[str]:
    return _store.get(user_id, [])
