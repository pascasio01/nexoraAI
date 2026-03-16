import json

from fastapi import Request, Response
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

from ai_core import ask_nexora
from config import BASE_URL, BOT_TOKEN, MODEL_NAME, TELEGRAM_ENABLED, logger
from memory import reset_memory

tg_app = None


async def tg_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Hola 👋 Soy Nexora. Modelo actual: {MODEL_NAME}")


async def tg_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Nexora está operativo.")


async def tg_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    await reset_memory(user_id)
    await update.message.reply_text("Memoria de chat reiniciada.")


async def handle_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return
    user_text = update.message.text or ""
    user_id = str(update.effective_user.id)
    answer = await ask_nexora(user_id=user_id, user_text=user_text)
    await update.message.reply_text(answer)


async def telegram_startup() -> None:
    global tg_app

    if not TELEGRAM_ENABLED:
        logger.warning("Telegram disabled: BOT_TOKEN missing or BASE_URL invalid.")
        return

    try:
        tg_app = ApplicationBuilder().token(BOT_TOKEN).build()
        tg_app.add_handler(CommandHandler("start", tg_start))
        tg_app.add_handler(CommandHandler("status", tg_status))
        tg_app.add_handler(CommandHandler("reset", tg_reset))
        tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_telegram))

        await tg_app.initialize()
        await tg_app.start()
        await tg_app.bot.set_webhook(url=f"{BASE_URL}/tg/{BOT_TOKEN}")
        logger.info("Telegram webhook configured.")
    except Exception as exc:
        logger.warning("Telegram startup failed; running without Telegram: %s", exc)
        tg_app = None


async def telegram_shutdown() -> None:
    global tg_app

    if tg_app is None:
        return

    try:
        await tg_app.bot.delete_webhook()
        await tg_app.stop()
        await tg_app.shutdown()
    except Exception as exc:
        logger.warning("Telegram shutdown warning: %s", exc)
    finally:
        tg_app = None


async def telegram_webhook(token: str, request: Request):
    if tg_app is None:
        return Response("Telegram disabled", status_code=503)
    if not BOT_TOKEN or token != BOT_TOKEN:
        return Response("Unauthorized", status_code=401)

    data = await request.json()
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return Response("ok")


async def telegram_status() -> dict:
    return {
        "enabled": TELEGRAM_ENABLED,
        "active": tg_app is not None,
        "base_url_valid": TELEGRAM_ENABLED,
    }
