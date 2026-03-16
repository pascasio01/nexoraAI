from fastapi import FastAPI, Request

from config import APP_NAME
from routes import router as http_router
from telegram_actor import telegram_shutdown, telegram_startup, telegram_webhook
from websocket_router import router as websocket_router

app = FastAPI(title=f"{APP_NAME} AI OS")
app.include_router(http_router)
app.include_router(websocket_router)


@app.on_event("startup")
async def startup() -> None:
    await telegram_startup()


@app.on_event("shutdown")
async def shutdown() -> None:
    await telegram_shutdown()


@app.post("/tg/{token}")
async def tg_webhook(token: str, request: Request):
    return await telegram_webhook(token, request)
