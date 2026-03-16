from fastapi import Request, Response
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

from ai_core import ask_nexora
from config import APP_NAME, BASE_URL, BOT_TOKEN, OWNER_ID, logger
from memory import reset_memory


tg_app = None


async def tg_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if OWNER_ID != 0 and update.effective_user and update.effective_user.id != OWNER_ID:
        return
    if update.message:
        await update.message.reply_text(f"✅ {APP_NAME} activa.")


async def tg_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if OWNER_ID != 0 and update.effective_user and update.effective_user.id != OWNER_ID:
        return
    if update.effective_user:
        await reset_memory(str(update.effective_user.id))
    if update.message:
        await update.message.reply_text("Memoria reiniciada.")


async def handle_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if OWNER_ID != 0 and update.effective_user and update.effective_user.id != OWNER_ID:
        return
    if update.message and update.message.text and update.effective_user:
        answer = await ask_nexora(str(update.effective_user.id), update.message.text, "telegram")
        await update.message.reply_text(answer)


async def telegram_startup():
    global tg_app
    if not BOT_TOKEN:
        return
    try:
        tg_app = ApplicationBuilder().token(BOT_TOKEN).build()
        tg_app.add_handler(CommandHandler("start", tg_start))
        tg_app.add_handler(CommandHandler("reset", tg_reset))
        tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_telegram))
        await tg_app.initialize()
        await tg_app.start()
        if BASE_URL:
            await tg_app.bot.set_webhook(url=f"{BASE_URL}/tg/{BOT_TOKEN}")
    except Exception as e:
        logger.warning(f"Telegram no pudo iniciar: {e}")
        tg_app = None


async def telegram_shutdown():
    global tg_app
    if tg_app is None:
        return
    try:
        if BASE_URL:
            await tg_app.bot.delete_webhook()
        await tg_app.stop()
        await tg_app.shutdown()
    except Exception as e:
        logger.warning(f"Error apagando Telegram: {e}")
    tg_app = None


async def telegram_webhook(token: str, request: Request):
    if not BOT_TOKEN or token != BOT_TOKEN:
        return Response(status_code=403)
    if tg_app is None:
        return Response(status_code=503)
    data = await request.json()
    await tg_app.process_update(Update.de_json(data, tg_app.bot))
    return {"ok": True}
