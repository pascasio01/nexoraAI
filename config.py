import logging
import os

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Nexora")


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name, default)
    if isinstance(value, str):
        value = value.strip()
    return value


OPENAI_API_KEY = _env("OPENAI_API_KEY")
REDIS_URL = _env("REDIS_URL")
BOT_TOKEN = _env("BOT_TOKEN")
BASE_URL = (_env("BASE_URL", "") or "").rstrip("/")
TAVILY_API_KEY = _env("TAVILY_API_KEY")
ACTION_WEBHOOK_URL = _env("ACTION_WEBHOOK_URL")
MODEL_NAME = _env("MODEL_NAME", "gpt-4o") or "gpt-4o"
APP_NAME = _env("APP_NAME", "Nexora") or "Nexora"

_owner_id_raw = _env("OWNER_ID", "0") or "0"
OWNER_ID = int(_owner_id_raw) if _owner_id_raw.isdigit() else 0
