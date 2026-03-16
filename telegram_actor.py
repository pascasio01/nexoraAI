from __future__ import annotations

import json

from fastapi import Request, Response

from ai_core import ask_nexora
from config import logger, settings
from memory import reset_memory

try:
    from telegram import Update
    from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
except Exception as exc:  # pragma: no cover
    Update = None
    ApplicationBuilder = None
    CommandHandler = None
    ContextTypes = None
    MessageHandler = None
    filters = None
    logger.warning("python-telegram-bot no disponible, Telegram desactivado: %s", exc)

_tg_app = None
_telegram_enabled = False


def telegram_is_active() -> bool:
    return bool(_telegram_enabled and _tg_app is not None)


async def _tg_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if settings.owner_id and update.effective_user.id != settings.owner_id:
        await update.message.reply_text("Acceso no autorizado.")
        return
    await reset_memory(str(update.effective_user.id))
    await update.message.reply_text(f"{settings.app_name} activa y lista.")


async def _tg_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if settings.owner_id and update.effective_user.id != settings.owner_id:
        await update.message.reply_text("Acceso no autorizado.")
        return
    status = "activa" if telegram_is_active() else "desactivada"
    await update.message.reply_text(f"Telegram {status}. Modelo: {settings.model_name}")


async def _tg_reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if settings.owner_id and update.effective_user.id != settings.owner_id:
        await update.message.reply_text("Acceso no autorizado.")
        return
    await reset_memory(str(update.effective_user.id))
    await update.message.reply_text("Memoria reiniciada.")


async def _tg_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    if settings.owner_id and update.effective_user.id != settings.owner_id:
        return

    user_id = str(update.effective_user.id)
    text = update.message.text or ""
    answer = await ask_nexora(user_id=user_id, text=text, channel="telegram")
    await update.message.reply_text(answer)


async def telegram_startup() -> None:
    global _tg_app, _telegram_enabled

    if ApplicationBuilder is None:
        _telegram_enabled = False
        return

    if not settings.bot_token:
        logger.warning("BOT_TOKEN ausente. Telegram desactivado de forma segura.")
        _telegram_enabled = False
        return

    if not settings.base_url:
        logger.warning("BASE_URL ausente o inválido. Telegram desactivado de forma segura.")
        _telegram_enabled = False
        return

    try:
        _tg_app = ApplicationBuilder().token(settings.bot_token).build()
        _tg_app.add_handler(CommandHandler("start", _tg_start))
        _tg_app.add_handler(CommandHandler("status", _tg_status))
        _tg_app.add_handler(CommandHandler("reset", _tg_reset))
        _tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _tg_message))

        await _tg_app.initialize()
        await _tg_app.start()
        await _tg_app.bot.set_webhook(url=f"{settings.base_url}/tg/{settings.bot_token}")
        _telegram_enabled = True
        logger.info("Telegram inicializado correctamente.")
    except Exception as exc:
        logger.warning("No se pudo inicializar Telegram. Se mantiene desactivado: %s", exc)
        _telegram_enabled = False
        _tg_app = None


async def telegram_shutdown() -> None:
    global _tg_app, _telegram_enabled
    if _tg_app is None:
        return

    try:
        await _tg_app.stop()
        await _tg_app.shutdown()
    except Exception as exc:
        logger.warning("Error en shutdown de Telegram: %s", exc)
    finally:
        _tg_app = None
        _telegram_enabled = False


async def telegram_webhook(token: str, request: Request) -> Response:
    if not settings.bot_token or token != settings.bot_token:
        return Response(status_code=403, content="Token inválido")
    if _tg_app is None:
        return Response(status_code=503, content="Telegram desactivado")

    try:
        data = await request.json()
        update = Update.de_json(data, _tg_app.bot)
        await _tg_app.process_update(update)
        return Response(status_code=200, content="ok")
    except json.JSONDecodeError:
        return Response(status_code=400, content="JSON inválido")
    except Exception as exc:
        logger.warning("Error procesando webhook de Telegram: %s", exc)
        return Response(status_code=500, content="error")
