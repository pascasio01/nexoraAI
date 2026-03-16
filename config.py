import os
import logging
from dotenv import load_dotenv

from openai import AsyncOpenAI
import redis.asyncio as redis
from tavily import TavilyClient

load_dotenv()

# =========================
# LOGS
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("Nexora")

# =========================
# ENV VARS
# =========================
APP_NAME = os.getenv("APP_NAME", "Nexora")
BASE_URL = os.getenv("BASE_URL", "").rstrip("/")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
REDIS_URL = os.getenv("REDIS_URL")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")

OWNER_ID_RAW = os.getenv("OWNER_ID", "0")
OWNER_ID = int(OWNER_ID_RAW) if OWNER_ID_RAW.isdigit() else 0

ACTION_WEBHOOK_URL = os.getenv("ACTION_WEBHOOK_URL")
CREATOR_NAME = os.getenv("CREATOR_NAME", "Pascasio Emmanuel Reynoso Reyes")
CREATOR_ALIAS = os.getenv("CREATOR_ALIAS", "Emmanuel Reynoso")

MAX_CHAT_HISTORY = int(os.getenv("MAX_CHAT_HISTORY", "12"))
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "8"))

# =========================
# SHARED CLIENTS
# =========================
client = None
r = None
tavily = None

if not OPENAI_API_KEY:
    logger.warning("⚠️ OPENAI_API_KEY no configurada. IA desactivada.")
else:
    try:
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    except Exception as _e:
        logger.warning(f"⚠️ No se pudo inicializar OpenAI: {_e}")

if not REDIS_URL:
    logger.warning("⚠️ REDIS_URL no configurada. Memoria desactivada.")
else:
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
    except Exception as _e:
        logger.warning(f"⚠️ No se pudo inicializar Redis: {_e}")

if not TAVILY_API_KEY:
    logger.warning("⚠️ TAVILY_API_KEY no configurada. Búsqueda web desactivada.")
else:
    try:
        tavily = TavilyClient(api_key=TAVILY_API_KEY)
    except Exception as _e:
        logger.warning(f"⚠️ No se pudo inicializar Tavily: {_e}")

if not BOT_TOKEN:
    logger.warning("⚠️ BOT_TOKEN no configurado. Telegram desactivado.")
