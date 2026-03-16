from collections.abc import AsyncGenerator

from config import APP_NAME, STREAMING_CHUNK_SIZE, logger
from deps import get_openai_client

HISTORY_CONTEXT_WINDOW = 6


async def generate_assistant_reply(user_message: str, history: list[dict[str, str]] | None = None) -> str:
    """Return an assistant reply, using OpenAI when configured and safe fallback otherwise."""
    history = history or []
    client = get_openai_client()

    if not client:
        return f"{APP_NAME}: Recibí tu mensaje: {user_message}"

    try:
        messages = [{"role": "system", "content": f"You are {APP_NAME}, a helpful assistant."}]
        for item in history[-HISTORY_CONTEXT_WINDOW:]:
            role = item.get("role", "user")
            content = item.get("content", "")
            if content:
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": user_message})

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.4,
        )
        return (response.choices[0].message.content or "").strip() or "Lo siento, no pude responder."
    except Exception as exc:  # pragma: no cover - network/provider errors
        logger.exception("Falling back to local assistant reply after provider error: %s", exc)
        return f"{APP_NAME}: Recibí tu mensaje: {user_message}"


async def stream_assistant_reply(
    user_message: str,
    history: list[dict[str, str]] | None = None,
) -> AsyncGenerator[str, None]:
    """Chunked response stream for websocket clients."""
    reply = await generate_assistant_reply(user_message=user_message, history=history)
    for idx in range(0, len(reply), STREAMING_CHUNK_SIZE):
        yield reply[idx : idx + STREAMING_CHUNK_SIZE]
