from fastapi import FastAPI

from config import APP_NAME
from deps import close_deps
from routes import router
from telegram_actor import telegram_shutdown, telegram_startup

app = FastAPI(title=f"{APP_NAME} AI OS")
app.include_router(router)


@app.on_event("startup")
async def startup() -> None:
    await telegram_startup()


@app.on_event("shutdown")
async def shutdown() -> None:
    await telegram_shutdown()
    await close_deps()
