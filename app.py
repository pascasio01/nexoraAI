from fastapi import FastAPI

from config import APP_NAME, logger
from deps import close_services, init_services
from routes import mark_started, router
from telegram_actor import telegram_shutdown, telegram_startup

app = FastAPI(title=f"{APP_NAME} AI OS")
app.include_router(router)


@app.on_event("startup")
async def startup() -> None:
    mark_started()
    try:
        await init_services()
    except Exception as exc:
        logger.warning(f"Service initialization degraded: {exc}")

    try:
        await telegram_startup()
    except Exception as exc:
        logger.warning(f"Telegram startup degraded: {exc}")


@app.on_event("shutdown")
async def shutdown() -> None:
    await telegram_shutdown()
    await close_services()
