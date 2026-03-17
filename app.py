import json
import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from openai import AsyncOpenAI
import redis.asyncio as redis
from tavily import TavilyClient
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("Nexora")

# =========================
# ENV
# =========================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
REDIS_URL = os.getenv("REDIS_URL")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
BASE_URL = os.getenv("BASE_URL", "https://nexoraai-production.up.railway.app").rstrip("/")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")
APP_NAME = os.getenv("APP_NAME", "Nexora")
MAX_CHAT_HISTORY = int(os.getenv("MAX_CHAT_HISTORY", "12"))
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "8"))

client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
r = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None
tavily = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None

app = FastAPI(title=f"{APP_NAME} AI OS")
tg_app = None


async def check_rate_limit(user_id: str) -> bool:
    if r is None:
        return True
    try:
        key = f"rate_limit:{user_id}"
        count = await r.incr(key)
        if count == 1:
            await r.expire(key, 60)
        return count <= RATE_LIMIT_PER_MINUTE
    except Exception as exc:
        logger.warning(f"Rate limit desactivado por error Redis: {exc}")
        return True


async def save_chat_memory(user_id: str, role: str, content: str) -> None:
    if r is None:
        return
    await r.rpush(f"chat:{user_id}", json.dumps({"role": role, "content": content}))
    await r.ltrim(f"chat:{user_id}", -MAX_CHAT_HISTORY, -1)


async def load_chat_memory(user_id: str):
    if r is None:
        return []
    history_raw = await r.lrange(f"chat:{user_id}", 0, -1)
    return [json.loads(item) for item in history_raw]


async def reset_memory(user_id: str) -> None:
    if r is None:
        return
    await r.delete(f"chat:{user_id}")


async def ask_nexora(user_id: str, text: str) -> str:
    if client is None:
        return "⚠️ OpenAI no está configurado ahora mismo."

    if not await check_rate_limit(user_id):
        return "⚠️ Límite de mensajes alcanzado. Espera un minuto."

    history = await load_chat_memory(user_id)
    response = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=history + [{"role": "user", "content": text}],
        max_tokens=500,
    )
    answer = response.choices[0].message.content or "No pude generar respuesta."

    await save_chat_memory(user_id, "user", text)
    await save_chat_memory(user_id, "assistant", answer)
    return answer


async def tg_start(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    if OWNER_ID and update.effective_user and update.effective_user.id != OWNER_ID:
        return
    if update.message:
        await update.message.reply_text("✅ Nexora está activa.")


async def tg_status(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    if OWNER_ID and update.effective_user and update.effective_user.id != OWNER_ID:
        return
    if update.message:
        await update.message.reply_text("Nexora status: activa.")


async def tg_reset(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    if OWNER_ID and update.effective_user and update.effective_user.id != OWNER_ID:
        return
    if update.effective_user:
        await reset_memory(str(update.effective_user.id))
    if update.message:
        await update.message.reply_text("Memoria reiniciada.")


async def handle_telegram(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    if OWNER_ID and update.effective_user and update.effective_user.id != OWNER_ID:
        return
    if update.message and update.message.text and update.effective_user:
        reply = await ask_nexora(str(update.effective_user.id), update.message.text)
        await update.message.reply_text(reply)


@app.on_event("startup")
async def startup():
    global r, tg_app

    if r is not None:
        try:
            await r.ping()
            logger.info("✅ Redis conectado")
        except Exception as exc:
            logger.warning(f"⚠️ Redis no disponible al startup: {exc}")
            r = None

    if BOT_TOKEN:
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
        except Exception as exc:
            logger.warning(f"⚠️ Telegram no pudo iniciar: {exc}")
            tg_app = None


@app.on_event("shutdown")
async def shutdown():
    global tg_app, r

    try:
        if tg_app:
            if BASE_URL:
                await tg_app.bot.delete_webhook()
            await tg_app.stop()
            await tg_app.shutdown()
    except Exception as exc:
        logger.warning(f"⚠️ Error apagando Telegram: {exc}")

    try:
        if r:
            await r.close()
    except Exception as exc:
        logger.warning(f"⚠️ Error cerrando Redis: {exc}")


@app.get("/")
async def home():
    return {"app": APP_NAME, "status": "online", "model": MODEL_NAME}


@app.get("/health")
async def health():
    redis_ok = False
    try:
        if r:
            await r.ping()
            redis_ok = True
    except Exception:
        redis_ok = False

    return {
        "status": "ok",
        "redis": redis_ok,
        "openai": client is not None,
        "tavily": tavily is not None,
        "telegram": tg_app is not None,
    }


@app.post("/tg/{token}")
async def tg_webhook(token: str, request: Request):
    if not BOT_TOKEN or token != BOT_TOKEN:
        return {"ok": False, "error": "token inválido"}

    if tg_app is None:
        return {"ok": False, "error": "telegram no iniciado"}

    data = await request.json()
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return {"ok": True}
