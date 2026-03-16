import redis.asyncio as redis
from openai import AsyncOpenAI
from tavily import TavilyClient

from config import OPENAI_API_KEY, REDIS_URL, TAVILY_API_KEY, logger

client = None
r = None
tavily = None


async def init_services() -> None:
    global client, r, tavily

    if OPENAI_API_KEY:
        try:
            client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        except Exception as exc:
            logger.warning(f"OpenAI init failed: {exc}")
            client = None
    else:
        logger.warning("OPENAI_API_KEY not configured. Chat generation disabled.")

    if REDIS_URL:
        try:
            r = redis.from_url(REDIS_URL, decode_responses=True)
            await r.ping()
        except Exception as exc:
            logger.warning(f"Redis init failed: {exc}")
            r = None
    else:
        logger.warning("REDIS_URL not configured. Using in-memory fallback.")

    if TAVILY_API_KEY:
        try:
            tavily = TavilyClient(api_key=TAVILY_API_KEY)
        except Exception as exc:
            logger.warning(f"Tavily init failed: {exc}")
            tavily = None
    else:
        logger.warning("TAVILY_API_KEY not configured. Web search disabled.")


async def close_services() -> None:
    global r
    if r is not None:
        try:
            await r.aclose()
        except Exception as exc:
            logger.warning(f"Redis close failed: {exc}")


async def redis_healthy() -> bool:
    if r is None:
        return False
    try:
        await r.ping()
        return True
    except Exception:
        return False


def service_flags() -> dict:
    return {
        "openai": client is not None,
        "redis": r is not None,
        "tavily": tavily is not None,
    }
