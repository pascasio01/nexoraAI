"""Telegram lifecycle and handlers using shared AI core."""

from __future__ import annotations

from fastapi import Request
from telegram import Update
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

from config import APP_NAME, BASE_URL, BOT_TOKEN, TELEGRAM_WEBHOOK_SECRET, logger


class TelegramActor:
    """Wrap Telegram startup/shutdown and webhook processing."""

    def __init__(self, ai_core) -> None:
        self.ai_core = ai_core
        self.app: Application | None = None

    @property
    def is_enabled(self) -> bool:
        return bool(BOT_TOKEN)

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(f"{APP_NAME} conectado.")

    async def _on_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.message or not update.effective_user:
            return
        user_id = str(update.effective_user.id)
        text = update.message.text or ""
        reply = await self.ai_core.ask(user_id=user_id, session_id="telegram", text=text, channel="telegram")
        await update.message.reply_text(reply)

    async def startup(self) -> None:
        if not self.is_enabled:
            logger.info("Telegram disabled: BOT_TOKEN missing.")
            return

        try:
            self.app = ApplicationBuilder().token(BOT_TOKEN).build()
            self.app.add_handler(CommandHandler("start", self._cmd_start))
            self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._on_message))
            await self.app.initialize()
            await self.app.start()

            if BASE_URL:
                await self.app.bot.set_webhook(url=f"{BASE_URL}/tg/{TELEGRAM_WEBHOOK_SECRET}")
        except Exception as exc:
            logger.warning("Telegram startup failed, continuing without Telegram: %s", exc)
            self.app = None

    async def shutdown(self) -> None:
        if not self.app:
            return
        try:
            if BASE_URL:
                await self.app.bot.delete_webhook()
            await self.app.stop()
            await self.app.shutdown()
        except Exception as exc:
            logger.warning("Telegram shutdown error: %s", exc)
        finally:
            self.app = None

    async def webhook(self, token: str, request: Request) -> None:
        if not self.app or token != TELEGRAM_WEBHOOK_SECRET:
            return
        payload = await request.json()
        update = Update.de_json(payload, self.app.bot)
        await self.app.process_update(update)
