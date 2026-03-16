import hmac
import html
import logging
import os
import time
from contextlib import suppress

from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException, Request
from pydantic import AliasChoices, BaseModel, Field, field_validator

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

import redis.asyncio as redis
from openai import AsyncOpenAI
from tavily import TavilyClient

load_dotenv()

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("Nexora")

APP_NAME = os.getenv("APP_NAME", "Nexora")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")
BASE_URL = (os.getenv("BASE_URL") or "").rstrip("/")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
REDIS_URL = os.getenv("REDIS_URL")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

app = FastAPI(title=f"{APP_NAME} AI OS")


def _init_openai() -> AsyncOpenAI | None:
    if not OPENAI_API_KEY:
        return None
    try:
        return AsyncOpenAI(api_key=OPENAI_API_KEY)
    except Exception as exc:
        logger.warning("OpenAI client init failed: %s", exc)
        return None


def _init_tavily() -> TavilyClient | None:
    if not TAVILY_API_KEY:
        return None
    try:
        return TavilyClient(api_key=TAVILY_API_KEY)
    except Exception as exc:
        logger.warning("Tavily client init failed: %s", exc)
        return None


def _init_redis() -> redis.Redis | None:
    if not REDIS_URL:
        return None
    try:
        return redis.from_url(REDIS_URL, decode_responses=True)
    except Exception as exc:
        logger.warning("Redis client init failed: %s", exc)
        return None


client = _init_openai()
tavily = _init_tavily()
r = _init_redis()
tg_app = None
failed_webhook_attempts: dict[str, list[float]] = {}


class ChatRequest(BaseModel):
    """Chat payload using current English names and legacy Spanish aliases."""

    user_id: str = Field(validation_alias=AliasChoices("user_id", "usuario"))
    text: str = Field(validation_alias=AliasChoices("text", "texto"))

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("text is required")
        return value


async def tg_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Hola 👋 Soy {APP_NAME}.")


async def handle_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        try:
            safe_text = html.escape(update.message.text, quote=False)
            await update.message.reply_text(f"{APP_NAME}: {safe_text}")
        except Exception as exc:
            logger.warning("Telegram reply failed: %s", exc)


def _is_webhook_rate_limited(client_ip: str, window_seconds: int = 60, max_attempts: int = 30) -> bool:
    now = time.time()
    attempts = failed_webhook_attempts.get(client_ip, [])
    attempts = [attempt for attempt in attempts if now - attempt < window_seconds]
    failed_webhook_attempts[client_ip] = attempts
    return len(attempts) >= max_attempts


def _record_webhook_failure(client_ip: str) -> None:
    failed_webhook_attempts.setdefault(client_ip, []).append(time.time())


@app.on_event("startup")
async def startup() -> None:
    global tg_app, r

    if r is not None:
        try:
            await r.ping()
            logger.info("Redis connected")
        except Exception as exc:
            logger.warning("Redis unavailable at startup: %s", exc)
            r = None

    if not BOT_TOKEN:
        logger.warning("BOT_TOKEN missing: Telegram bot disabled")
        return

    try:
        tg_app = ApplicationBuilder().token(BOT_TOKEN).build()
        tg_app.add_handler(CommandHandler("start", tg_start))
        tg_app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_telegram))
        await tg_app.initialize()
        await tg_app.start()

        if BASE_URL:
            await tg_app.bot.set_webhook(url=f"{BASE_URL}/tg/{BOT_TOKEN}")
        logger.info("Telegram bot initialized")
    except Exception as exc:
        logger.warning("Telegram startup failed, continuing without Telegram: %s", exc)
        tg_app = None


@app.on_event("shutdown")
async def shutdown() -> None:
    if tg_app:
        with suppress(Exception):
            if BASE_URL:
                await tg_app.bot.delete_webhook()
            await tg_app.stop()
            await tg_app.shutdown()

    if r is not None:
        with suppress(Exception):
            await r.close()


@app.get("/")
async def home() -> dict:
    return {"app": APP_NAME, "status": "online", "model": MODEL_NAME}


@app.get("/health")
async def health() -> dict:
    redis_ok = False
    if r is not None:
        with suppress(Exception):
            await r.ping()
            redis_ok = True

    return {
        "status": "ok",
        "redis": redis_ok,
        "openai": client is not None,
        "tavily": tavily is not None,
        "telegram": tg_app is not None,
    }


@app.post("/chat")
async def chat(req: ChatRequest) -> dict:
    if client is None:
        return {"response": f"{APP_NAME} running (OPENAI_API_KEY not configured)."}

    return {"response": f"{APP_NAME}: {req.text}"}


@app.post("/reset-web")
async def reset_web(req: ChatRequest) -> dict:
    if r is None:
        return {"status": "ok", "reset": False, "reason": "redis unavailable"}

    with suppress(Exception):
        await r.delete(f"chat:{req.user_id}")
        return {"status": "ok", "reset": True}

    return {"status": "ok", "reset": False}


@app.post("/whatsapp")
async def whatsapp_webhook(Body: str = Form(...), From: str = Form(...)) -> dict:
    return {"reply": f"{APP_NAME}: {Body}", "from": From}


@app.post("/tg/{token}")
async def tg_webhook(token: str, request: Request) -> dict:
    client_ip = request.client.host if request.client else "unknown"
    if _is_webhook_rate_limited(client_ip):
        raise HTTPException(status_code=429, detail="too many requests")

    if not isinstance(BOT_TOKEN, str) or not BOT_TOKEN:
        _record_webhook_failure(client_ip)
        raise HTTPException(status_code=403, detail="invalid webhook token")

    if not hmac.compare_digest(token.encode(), BOT_TOKEN.encode()):
        _record_webhook_failure(client_ip)
        raise HTTPException(status_code=403, detail="invalid webhook token")

    if tg_app is None:
        raise HTTPException(status_code=503, detail="telegram is unavailable")

    payload = await request.json()
    update = Update.de_json(payload, tg_app.bot)
    await tg_app.process_update(update)
    return {"ok": True}
