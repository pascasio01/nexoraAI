from openai import AsyncOpenAI
from tavily import TavilyClient

from config import APP_NAME, MODEL_NAME, OPENAI_API_KEY, TAVILY_API_KEY, logger
from memory import check_rate_limit, load_chat_memory, save_chat_memory

client = None
tavily = None

if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY is not configured. AI responses are disabled.")
else:
    try:
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    except Exception as exc:
        logger.warning("OpenAI initialization failed: %s", exc)
        client = None

if TAVILY_API_KEY:
    try:
        tavily = TavilyClient(api_key=TAVILY_API_KEY)
    except Exception as exc:
        logger.warning("Tavily initialization failed: %s", exc)
        tavily = None
else:
    logger.warning("TAVILY_API_KEY is not configured. Web search is disabled.")


async def search_web(query: str) -> list[dict]:
    if tavily is None:
        return []
    try:
        result = tavily.search(query=query, max_results=3)
        return [
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("content", ""),
            }
            for item in result.get("results", [])
        ]
    except Exception as exc:
        logger.warning("Tavily search failed: %s", exc)
        return []


async def ask_nexora(
    user_id: str,
    text: str,
    channel: str = "web",
    use_web_search: bool = False,
) -> str:
    if client is None:
        return "NexoraAI is online, but OpenAI is not configured yet."

    if not await check_rate_limit(user_id):
        return "Too many messages. Please wait a minute and try again."

    history = await load_chat_memory(user_id)
    system_prompt = (
        f"You are {APP_NAME}, a personal AI assistant. "
        f"Keep responses clear and concise. Channel: {channel}."
    )
    messages = [{"role": "system", "content": system_prompt}] + history

    if use_web_search:
        snippets = await search_web(text)
        if snippets:
            context = "\n".join(
                f"- {item['title']}: {item['snippet']} ({item['url']})" for item in snippets
            )
            messages.append({"role": "system", "content": f"Web context:\n{context}"})

    messages.append({"role": "user", "content": text})

    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            max_tokens=500,
        )
    except Exception as exc:
        logger.warning("OpenAI request failed: %s", exc)
        return "I couldn't generate a response right now. Please try again soon."

    answer = response.choices[0].message.content or "I couldn't generate a response."
    await save_chat_memory(user_id, "user", text)
    await save_chat_memory(user_id, "assistant", answer)
    return answer


def openai_enabled() -> bool:
    return client is not None


def tavily_enabled() -> bool:
    return tavily is not None
