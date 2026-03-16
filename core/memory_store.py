import asyncio

_store: dict[str, list[str]] = {}
_store_lock = asyncio.Lock()


async def save_long_memory(user_id: str, memory: str) -> None:
    async with _store_lock:
        _store.setdefault(user_id, []).append(memory)


async def load_long_memory(user_id: str) -> list[str]:
    async with _store_lock:
        return list(_store.get(user_id, []))
