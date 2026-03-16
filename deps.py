from openai import AsyncOpenAI

from config import OPENAI_API_KEY


def get_openai_client() -> AsyncOpenAI | None:
    if not OPENAI_API_KEY:
        return None
    return AsyncOpenAI(api_key=OPENAI_API_KEY)
