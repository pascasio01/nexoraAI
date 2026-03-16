import logging
import os
from contextlib import suppress
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request, Response
from pydantic import BaseModel

try:
    from openai import AsyncOpenAI
except Exception:  # pragma: no cover - defensive import guard
    AsyncOpenAI = None  # type: ignore[assignment]

try:
    import redis.asyncio as redis
except Exception:  # pragma: no cover - defensive import guard
    redis = None  # type: ignore[assignment]

try:
    from tavily import TavilyClient
except Exception:  # pragma: no cover - defensive import guard
    TavilyClient = None  # type: ignore[assignment]

try:
    from telegram import Update
    from telegram.ext import (
        ApplicationBuilder,
        CommandHandler,
        ContextTypes,
        MessageHandler,
        filters,
    )

    TELEGRAM_IMPORT_OK = True
except Exception:  # pragma: no cover - defensive import guard
    TELEGRAM_IMPORT_OK = False


load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("Nexora")

APP_NAME = (os.getenv("APP_NAME") or "Nexora").strip()
MODEL_NAME = (os.getenv("MODEL_NAME") or "gpt-4o-mini").strip()
BASE_URL = (os.getenv("BASE_URL") or "").strip().rstrip("/")
BOT_TOKEN = (os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN") or "").strip()
OPENAI_API_KEY = (os.getenv("OPENAI_API_KEY") or "").strip()
REDIS_URL = (os.getenv("REDIS_URL") or "").strip()
TAVILY_API_KEY = (os.getenv("TAVILY_API_KEY") or "").strip()


class ChatRequest(BaseModel):
    usuario: Optional[str] = "web_user"
    texto: str


app = FastAPI(title=f"{APP_NAME} AI OS")

redis_client = None
openai_client = None
tavily_client = None
tg_app = None


async def ask_nexora(user_id: str, text: str, channel: str) -> str:
    text = text.strip()
    if not text:
        return "No recibí texto para procesar."

    if openai_client is None:
        return "OPENAI_API_KEY no configurada. Respuesta local de contingencia activa."

    try:
        response = await openai_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Eres Nexora, una asistente útil y breve."},
                {
                    "role": "user",
                    "content": f"Usuario: {user_id}\nCanal: {channel}\nMensaje: {text}",
                },
            ],
            max_tokens=400,
        )
        return (response.choices[0].message.content or "").strip() or "Sin contenido generado."
    except Exception as exc:
        logger.warning("OpenAI request failed: %s", exc)
        return "Servicio de IA temporalmente no disponible."


async def tg_start(update: "Update", context: "ContextTypes.DEFAULT_TYPE") -> None:
    await update.message.reply_text("Nexora activa ✅")


async def tg_status(update: "Update", context: "ContextTypes.DEFAULT_TYPE") -> None:
    await update.message.reply_text("Estado: operativo")


async def tg_reset(update: "Update", context: "ContextTypes.DEFAULT_TYPE") -> None:
    await update.message.reply_text("Memoria web reiniciada para esta sesión ✅")


async def handle_telegram(update: "Update", context: "ContextTypes.DEFAULT_TYPE") -> None:
    if not update.message or not update.message.text:
        return
    user_id = str(update.effective_user.id if update.effective_user else "telegram_user")
    answer = await ask_nexora(user_id, update.message.text, "Telegram")
    await update.message.reply_text(answer)


@app.on_event("startup")
async def startup() -> None:
    global redis_client, openai_client, tavily_client, tg_app

    if AsyncOpenAI is not None and OPENAI_API_KEY:
        openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    else:
        logger.warning("OpenAI client disabled (missing package or OPENAI_API_KEY)")

    if redis is not None and REDIS_URL:
        with suppress(Exception):
            redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        if redis_client is not None:
            try:
                await redis_client.ping()
                logger.info("Redis conectado")
            except Exception as exc:
                logger.warning("Redis no disponible al startup: %s", exc)
                redis_client = None

    if TavilyClient is not None and TAVILY_API_KEY:
        with suppress(Exception):
            tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

    if TELEGRAM_IMPORT_OK and BOT_TOKEN:
        try:
            tg_app = ApplicationBuilder().token(BOT_TOKEN).build()
            tg_app.add_handler(CommandHandler("start", tg_start))
            tg_app.add_handler(CommandHandler("status", tg_status))
            tg_app.add_handler(CommandHandler("reset", tg_reset))
            tg_app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_telegram))
            await tg_app.initialize()
            await tg_app.start()

            if BASE_URL:
                await tg_app.bot.set_webhook(url=f"{BASE_URL}/tg/{BOT_TOKEN}")
                logger.info("Telegram webhook configurado")
            else:
                logger.warning("BASE_URL ausente: webhook de Telegram no configurado")
        except Exception as exc:
            logger.warning("Telegram no pudo iniciar: %s", exc)
            tg_app = None


@app.on_event("shutdown")
async def shutdown() -> None:
    global tg_app, redis_client

    if tg_app is not None:
        with suppress(Exception):
            if BASE_URL:
                await tg_app.bot.delete_webhook()
        with suppress(Exception):
            await tg_app.stop()
        with suppress(Exception):
            await tg_app.shutdown()
        tg_app = None

    if redis_client is not None:
        with suppress(Exception):
            await redis_client.close()
        redis_client = None


@app.get("/")
async def home() -> Dict[str, str]:
    return {"app": APP_NAME, "status": "online", "model": MODEL_NAME}


@app.get("/health")
async def health() -> Dict[str, Any]:
    redis_ok = False
    if redis_client is not None:
        with suppress(Exception):
            redis_ok = bool(await redis_client.ping())

    health_data = {
        "status": "ok" if (openai_client is not None or redis_ok or tg_app is not None) else "degraded",
        "services": {
            "openai": openai_client is not None,
            "redis": redis_ok,
            "telegram": tg_app is not None,
            "tavily": tavily_client is not None,
        },
        "config": {
            "has_base_url": bool(BASE_URL),
            "has_bot_token": bool(BOT_TOKEN),
            "has_openai_api_key": bool(OPENAI_API_KEY),
            "has_redis_url": bool(REDIS_URL),
            "has_tavily_api_key": bool(TAVILY_API_KEY),
        },
    }
    return health_data


@app.post("/chat")
async def chat(req: ChatRequest) -> Dict[str, str]:
    answer = await ask_nexora(req.usuario or "web_user", req.texto, "Web")
    return {"respuesta": answer}


@app.post("/reset-web")
async def reset_web(req: ChatRequest) -> Dict[str, str]:
    return {"ok": "true", "usuario": req.usuario or "web_user", "message": "Memoria web reseteada"}


@app.post("/whatsapp")
async def whatsapp_webhook(Body: str = Form(...), From: str = Form(...)) -> Dict[str, str]:
    answer = await ask_nexora(From, Body, "WhatsApp")
    return {"respuesta": answer}


@app.post("/tg/{token}")
async def tg_webhook(token: str, request: Request) -> Any:
    if not BOT_TOKEN or token != BOT_TOKEN:
        return Response(status_code=403)
    if tg_app is None:
        return Response(status_code=503)

    payload = await request.json()
    await tg_app.process_update(Update.de_json(payload, tg_app.bot))
    return {"ok": True}
