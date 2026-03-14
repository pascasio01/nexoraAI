import os
import asyncio

from fastapi import FastAPI, Request

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

telegram_app = None

async def tg_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Acceso no autorizado.")
        return

    memory_store[f"tg:{update.effective_user.id}"] = []
    await update.message.reply_text(
        f"Hola. Soy {APP_NAME}. Estoy activa, privada y lista para ayudarte."
    )

async def tg_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Acceso no autorizado.")
        return

    memory_store[f"tg:{update.effective_user.id}"] = []
    await update.message.reply_text("Memoria reiniciada.")

async def tg_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Acceso no autorizado.")
        return

    await update.message.reply_text(
        f"{APP_NAME} activa.\n"
        f"Modelo: {MODEL_NAME}\n"
        f"Noticias tiempo real: {NEWS_MODE}\n"
        f"Documentos: {DOCS_MODE}\n"
        f"Visión: {VISION_MODE}\n"
        f"Automatización: {AUTOMATION_MODE}"
    )

async def tg_responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Acceso no autorizado.")
        return

    if not update.message or not update.message.text:
        return

    texto = update.message.text.strip().lower()

    if "quién te creó" in texto or "quien te creo" in texto:
        await update.message.reply_text(
            f"Fui creada por {CREATOR_NAME}, también conocido como {CREATOR_ALIAS}."
        )
        return

    try:
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING
        )

        memory_key = f"tg:{update.effective_user.id}"
        answer = await ask_nexora(memory_key, update.message.text, "Telegram")
        await update.message.reply_text(answer)

    except Exception as e:
        await update.message.reply_text(f"Tuve un problema: {e}")

@app.on_event("startup")
async def startup_event():
    global telegram_app

    if BOT_TOKEN:
        telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

        telegram_app.add_handler(CommandHandler("start", tg_start))
        telegram_app.add_handler(CommandHandler("reset", tg_reset))
        telegram_app.add_handler(CommandHandler("status", tg_status))
        telegram_app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, tg_responder)
        )

        await telegram_app.initialize()
        await telegram_app.start()

        webhook_url = f"{BASE_URL}/telegram-webhook/{BOT_TOKEN}"
        await telegram_app.bot.set_webhook(url=webhook_url)
        print(f"Telegram webhook activo en: {webhook_url}")

@app.post("/telegram-webhook/{token}")
async def telegram_webhook(token: str, request: Request):
    if token != BOT_TOKEN:
        return {"ok": False, "error": "token inválido"}

    if telegram_app is None:
        return {"ok": False, "error": "telegram no iniciado"}

    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}

@app.on_event("shutdown")
async def shutdown_event():
    global telegram_app

    if telegram_app:
        await telegram_app.bot.delete_webhook()
        await telegram_app.stop()
        await telegram_app.shutdown()
        print("Telegram detenido.")
