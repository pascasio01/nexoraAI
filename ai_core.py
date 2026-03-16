from __future__ import annotations

from config import APP_NAME, MODEL_NAME, logger
from deps import get_openai
from memory import check_rate_limit, load_chat_memory, save_chat_memory

SYSTEM_PROMPT = (
    f"You are {APP_NAME}, a reliable modular AI assistant backend. "
    "Be concise, safe, and transparent when an integration is unavailable."
)


async def ask_nexora(user_id: str, text: str, channel: str) -> str:
    if not await check_rate_limit(user_id):
        return "Rate limit exceeded. Please wait a minute and try again."

    client = get_openai()
    history = await load_chat_memory(user_id)

    if client is None:
        answer = (
            "OpenAI is not configured yet. "
            f"I received your message from {channel}: {text}"
        )
        await save_chat_memory(user_id, "user", text)
        await save_chat_memory(user_id, "assistant", answer)
        return answer

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history + [
        {"role": "user", "content": text}
    ]

    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            max_tokens=500,
        )
        answer = response.choices[0].message.content or "No response generated."
    except Exception as exc:
        logger.warning("OpenAI chat call failed: %s", exc)
        answer = "The assistant had a temporary model error. Please retry."

    await save_chat_memory(user_id, "user", text)
    await save_chat_memory(user_id, "assistant", answer)
    return answer
