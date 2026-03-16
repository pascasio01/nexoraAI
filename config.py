import logging
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Nexora")
    model_name: str = os.getenv("MODEL_NAME", "gpt-4o-mini")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    redis_url: str | None = os.getenv("REDIS_URL")
    tavily_api_key: str | None = os.getenv("TAVILY_API_KEY")
    action_webhook_url: str | None = os.getenv("ACTION_WEBHOOK_URL")
    bot_token: str | None = os.getenv("BOT_TOKEN")
    telegram_webhook_secret: str = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
    max_chat_history: int = int(os.getenv("MAX_CHAT_HISTORY", "20"))


settings = Settings()

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("Nexora")
