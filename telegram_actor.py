from __future__ import annotations

import json

from fastapi import Request, Response
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

from ai_core import ask_nexora
from config import APP_NAME, BASE_URL, BOT_TOKEN, MODEL_NAME, logger

_tg_app = None


async def _tg_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"👋 Hola, soy {APP_NAME}. ¿En qué te ayudo?")


async def _tg_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"✅ {APP_NAME} online | model={MODEL_NAME}")


async def _tg_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user_id = str(update.effective_user.id) if update.effective_user else "telegram_anonymous"
    text = update.message.text or ""

    await update.message.chat.send_action(action=ChatAction.TYPING)
    answer = await ask_nexora(user_id=user_id, text=text, channel="telegram")
    await update.message.reply_text(answer)


async def telegram_startup() -> None:
    global _tg_app

    if not BOT_TOKEN:
        logger.warning("BOT_TOKEN missing: Telegram actor disabled.")
        return

    try:
        _tg_app = ApplicationBuilder().token(BOT_TOKEN).build()
        _tg_app.add_handler(CommandHandler("start", _tg_start))
        _tg_app.add_handler(CommandHandler("status", _tg_status))
        _tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _tg_message))

        await _tg_app.initialize()
        if BASE_URL:
            await _tg_app.bot.set_webhook(url=f"{BASE_URL}/tg/{BOT_TOKEN}")
        await _tg_app.start()
        logger.info("Telegram actor started.")
    except Exception as exc:
        logger.warning("Telegram startup skipped due to error: %s", exc)
        _tg_app = None


async def telegram_shutdown() -> None:
    global _tg_app

    if not _tg_app:
        return

    try:
        if BASE_URL:
            await _tg_app.bot.delete_webhook()
        await _tg_app.stop()
        await _tg_app.shutdown()
    except Exception as exc:
        logger.warning("Telegram shutdown issue: %s", exc)
    finally:
        _tg_app = None


async def telegram_webhook(token: str, request: Request):
    if not _tg_app or token != BOT_TOKEN:
        return Response(status_code=403)

    data = await request.json()
    update = Update.de_json(data, _tg_app.bot)
    await _tg_app.process_update(update)
    return {"ok": True}


def telegram_health() -> dict:
    return {
        "configured": bool(BOT_TOKEN),
        "running": _tg_app is not None,
        "webhook": f"{BASE_URL}/tg/{BOT_TOKEN}" if BOT_TOKEN and BASE_URL else None,
    }
