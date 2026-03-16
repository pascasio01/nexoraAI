import logging
import os
from dotenv import load_dotenv

load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("Nexora")

APP_NAME = os.getenv("APP_NAME", "Nexora")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
REDIS_URL = os.getenv("REDIS_URL")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = os.getenv("BASE_URL", "").rstrip("/")
ACTION_WEBHOOK_URL = os.getenv("ACTION_WEBHOOK_URL")

OWNER_ID_RAW = os.getenv("OWNER_ID", "0")
_owner_id_int = int(OWNER_ID_RAW) if OWNER_ID_RAW.isdigit() else 0
OWNER_ID = _owner_id_int if _owner_id_int > 0 else None
ALLOW_ALL_USERS = os.getenv("ALLOW_ALL_USERS", "false").lower() in {"1", "true", "yes", "on"}

CREATOR_NAME = os.getenv("CREATOR_NAME", "Pascasio Emmanuel Reynoso Reyes")
CREATOR_ALIAS = os.getenv("CREATOR_ALIAS", "Emmanuel Reynoso")

MAX_CHAT_HISTORY = int(os.getenv("MAX_CHAT_HISTORY", "12"))
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "8"))
