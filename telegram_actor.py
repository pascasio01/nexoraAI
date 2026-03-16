from __future__ import annotations

from fastapi import Request, Response
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from ai_core import ask_nexora
from config import APP_NAME, BASE_URL, BOT_TOKEN, OWNER_ID, logger
from memory import reset_memory

_tg_app: Application | None = None


async def tg_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(f"{APP_NAME} is online.")


async def tg_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text("Status: active")


async def tg_reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user:
        return
    await reset_memory(str(update.effective_user.id))
    if update.message:
        await update.message.reply_text("Memory reset.")


async def tg_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user or not update.message.text:
        return

    if OWNER_ID and update.effective_user.id != OWNER_ID:
        return

    reply = await ask_nexora(str(update.effective_user.id), update.message.text, "telegram")
    await update.message.reply_text(reply)


async def telegram_startup() -> None:
    global _tg_app

    if not BOT_TOKEN:
        logger.info("BOT_TOKEN not configured; Telegram lifecycle disabled")
        return

    try:
        _tg_app = ApplicationBuilder().token(BOT_TOKEN).build()
        _tg_app.add_handler(CommandHandler("start", tg_start))
        _tg_app.add_handler(CommandHandler("status", tg_status))
        _tg_app.add_handler(CommandHandler("reset", tg_reset))
        _tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, tg_message))

        await _tg_app.initialize()
        await _tg_app.start()

        if BASE_URL:
            await _tg_app.bot.set_webhook(url=f"{BASE_URL}/tg/{BOT_TOKEN}")

        logger.info("Telegram started")
    except Exception as exc:
        logger.warning("Telegram startup failed: %s", exc)
        _tg_app = None


async def telegram_shutdown() -> None:
    global _tg_app

    if _tg_app is None:
        return

    try:
        if BASE_URL:
            await _tg_app.bot.delete_webhook()
        await _tg_app.stop()
        await _tg_app.shutdown()
    except Exception as exc:
        logger.warning("Telegram shutdown warning: %s", exc)
    finally:
        _tg_app = None


async def telegram_webhook(token: str, request: Request):
    if not BOT_TOKEN or token != BOT_TOKEN:
        return Response(status_code=403)

    if _tg_app is None:
        return Response(status_code=503)

    data = await request.json()
    await _tg_app.process_update(Update.de_json(data, _tg_app.bot))
    return {"ok": True}


def telegram_enabled() -> bool:
    return _tg_app is not None
