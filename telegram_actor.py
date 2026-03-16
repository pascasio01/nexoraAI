from fastapi import Request

from config import BOT_TOKEN


async def telegram_startup() -> None:
    if not BOT_TOKEN:
        return


async def telegram_shutdown() -> None:
    return


async def telegram_webhook(token: str, request: Request):
    _ = request
    if not BOT_TOKEN or token != BOT_TOKEN:
        return {"ok": False, "error": "unauthorized"}
    return {"ok": True}
