import redis.asyncio as redis
from openai import AsyncOpenAI
from tavily import TavilyClient

from config import OPENAI_API_KEY, REDIS_URL, TAVILY_API_KEY, logger

client = None
r = None
tavily = None

if OPENAI_API_KEY:
    try:
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    except Exception as exc:
        logger.warning("OpenAI disabled: %s", exc)
else:
    logger.warning("OPENAI_API_KEY missing; OpenAI features disabled.")

if REDIS_URL:
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
    except Exception as exc:
        logger.warning("Redis disabled: %s", exc)
else:
    logger.warning("REDIS_URL missing; memory features disabled.")

if TAVILY_API_KEY:
    try:
        tavily = TavilyClient(api_key=TAVILY_API_KEY)
    except Exception as exc:
        logger.warning("Tavily disabled: %s", exc)
else:
    logger.warning("TAVILY_API_KEY missing; web search disabled.")


async def close_deps() -> None:
    if r is not None:
        try:
            await r.aclose()
        except Exception as exc:
            logger.warning("Redis close warning: %s", exc)
