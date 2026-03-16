from __future__ import annotations

from fastapi import Request

from config import logger, settings


async def telegram_startup() -> None:
    if not settings.bot_token:
        logger.info("Telegram disabled: BOT_TOKEN not configured.")
        return
    logger.info("Telegram startup prepared (webhook-based mode).")


async def telegram_shutdown() -> None:
    logger.info("Telegram shutdown complete.")


async def telegram_webhook(token: str, request: Request, agent_manager) -> dict:
    if not settings.bot_token:
        return {"ok": False, "message": "Telegram not configured."}
    if settings.telegram_webhook_secret and token != settings.telegram_webhook_secret:
        return {"ok": False, "message": "Invalid token."}

    payload = await request.json()
    message = payload.get("message", {})
    text = message.get("text")
    chat = message.get("chat", {})
    user_id = str(chat.get("id", "telegram-anon"))

    if not text:
        return {"ok": True, "message": "No text content."}

    answer = await agent_manager.route_request(user_id=user_id, message=text, channel="telegram")
    return {"ok": True, "response": answer}
