from fastapi import Request


async def telegram_startup() -> None:
    return None


async def telegram_shutdown() -> None:
    return None


async def telegram_webhook(token: str, request: Request) -> dict[str, str]:
    return {"ok": True, "token": token}
