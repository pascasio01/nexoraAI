async def telegram_startup():
    return None


async def telegram_shutdown():
    return None


async def telegram_webhook(request):
    del request
    return {"ok": True, "message": "Telegram integration scaffold ready"}
