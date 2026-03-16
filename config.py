import logging
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("Nexora")

APP_NAME = os.getenv("APP_NAME", "Nexora")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")
CREATOR_NAME = os.getenv("CREATOR_NAME", "Pascasio Emmanuel Reynoso Reyes")
CREATOR_ALIAS = os.getenv("CREATOR_ALIAS", "Emmanuel Reynoso")
BASE_URL = os.getenv("BASE_URL", "").rstrip("/")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
REDIS_URL = os.getenv("REDIS_URL")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ACTION_WEBHOOK_URL = os.getenv("ACTION_WEBHOOK_URL")
_OWNER_ID_RAW = os.getenv("OWNER_ID", "0")
OWNER_ID = int(_OWNER_ID_RAW) if _OWNER_ID_RAW.isdigit() else 0

MAX_CHAT_HISTORY = int(os.getenv("MAX_CHAT_HISTORY", "12"))
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "8"))
AUTH_SIGNING_KEY = os.getenv("AUTH_SIGNING_KEY", "")
AUTH_TOKEN_MAX_AGE_SECONDS = int(os.getenv("AUTH_TOKEN_MAX_AGE_SECONDS", str(30 * 24 * 3600)))
