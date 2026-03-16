from fastapi import Request, Response

from config import BOT_TOKEN
from ai_core import ask_nexora


async def telegram_startup() -> None:
    pass


async def telegram_shutdown() -> None:
    pass


async def telegram_webhook(_token: str, _request: Request):
    if not BOT_TOKEN or _token != BOT_TOKEN:
        return Response(status_code=403)
    data = await _request.json()
    message = data.get("message", {})
    text = message.get("text")
    sender = message.get("from", {}) or {}
    chat = message.get("chat", {}) or {}
    sender_id = sender.get("id") or chat.get("id")
    if sender_id is None:
        return Response(status_code=400)
    user_id = str(sender_id)

    if text:
        await ask_nexora(user_id=user_id, text=text, channel="Telegram")
    return Response(content='{"ok": true}', media_type="application/json")
