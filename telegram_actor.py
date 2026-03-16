from fastapi import Request

from config import BOT_TOKEN
from config import logger


async def telegram_startup() -> None:
    # Placeholder lifecycle hook. Webhook mode can be expanded here without changing app wiring.
    if not BOT_TOKEN:
        logger.info("Telegram disabled: BOT_TOKEN not configured.")
        return


async def telegram_shutdown() -> None:
    return


async def telegram_webhook(token: str, request: Request):
    _ = request
    if not BOT_TOKEN or token != BOT_TOKEN:
        return {"ok": False, "error": "unauthorized"}
    return {"ok": True}
