from services.api_gateway.database import get_db


async def reset_memory(user_id: str):
    with get_db() as conn:
        conn.execute("DELETE FROM memory_items WHERE user_id = ?", (int(user_id),))
