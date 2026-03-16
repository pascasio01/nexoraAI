"""Telegram lifecycle and webhook processing with safe optional startup."""

from __future__ import annotations

from fastapi import Request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

from ai_core import ask_nexora
from config import APP_NAME, BASE_URL, BOT_TOKEN, logger
from memory import reset_memory

_tg_app = None


def telegram_status() -> dict:
    return {
        "configured": bool(BOT_TOKEN and BASE_URL),
        "running": _tg_app is not None,
    }


async def tg_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    await reset_memory(user_id)
    await update.message.reply_text(f"{APP_NAME} is active. Your personal memory was reset.")


async def tg_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    st = telegram_status()
    await update.message.reply_text(f"Telegram configured={st['configured']} running={st['running']}")


async def handle_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return
    user_id = str(update.effective_user.id)
    text = update.message.text or ""
    answer = await ask_nexora(user_id=user_id, text=text, channel="Telegram")
    await update.message.reply_text(answer)


async def telegram_startup() -> None:
    global _tg_app
    if not BOT_TOKEN or not BASE_URL:
        logger.info("Telegram disabled because BOT_TOKEN or BASE_URL is missing")
        return

    _tg_app = ApplicationBuilder().token(BOT_TOKEN).build()
    _tg_app.add_handler(CommandHandler("start", tg_start))
    _tg_app.add_handler(CommandHandler("status", tg_status))
    _tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_telegram))

    await _tg_app.initialize()
    await _tg_app.start()

    webhook_url = f"{BASE_URL}/tg/{BOT_TOKEN}"
    await _tg_app.bot.set_webhook(webhook_url)
    logger.info("Telegram webhook enabled at %s", webhook_url)


async def telegram_shutdown() -> None:
    global _tg_app
    if _tg_app is None:
        return

    await _tg_app.stop()
    await _tg_app.shutdown()
    _tg_app = None


async def telegram_webhook(token: str, request: Request) -> dict:
    if not BOT_TOKEN or token != BOT_TOKEN or _tg_app is None:
        return {"ok": False, "reason": "telegram_not_available"}

    payload = await request.json()
    update = Update.de_json(payload, _tg_app.bot)
    await _tg_app.process_update(update)
    return {"ok": True}
