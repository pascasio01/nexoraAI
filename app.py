from fastapi import FastAPI

from config import APP_NAME, logger
from deps import r
from routes import router
from telegram_actor import telegram_shutdown, telegram_startup

app = FastAPI(title=f"{APP_NAME} AI OS")
app.include_router(router)


@app.on_event("startup")
async def startup():
    if r is not None:
        try:
            await r.ping()
            logger.info("Redis connected.")
        except Exception as exc:
            logger.warning("Redis ping failed on startup: %s", exc)
    await telegram_startup()


@app.on_event("shutdown")
async def shutdown():
    await telegram_shutdown()
    if r is not None:
        try:
            await r.close()
        except Exception as exc:
            logger.warning("Redis close failed: %s", exc)
