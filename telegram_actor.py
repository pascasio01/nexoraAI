async def telegram_startup():
    """Placeholder startup hook for future Telegram integration."""
    return None


async def telegram_shutdown():
    """Placeholder shutdown hook for future Telegram integration."""
    return None


async def telegram_webhook(_request):
    """Placeholder webhook endpoint that confirms scaffold availability."""
    return {"ok": True, "message": "Telegram integration scaffold ready"}
