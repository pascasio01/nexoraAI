from fastapi import Request


async def telegram_startup() -> None:
    pass


async def telegram_shutdown() -> None:
    pass


async def telegram_webhook(token: str, request: Request) -> dict[str, str | bool]:
    return {"ok": True, "token": token}
