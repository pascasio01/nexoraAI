import io

from fastapi import Request, Response
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import BOT_TOKEN, OWNER_ID, BASE_URL, APP_NAME, MODEL_NAME, TAVILY_API_KEY, ACTION_WEBHOOK_URL, logger, client
from ai_core import ask_nexora, SYSTEM_PROMPT
from memory import reset_memory, save_chat_memory

tg_app = None


# =========================
# TELEGRAM HANDLERS
# =========================
async def tg_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if OWNER_ID and update.effective_user and update.effective_user.id != OWNER_ID:
        if update.message:
            await update.message.reply_text("Acceso no autorizado.")
        return
    await reset_memory(str(update.effective_user.id))
    if update.message:
        await update.message.reply_text(f"{APP_NAME} activa. Memoria limpia y lista.")


async def tg_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if OWNER_ID and update.effective_user and update.effective_user.id != OWNER_ID:
        if update.message:
            await update.message.reply_text("Acceso no autorizado.")
        return
    msg = (
        f"Estado: activa\n"
        f"Modelo: {MODEL_NAME}\n"
        f"Web search: {'on' if TAVILY_API_KEY else 'off'}\n"
        f"Redis: ok\n"
        f"Actions webhook: {'on' if ACTION_WEBHOOK_URL else 'off'}"
    )
    if update.message:
        await update.message.reply_text(msg)


async def tg_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if OWNER_ID and update.effective_user and update.effective_user.id != OWNER_ID:
        if update.message:
            await update.message.reply_text("Acceso no autorizado.")
        return
    if update.effective_user:
        await reset_memory(str(update.effective_user.id))
    if update.message:
        await update.message.reply_text("Memoria reiniciada.")


async def handle_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if OWNER_ID and update.effective_user and update.effective_user.id != OWNER_ID:
        return
    if not update.message:
        return

    user_id = str(update.effective_user.id)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    try:
        if update.message.document:
            await update.message.reply_text("📥 Documento recibido. La biblioteca privada está lista para integrarse.")
            return

        if update.message.photo and client is not None:
            file = await context.bot.get_file(update.message.photo[-1].file_id)
            prompt = update.message.caption or "Analiza esta imagen."

            response = await client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": file.file_path}},
                        ],
                    },
                ],
                max_tokens=800,
            )
            answer = response.choices[0].message.content or "No pude analizar la imagen."
            await save_chat_memory(user_id, "user", prompt)
            await save_chat_memory(user_id, "assistant", answer)
            await update.message.reply_text(answer)
            return

        if update.message.voice and client is not None:
            file = await context.bot.get_file(update.message.voice.file_id)
            audio_data = io.BytesIO()
            await file.download_to_memory(audio_data)
            audio_data.name = "audio.ogg"
            audio_data.seek(0)

            transcription = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_data,
            )
            answer = await ask_nexora(user_id, transcription.text, "Telegram")
            await update.message.reply_text(answer)
            return

        if update.message.text:
            res = await ask_nexora(user_id, update.message.text, "Telegram")
            await update.message.reply_text(res)
            return

    except Exception as e:
        logger.error(f"Error Telegram: {e}")
        if update.message:
            await update.message.reply_text(f"Error interno: {e}")


# =========================
# LIFECYCLE
# =========================
async def telegram_startup() -> None:
    global tg_app

    if not BOT_TOKEN:
        return

    try:
        tg_app = ApplicationBuilder().token(BOT_TOKEN).build()
        tg_app.add_handler(CommandHandler("start", tg_start))
        tg_app.add_handler(CommandHandler("status", tg_status))
        tg_app.add_handler(CommandHandler("reset", tg_reset))
        tg_app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_telegram))

        await tg_app.initialize()
        await tg_app.start()

        if BASE_URL:
            await tg_app.bot.set_webhook(url=f"{BASE_URL}/tg/{BOT_TOKEN}")

        logger.info("✅ Telegram activo")
    except Exception as e:
        logger.warning(f"⚠️ Telegram no pudo iniciar: {e}")
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
    except Exception as e:
        logger.warning(f"⚠️ Error apagando Telegram: {e}")
    finally:
        tg_app = None


# =========================
# WEBHOOK HANDLER
# =========================
async def telegram_webhook(token: str, request: Request) -> dict | Response:
    if not BOT_TOKEN or token != BOT_TOKEN:
        return Response(status_code=403)
    if tg_app is None:
        return Response(status_code=503)

    data = await request.json()
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return {"ok": True}
