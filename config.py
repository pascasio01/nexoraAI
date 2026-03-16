import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _to_int(value: str | None, default: int) -> int:
    try:
        return int(value) if value is not None else default
    except (TypeError, ValueError):
        return default


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("Nexora")


@dataclass(frozen=True)
class Settings:
    app_name: str
    model_name: str
    creator_name: str
    creator_alias: str
    openai_api_key: str | None
    redis_url: str | None
    tavily_api_key: str | None
    bot_token: str | None
    base_url: str | None
    action_webhook_url: str | None
    owner_id: int
    max_chat_history: int
    rate_limit_per_minute: int

    @classmethod
    def from_env(cls) -> "Settings":
        base_url = os.getenv("BASE_URL", "").strip().rstrip("/")
        return cls(
            app_name=os.getenv("APP_NAME", "Nexora"),
            model_name=os.getenv("MODEL_NAME", "gpt-4o"),
            creator_name=os.getenv("CREATOR_NAME", "Pascasio Emmanuel Reynoso Reyes"),
            creator_alias=os.getenv("CREATOR_ALIAS", "Emmanuel Reynoso"),
            openai_api_key=os.getenv("OPENAI_API_KEY") or None,
            redis_url=os.getenv("REDIS_URL") or None,
            tavily_api_key=os.getenv("TAVILY_API_KEY") or None,
            bot_token=os.getenv("BOT_TOKEN") or None,
            base_url=base_url or None,
            action_webhook_url=os.getenv("ACTION_WEBHOOK_URL") or None,
            owner_id=_to_int(os.getenv("OWNER_ID"), 0),
            max_chat_history=_to_int(os.getenv("MAX_CHAT_HISTORY"), 12),
            rate_limit_per_minute=_to_int(os.getenv("RATE_LIMIT_PER_MINUTE"), 8),
        )


settings = Settings.from_env()
