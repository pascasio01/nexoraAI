from fastapi import Request, Response

from config import BOT_TOKEN, logger


async def telegram_startup() -> None:
    if not BOT_TOKEN:
        logger.info("Telegram disabled (BOT_TOKEN missing).")


async def telegram_shutdown() -> None:
    return None


async def telegram_webhook(token: str, request: Request):
    _ = request
    if not BOT_TOKEN or token != BOT_TOKEN:
        return Response(status_code=403)
    return {"ok": False, "message": "Telegram actor not configured in this deployment."}
