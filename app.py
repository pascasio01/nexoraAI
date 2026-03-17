import json
import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from openai import AsyncOpenAI
from pydantic import BaseModel
import redis.asyncio as redis
from tavily import TavilyClient
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("Nexora")

APP_NAME = os.getenv("APP_NAME", "Nexora")
BASE_URL = os.getenv("BASE_URL", "https://nexoraai-production.up.railway.app").rstrip("/")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
REDIS_URL = os.getenv("REDIS_URL")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")

OWNER_ID_RAW = os.getenv("OWNER_ID", "0")
OWNER_ID = int(OWNER_ID_RAW) if OWNER_ID_RAW.isdigit() else 0

client = None
r = None
tavily = None
tg_app = None

if OPENAI_API_KEY:
    try:
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:
        logger.warning(f"⚠️ No se pudo inicializar OpenAI: {e}")
else:
    logger.warning("⚠️ OPENAI_API_KEY no configurada. IA desactivada.")

if REDIS_URL:
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
    except Exception as e:
        logger.warning(f"⚠️ No se pudo inicializar Redis: {e}")
else:
    logger.warning("⚠️ REDIS_URL no configurada. Memoria desactivada.")

if TAVILY_API_KEY:
    try:
        tavily = TavilyClient(api_key=TAVILY_API_KEY)
    except Exception as e:
        logger.warning(f"⚠️ No se pudo inicializar Tavily: {e}")

if not BOT_TOKEN:
    logger.warning("⚠️ BOT_TOKEN no configurado. Telegram desactivado.")

app = FastAPI(title=APP_NAME)


class ChatRequest(BaseModel):
    texto: str
    usuario: str | None = "web_user"


async def save_chat_memory(user_id: str, role: str, content: str) -> None:
    if r is None:
        return
    try:
        await r.rpush(f"chat:{user_id}", json.dumps({"role": role, "content": content}))
        await r.ltrim(f"chat:{user_id}", -12, -1)
    except Exception as e:
        logger.warning(f"No se pudo guardar memoria: {e}")


async def load_chat_memory(user_id: str) -> list[dict]:
    if r is None:
        return []
    try:
        history_raw = await r.lrange(f"chat:{user_id}", 0, -1)
        return [json.loads(m) for m in history_raw]
    except Exception as e:
        logger.warning(f"No se pudo cargar memoria: {e}")
        return []


async def ask_nexora(user_id: str, text: str) -> str:
    if client is None:
        return "⚠️ OpenAI no está configurado ahora mismo."

    history = await load_chat_memory(user_id)
    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=history + [{"role": "user", "content": text}],
            max_tokens=500,
        )
        answer = response.choices[0].message.content or "No pude generar respuesta."
    except Exception as e:
        logger.error(f"Error OpenAI: {e}")
        return "⚠️ Hubo un problema generando la respuesta."

    await save_chat_memory(user_id, "user", text)
    await save_chat_memory(user_id, "assistant", answer)
    return answer


async def tg_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if OWNER_ID and update.effective_user and update.effective_user.id != OWNER_ID:
        return
    if update.message:
        await update.message.reply_text("✅ Nexora está activa.")


async def handle_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if OWNER_ID and update.effective_user and update.effective_user.id != OWNER_ID:
        return
    if update.message and update.message.text:
        if not update.effective_user:
            logger.warning("Mensaje de Telegram sin usuario efectivo; se ignora.")
            return
        user_id = str(update.effective_user.id)
        reply = await ask_nexora(user_id, update.message.text)
        await update.message.reply_text(reply)


@app.on_event("startup")
async def startup():
    global r, tg_app

    if r is not None:
        try:
            await r.ping()
            logger.info("✅ Redis conectado")
        except Exception as e:
            logger.warning(f"⚠️ Redis no disponible al startup: {e}")
            r = None

    if BOT_TOKEN:
        try:
            tg_app = ApplicationBuilder().token(BOT_TOKEN).build()
            tg_app.add_handler(CommandHandler("start", tg_start))
            tg_app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_telegram))

            await tg_app.initialize()
            await tg_app.start()

            if BASE_URL:
                await tg_app.bot.set_webhook(url=f"{BASE_URL}/tg/{BOT_TOKEN}")

            logger.info("✅ Telegram activo")
        except Exception as e:
            logger.warning(f"⚠️ Telegram no pudo iniciar: {e}")
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
    except Exception as e:
        logger.warning(f"⚠️ Error apagando Telegram: {e}")

    try:
        if r:
            await r.close()
    except Exception as e:
        logger.warning(f"⚠️ Error cerrando Redis: {e}")


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


@app.post("/chat")
async def chat(req: ChatRequest):
    user_id = req.usuario or "web_user"
    answer = await ask_nexora(user_id, req.texto)
    return {"respuesta": answer}


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
