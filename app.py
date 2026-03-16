"""Minimal FastAPI entrypoint for Nexora AI OS foundation."""

from __future__ import annotations

from fastapi import FastAPI

from config import APP_NAME
from deps import get_telegram_actor, shutdown_dependencies, startup_dependencies
from routes import router

app = FastAPI(title=f"{APP_NAME} AI OS")
app.include_router(router)


@app.on_event("startup")
async def startup() -> None:
    await startup_dependencies()
    await get_telegram_actor().startup()


@app.on_event("shutdown")
async def shutdown() -> None:
    await get_telegram_actor().shutdown()
    await shutdown_dependencies()
