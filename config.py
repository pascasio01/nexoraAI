import logging
import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("Nexora")


def _as_int(name: str, default: int = 0) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        return int(raw)
    except (TypeError, ValueError):
        logger.warning("Invalid %s=%r, using %s", name, raw, default)
        return default


def _clean_optional(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


OPENAI_API_KEY = _clean_optional(os.getenv("OPENAI_API_KEY"))
BOT_TOKEN = _clean_optional(os.getenv("BOT_TOKEN"))
REDIS_URL = _clean_optional(os.getenv("REDIS_URL"))
OWNER_ID = _as_int("OWNER_ID", 0)
BASE_URL = (_clean_optional(os.getenv("BASE_URL", "https://nexoraai-production.up.railway.app")) or "").rstrip("/")
TAVILY_API_KEY = _clean_optional(os.getenv("TAVILY_API_KEY"))
ACTION_WEBHOOK_URL = _clean_optional(os.getenv("ACTION_WEBHOOK_URL"))

MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o").strip() or "gpt-4o"
APP_NAME = os.getenv("APP_NAME", "Nexora").strip() or "Nexora"
CREATOR_NAME = os.getenv("CREATOR_NAME", "Pascasio Emmanuel Reynoso Reyes").strip() or "Pascasio Emmanuel Reynoso Reyes"
CREATOR_ALIAS = os.getenv("CREATOR_ALIAS", "Emmanuel Reynoso").strip() or "Emmanuel Reynoso"

MAX_CHAT_HISTORY = _as_int("MAX_CHAT_HISTORY", 12)
RATE_LIMIT_PER_MINUTE = _as_int("RATE_LIMIT_PER_MINUTE", 8)
PROFILE_MAX_LENGTH = _as_int("PROFILE_MAX_LENGTH", 1000)

if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY is not configured. AI responses will use fallback mode.")
if not BOT_TOKEN:
    logger.warning("BOT_TOKEN is not configured. Telegram actor is disabled.")
if not REDIS_URL:
    logger.warning("REDIS_URL is not configured. Using in-memory memory store.")
if not BASE_URL:
    logger.warning("BASE_URL is not configured. Telegram webhook registration is disabled.")
if not TAVILY_API_KEY:
    logger.warning("TAVILY_API_KEY is not configured. Web search tool is disabled.")
