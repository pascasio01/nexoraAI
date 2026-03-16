from __future__ import annotations

from typing import Optional

from fastapi import Request
from telegram import Update
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

from ai_core import ask_nexora
from config import BASE_URL, BOT_TOKEN, logger
from memory import reset_memory

_tg_app: Optional[Application] = None


async def _cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text("👋 Nexora is online. Send me a message anytime.")


async def _cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    mode = "webhook" if BASE_URL and BASE_URL.startswith("http") else "polling-disabled"
    await update.effective_message.reply_text(f"✅ Telegram actor active ({mode}).")


async def _cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    await reset_memory(user_id)
    await update.effective_message.reply_text("🧠 Your conversation memory has been reset.")


async def _handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.effective_message.text or "").strip()
    if not text:
        return
    user_id = str(update.effective_user.id)
    reply = await ask_nexora(user_id=user_id, text=text, channel="telegram")
    await update.effective_message.reply_text(reply)


async def telegram_startup() -> None:
    global _tg_app

    if not BOT_TOKEN:
        logger.warning("Telegram startup skipped: BOT_TOKEN missing.")
        return

    try:
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", _cmd_start))
        app.add_handler(CommandHandler("status", _cmd_status))
        app.add_handler(CommandHandler("reset", _cmd_reset))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _handle_text))

        await app.initialize()
        await app.start()

        if BASE_URL and BASE_URL.startswith("http"):
            webhook_url = f"{BASE_URL}/tg/{BOT_TOKEN}"
            try:
                await app.bot.set_webhook(webhook_url)
            except Exception as exc:
                logger.warning("Telegram webhook registration failed: %s", exc)
        elif BASE_URL:
            logger.warning("Telegram webhook skipped: invalid BASE_URL=%r", BASE_URL)

        _tg_app = app
        logger.info("Telegram actor initialized.")
    except Exception as exc:
        logger.warning("Telegram startup failed gracefully: %s", exc)
        _tg_app = None


async def telegram_shutdown() -> None:
    global _tg_app
    app = _tg_app
    if app is None:
        return

    try:
        if BASE_URL and BASE_URL.startswith("http"):
            try:
                await app.bot.delete_webhook()
            except Exception as exc:
                logger.warning("Telegram webhook deletion issue: %s", exc)
        await app.stop()
        await app.shutdown()
    except Exception as exc:
        logger.warning("Telegram shutdown issue: %s", exc)
    finally:
        _tg_app = None


async def telegram_webhook(token: str, request: Request) -> bool:
    app = _tg_app
    if app is None or not BOT_TOKEN or token != BOT_TOKEN:
        return False

    try:
        payload = await request.json()
        update = Update.de_json(payload, app.bot)
        await app.process_update(update)
        return True
    except Exception as exc:
        logger.warning("Telegram webhook processing failed: %s", exc)
        return False


def telegram_is_active() -> bool:
    return _tg_app is not None
