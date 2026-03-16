from fastapi import FastAPI

from config import APP_NAME, logger
from deps import close_deps
from routes import router as http_router
from telegram_actor import telegram_shutdown, telegram_startup
from websocket_router import router as websocket_router

app = FastAPI(title=f"{APP_NAME} AI OS")
app.include_router(http_router)
app.include_router(websocket_router)


@app.on_event("startup")
async def startup() -> None:
    try:
        await telegram_startup()
    except Exception as exc:  # pragma: no cover - defensive startup branch
        logger.warning("Telegram startup skipped due to error: %s", exc)


@app.on_event("shutdown")
async def shutdown() -> None:
    try:
        await telegram_shutdown()
    finally:
        await close_deps()
