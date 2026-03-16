from fastapi import FastAPI

from config import APP_NAME, logger
from deps import initialize_optional_services, shutdown_optional_services
from routes import router
from telegram_actor import telegram_shutdown, telegram_startup

app = FastAPI(title=f"{APP_NAME} AI OS")
app.include_router(router)


@app.on_event("startup")
async def startup() -> None:
    """Initialize optional integrations safely for Railway and local runs."""
    await initialize_optional_services()
    await telegram_startup()
    logger.info("Nexora startup complete.")


@app.on_event("shutdown")
async def shutdown() -> None:
    """Shutdown optional integrations safely."""
    await telegram_shutdown()
    await shutdown_optional_services()
    logger.info("Nexora shutdown complete.")
