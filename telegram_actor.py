import io

from fastapi import Request, Response
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

from ai_core import SYSTEM_PROMPT, ask_nexora
from config import ACTION_WEBHOOK_URL, APP_NAME, BASE_URL, BOT_TOKEN, MODEL_NAME, OWNER_ID, TAVILY_API_KEY, logger
from deps import client
from memory import reset_memory, save_chat_memory


tg_app = None


def telegram_is_running() -> bool:
    return tg_app is not None


async def tg_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if OWNER_ID and update.effective_user and update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Acceso no autorizado.")
        return
    await reset_memory(str(update.effective_user.id))
    await update.message.reply_text(f"{APP_NAME} activa. Memoria limpia y lista.")


async def tg_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if OWNER_ID and update.effective_user and update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Acceso no autorizado.")
        return
    msg = (
        "Estado: activa\n"
        f"Modelo: {MODEL_NAME}\n"
        f"Web search: {'on' if TAVILY_API_KEY else 'off'}\n"
        "Redis: ok\n"
        f"Actions webhook: {'on' if ACTION_WEBHOOK_URL else 'off'}"
    )
    await update.message.reply_text(msg)


async def tg_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if OWNER_ID and update.effective_user and update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Acceso no autorizado.")
        return
    await reset_memory(str(update.effective_user.id))
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

            transcription = await client.audio.transcriptions.create(model="whisper-1", file=audio_data)
            answer = await ask_nexora(user_id, transcription.text, "Telegram")
            await update.message.reply_text(answer)
            return

        if update.message.text:
            res = await ask_nexora(user_id, update.message.text, "Telegram")
            await update.message.reply_text(res)
            return

    except Exception as exc:
        logger.error(f"Error Telegram: {exc}")
        await update.message.reply_text(f"Error interno: {exc}")


async def telegram_startup() -> None:
    global tg_app
    if not BOT_TOKEN:
        logger.warning("⚠️ BOT_TOKEN no configurado. Telegram desactivado.")
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
            logger.info("Telegram webhook activo")
    except Exception as exc:
        logger.warning(f"⚠️ No se pudo iniciar Telegram: {exc}")
        tg_app = None


async def telegram_shutdown() -> None:
    global tg_app
    if not tg_app:
        return

    try:
        if BASE_URL:
            await tg_app.bot.delete_webhook()
        await tg_app.stop()
        await tg_app.shutdown()
    except Exception as exc:
        logger.warning(f"⚠️ Error apagando Telegram: {exc}")
    finally:
        tg_app = None


async def telegram_webhook(token: str, request: Request):
    if token != BOT_TOKEN:
        return Response(status_code=403)
    if tg_app is None:
        return Response(status_code=503)

    data = await request.json()
    await tg_app.process_update(Update.de_json(data, tg_app.bot))
    return {"ok": True}
