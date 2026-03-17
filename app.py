import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from openai import AsyncOpenAI
import redis.asyncio as redis
from tavily import TavilyClient

load_dotenv()

# =========================
# LOGS
# =========================
logging.basicConfig(level=logging.INFO)
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
ACTION_WEBHOOK_URL = os.getenv("ACTION_WEBHOOK_URL")

MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")
APP_NAME = os.getenv("APP_NAME", "Nexora")
CREATOR_NAME = os.getenv("CREATOR_NAME", "Pascasio Emmanuel Reynoso Reyes")
CREATOR_ALIAS = os.getenv("CREATOR_ALIAS", "Emmanuel Reynoso")

MAX_CHAT_HISTORY = int(os.getenv("MAX_CHAT_HISTORY", "12"))
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "8"))

# =========================
# VALIDATION
# =========================
if not OPENAI_API_KEY:
    raise ValueError("Falta OPENAI_API_KEY")
if not BOT_TOKEN:
    raise ValueError("Falta BOT_TOKEN")
if not REDIS_URL:
    raise ValueError("Falta REDIS_URL")

client = AsyncOpenAI(api_key=OPENAI_API_KEY)
r = redis.from_url(REDIS_URL, decode_responses=True)
tavily = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None

app = FastAPI(title=f"{APP_NAME} AI OS")


@app.get("/")
async def home():
    return {"app": APP_NAME, "status": "online", "model": MODEL_NAME}


@app.get("/health")
async def health():
    redis_ok = False
    try:
        await r.ping()
        redis_ok = True
    except Exception as exc:
        logger.warning("Redis no disponible en healthcheck: %s", exc)

    return {
        "status": "ok",
        "redis": redis_ok,
        "openai": client is not None,
        "tavily": tavily is not None,
        "base_url": BASE_URL,
    }


@app.on_event("shutdown")
async def shutdown():
    try:
        await r.close()
    except Exception as exc:
        logger.warning("Error cerrando Redis: %s", exc)
