from fastapi import Request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from ai_core import ask_nexora
from config import (
    ALLOW_ALL_USERS,
    APP_NAME,
    BASE_URL,
    BOT_TOKEN,
    MODEL_NAME,
    OWNER_ID,
    logger,
)
from memory import reset_memory


tg_app = None


def _allowed_user(update: Update) -> bool:
    if OWNER_ID is None:
        return ALLOW_ALL_USERS
    if update.effective_user is None:
        return False
    return update.effective_user.id == OWNER_ID


async def tg_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _allowed_user(update):
        return
    if update.message:
        await update.message.reply_text(f"✅ {APP_NAME} activa y lista.")


async def tg_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _allowed_user(update):
        return
    if update.message:
        await update.message.reply_text(f"Modelo: {MODEL_NAME} | Telegram: activo")


async def tg_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _allowed_user(update):
        return
    if update.effective_user:
        await reset_memory(str(update.effective_user.id))
    if update.message:
        await update.message.reply_text("Memoria reiniciada.")


async def handle_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _allowed_user(update):
        return
    if update.message and update.message.text and update.effective_user:
        reply = await ask_nexora(str(update.effective_user.id), update.message.text, "telegram")
        await update.message.reply_text(reply)


async def telegram_startup() -> None:
    global tg_app

    if not BOT_TOKEN:
        logger.warning("BOT_TOKEN missing. Telegram lifecycle disabled.")
        tg_app = None
        return

    try:
        tg_app = ApplicationBuilder().token(BOT_TOKEN).build()
        tg_app.add_handler(CommandHandler("start", tg_start))
        tg_app.add_handler(CommandHandler("status", tg_status))
        tg_app.add_handler(CommandHandler("reset", tg_reset))
        tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_telegram))

        await tg_app.initialize()
        await tg_app.start()

        if BASE_URL:
            await tg_app.bot.set_webhook(url=f"{BASE_URL}/tg/{BOT_TOKEN}")
        logger.info("Telegram lifecycle started")
    except Exception as exc:
        logger.warning(f"Telegram startup failed: {exc}")
        tg_app = None


async def telegram_shutdown() -> None:
    global tg_app
    if tg_app is None:
        return

    try:
        if BASE_URL:
            await tg_app.bot.delete_webhook()
        await tg_app.stop()
        await tg_app.shutdown()
    except Exception as exc:
        logger.warning(f"Telegram shutdown failed: {exc}")
    finally:
        tg_app = None


async def telegram_webhook(token: str, request: Request):
    if not BOT_TOKEN or token != BOT_TOKEN:
        return {"ok": False, "error": "invalid token"}
    if tg_app is None:
        return {"ok": False, "error": "telegram is not running"}

    payload = await request.json()
    update = Update.de_json(payload, tg_app.bot)
    await tg_app.process_update(update)
    return {"ok": True}
