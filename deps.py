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
        logger.warning(f"⚠️ No se pudo inicializar OpenAI: {exc}")
else:
    logger.warning("⚠️ OPENAI_API_KEY no configurada. IA desactivada.")

if REDIS_URL:
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
    except Exception as exc:
        logger.warning(f"⚠️ No se pudo inicializar Redis: {exc}")
else:
    logger.warning("⚠️ REDIS_URL no configurada. Memoria desactivada.")

if TAVILY_API_KEY:
    try:
        tavily = TavilyClient(api_key=TAVILY_API_KEY)
    except Exception as exc:
        logger.warning(f"⚠️ No se pudo inicializar Tavily: {exc}")
else:
    logger.warning("⚠️ TAVILY_API_KEY no configurada. Búsqueda web desactivada.")
