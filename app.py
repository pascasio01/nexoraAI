from fastapi import FastAPI

from config import APP_NAME, r, logger
from routes import router
from telegram_actor import telegram_startup, telegram_shutdown

app = FastAPI(title=f"{APP_NAME} AI OS")
app.include_router(router)


@app.on_event("startup")
async def startup():
    if r is not None:
        try:
            await r.ping()
            logger.info("✅ Redis conectado")
        except Exception as e:
            logger.warning(f"⚠️ Redis no disponible al startup: {e}")
    await telegram_startup()


@app.on_event("shutdown")
async def shutdown():
    await telegram_shutdown()
    if r is not None:
        try:
            await r.close()
        except Exception as e:
            logger.warning(f"⚠️ Error cerrando Redis: {e}")
