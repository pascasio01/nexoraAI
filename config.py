"""Application configuration and logging."""

from __future__ import annotations

import logging
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("Nexora")

APP_NAME = os.getenv("APP_NAME", "Nexora")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")
BASE_URL = os.getenv("BASE_URL", "").rstrip("/")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
REDIS_URL = os.getenv("REDIS_URL")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", BOT_TOKEN or "")
ACTION_WEBHOOK_URL = os.getenv("ACTION_WEBHOOK_URL")

CREATOR_NAME = os.getenv("CREATOR_NAME", "Pascasio Emmanuel Reynoso Reyes")
CREATOR_ALIAS = os.getenv("CREATOR_ALIAS", "Emmanuel Reynoso")

MAX_CHAT_HISTORY = int(os.getenv("MAX_CHAT_HISTORY", "12"))
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "12"))
DEFAULT_CHANNEL = os.getenv("DEFAULT_CHANNEL", "web")
