import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _as_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Nexora")
    base_url: str = os.getenv("BASE_URL", "").rstrip("/")
    model_name: str = os.getenv("MODEL_NAME", "gpt-4o")

    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    redis_url: str | None = os.getenv("REDIS_URL")
    tavily_api_key: str | None = os.getenv("TAVILY_API_KEY")
    bot_token: str | None = os.getenv("BOT_TOKEN")
    action_webhook_url: str | None = os.getenv("ACTION_WEBHOOK_URL")

    owner_id: int = _as_int("OWNER_ID", 0)
    max_chat_history: int = _as_int("MAX_CHAT_HISTORY", 12)
    rate_limit_per_minute: int = _as_int("RATE_LIMIT_PER_MINUTE", 8)

    creator_name: str = os.getenv("CREATOR_NAME", "Pascasio Emmanuel Reynoso Reyes")
    creator_alias: str = os.getenv("CREATOR_ALIAS", "Emmanuel Reynoso")


settings = Settings()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("Nexora")

# Backward-compatible names
APP_NAME = settings.app_name
BASE_URL = settings.base_url
MODEL_NAME = settings.model_name
OPENAI_API_KEY = settings.openai_api_key
REDIS_URL = settings.redis_url
TAVILY_API_KEY = settings.tavily_api_key
BOT_TOKEN = settings.bot_token
ACTION_WEBHOOK_URL = settings.action_webhook_url
OWNER_ID = settings.owner_id
MAX_CHAT_HISTORY = settings.max_chat_history
RATE_LIMIT_PER_MINUTE = settings.rate_limit_per_minute
CREATOR_NAME = settings.creator_name
CREATOR_ALIAS = settings.creator_alias
