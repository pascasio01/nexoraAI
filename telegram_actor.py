from fastapi import Request, Response
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from ai_core import ask_nexora
from config import APP_NAME, BASE_URL, BOT_TOKEN, MODEL_NAME, OWNER_ID, logger
from memory import redis_healthcheck, reset_memory

tg_app = None


def _allowed(user_id: int | None) -> bool:
    if OWNER_ID <= 0:
        return True
    return user_id == OWNER_ID


async def tg_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _allowed(update.effective_user.id if update.effective_user else None):
        return
    if update.message:
        await update.message.reply_text(f"✅ {APP_NAME} is active.")


async def tg_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _allowed(update.effective_user.id if update.effective_user else None):
        return
    if not update.message:
        return
    redis_ok = await redis_healthcheck()
    await update.message.reply_text(
        "\n".join(
            [
                "Status: active",
                f"Model: {MODEL_NAME}",
                f"Redis: {'on' if redis_ok else 'off'}",
            ]
        )
    )


async def tg_reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _allowed(update.effective_user.id if update.effective_user else None):
        return
    if update.effective_user:
        await reset_memory(str(update.effective_user.id))
    if update.message:
        await update.message.reply_text("Memory reset.")


async def handle_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _allowed(update.effective_user.id if update.effective_user else None):
        return
    if update.message and update.message.text and update.effective_user:
        reply = await ask_nexora(str(update.effective_user.id), update.message.text, "telegram")
        await update.message.reply_text(reply)


async def telegram_startup() -> None:
    global tg_app
    token = (BOT_TOKEN or "").strip()
    base_url = (BASE_URL or "").strip().rstrip("/")

    if not token:
        logger.warning("BOT_TOKEN is missing. Telegram integration is disabled.")
        return

    try:
        tg_app = ApplicationBuilder().token(token).build()
        tg_app.add_handler(CommandHandler("start", tg_start))
        tg_app.add_handler(CommandHandler("status", tg_status))
        tg_app.add_handler(CommandHandler("reset", tg_reset))
        tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_telegram))
        await tg_app.initialize()
        await tg_app.start()
    except Exception as exc:
        logger.warning("Telegram startup failed: %s", exc)
        tg_app = None
        return

    if not base_url:
        logger.warning("BASE_URL is missing. Telegram webhook was not configured.")
        return
    if not (base_url.startswith("http://") or base_url.startswith("https://")):
        logger.warning("BASE_URL is invalid for webhook setup: %s", base_url)
        return

    try:
        await tg_app.bot.set_webhook(url=f"{base_url}/tg/{token}")
    except Exception as exc:
        logger.warning("Failed to set Telegram webhook: %s", exc)


async def telegram_shutdown() -> None:
    global tg_app
    if tg_app is None:
        return

    try:
        await tg_app.bot.delete_webhook()
    except Exception as exc:
        logger.warning("Failed to delete Telegram webhook: %s", exc)

    try:
        await tg_app.stop()
        await tg_app.shutdown()
    except Exception as exc:
        logger.warning("Telegram shutdown failed: %s", exc)
    finally:
        tg_app = None


async def telegram_webhook(token: str, request: Request):
    safe_token = (BOT_TOKEN or "").strip()
    if not safe_token or token != safe_token:
        return Response(status_code=403)
    if tg_app is None:
        return Response(status_code=503)

    data = await request.json()
    await tg_app.process_update(Update.de_json(data, tg_app.bot))
    return {"ok": True}


def telegram_is_running() -> bool:
    return tg_app is not None
