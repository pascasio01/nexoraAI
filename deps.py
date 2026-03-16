"""Shared dependency clients with graceful optional fallbacks."""

from __future__ import annotations

from openai import AsyncOpenAI
import redis.asyncio as redis
from tavily import TavilyClient

from config import OPENAI_API_KEY, REDIS_URL, TAVILY_API_KEY, logger

openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
redis_client = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None
tavily_client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None

if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY not configured. AI responses use fallback mode.")
if not REDIS_URL:
    logger.warning("REDIS_URL not configured. In-memory store fallback enabled.")
if not TAVILY_API_KEY:
    logger.warning("TAVILY_API_KEY not configured. Web search tool will be limited.")
