from __future__ import annotations

from typing import Any

from fastapi import Request, Response

from config import BOT_TOKEN, logger
from ai_core import ask_nexora
from memory import reset_memory

try:
    from telegram import Update
    from telegram.constants import ChatAction
    from telegram.ext import (
        Application,
        ApplicationBuilder,
        CommandHandler,
        ContextTypes,
        MessageHandler,
        filters,
    )
except Exception:  # pragma: no cover - optional runtime integration
    Application = None
    ApplicationBuilder = None
    CommandHandler = None
    ContextTypes = None
    MessageHandler = None
    Update = None
    ChatAction = None
    filters = None

_tg_app: Application | None = None


async def tg_start(update: Any, context: Any) -> None:
    await update.message.reply_text("👋 Hola. Tu agente personal está activo.")


async def tg_status(update: Any, context: Any) -> None:
    await update.message.reply_text("✅ Telegram conectado al núcleo de Nexora.")


async def tg_reset(update: Any, context: Any) -> None:
    user_id = str(update.effective_user.id)
    await reset_memory(user_id)
    await update.message.reply_text("🧹 Memoria reiniciada para tu agente.")


async def handle_telegram(update: Any, context: Any) -> None:
    if not update.message or not update.message.text:
        return
    user_id = str(update.effective_user.id)
    text = update.message.text
    if ChatAction:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    answer = await ask_nexora(user_id, text, "Telegram")
    await update.message.reply_text(answer)


async def telegram_startup() -> None:
    """Initialize Telegram bot lifecycle if token/dependency is available."""
    global _tg_app
    if not BOT_TOKEN or ApplicationBuilder is None:
        logger.info("Telegram disabled (missing BOT_TOKEN or telegram dependency).")
        _tg_app = None
        return

    try:
        _tg_app = ApplicationBuilder().token(BOT_TOKEN).build()
        _tg_app.add_handler(CommandHandler("start", tg_start))
        _tg_app.add_handler(CommandHandler("status", tg_status))
        _tg_app.add_handler(CommandHandler("reset", tg_reset))
        _tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_telegram))
        await _tg_app.initialize()
        await _tg_app.start()
        logger.info("Telegram lifecycle initialized.")
    except Exception as exc:
        logger.warning("Telegram startup failed; running without Telegram: %s", exc)
        _tg_app = None


async def telegram_shutdown() -> None:
    global _tg_app
    if not _tg_app:
        return
    try:
        await _tg_app.stop()
        await _tg_app.shutdown()
    except Exception as exc:
        logger.warning("Telegram shutdown warning: %s", exc)
    _tg_app = None


async def telegram_webhook(token: str, request: Request):
    if not BOT_TOKEN or token != BOT_TOKEN:
        return Response(status_code=403)
    if _tg_app is None or Update is None:
        return Response(status_code=503)

    data = await request.json()
    await _tg_app.process_update(Update.de_json(data, _tg_app.bot))
    return {"ok": True}


def telegram_is_ready() -> bool:
    return _tg_app is not None
