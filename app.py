import html
import io
import json
import logging
import os
from datetime import datetime
from urllib.parse import urlparse

import httpx
import redis.asyncio as redis
from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request, Response
from openai import AsyncOpenAI
from pydantic import BaseModel
from tavily import TavilyClient
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Nexora")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
REDIS_URL = os.getenv("REDIS_URL")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
BASE_URL = os.getenv("BASE_URL", "").rstrip("/")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
ACTION_WEBHOOK_URL = os.getenv("ACTION_WEBHOOK_URL")

MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")
APP_NAME = os.getenv("APP_NAME", "Nexora")
CREATOR_NAME = os.getenv("CREATOR_NAME", "Pascasio Emmanuel Reynoso Reyes")
CREATOR_ALIAS = os.getenv("CREATOR_ALIAS", "Emmanuel Reynoso")

MAX_CHAT_HISTORY = int(os.getenv("MAX_CHAT_HISTORY", "12"))
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "8"))


def _is_valid_base_url(url: str) -> bool:
    if not url:
        return False
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
r = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None
tavily = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None

app = FastAPI(title=f"{APP_NAME} AI OS")
tg_app = None


async def check_rate_limit(user_id: str) -> bool:
    if not r:
        return True
    key = f"rate_limit:{user_id}"
    count = await r.incr(key)
    if count == 1:
        await r.expire(key, 60)
    return count <= RATE_LIMIT_PER_MINUTE


async def save_chat_memory(user_id: str, role: str, content: str):
    if not r:
        return
    await r.rpush(f"chat:{user_id}", json.dumps({"role": role, "content": content}))
    await r.ltrim(f"chat:{user_id}", -MAX_CHAT_HISTORY, -1)


async def load_chat_memory(user_id: str):
    if not r:
        return []
    history_raw = await r.lrange(f"chat:{user_id}", 0, -1)
    return [json.loads(m) for m in history_raw]


async def reset_memory(user_id: str):
    if not r:
        return
    await r.delete(f"chat:{user_id}")


async def search_web(query: str):
    if not tavily:
        return [{"error": "Búsqueda web deshabilitada: TAVILY_API_KEY no configurada."}]

    try:
        result = tavily.search(query=query, max_results=3)
        return [
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("content", ""),
            }
            for item in result.get("results", [])
        ]
    except Exception as e:
        return [{"error": f"Error de búsqueda: {e}"}]


async def consultar_biblioteca(query: str):
    return {
        "resultado": "Sistema RAG listo para indexar PDFs y documentos. Búsqueda privada aún en fase inicial.",
        "query": query,
    }


async def execute_action(action_name: str, details: dict):
    if not ACTION_WEBHOOK_URL:
        return "ACTION_WEBHOOK_URL no configurado."

    try:
        async with httpx.AsyncClient(timeout=20) as client_http:
            payload = {
                "action": action_name,
                "user_id": OWNER_ID,
                "agent": APP_NAME,
                "data": {**details, "timestamp": datetime.utcnow().isoformat()},
            }
            res = await client_http.post(ACTION_WEBHOOK_URL, json=payload)
            return f"Acción '{action_name}' enviada. Estado: {res.status_code}"
    except Exception as e:
        return f"Error ejecutando acción: {e}"


tools = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Busca en tiempo real en internet.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_biblioteca",
            "description": "Consulta documentos y archivos privados del usuario.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_action",
            "description": "Guarda notas, crea recordatorios, agenda eventos o genera reportes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action_name": {
                        "type": "string",
                        "enum": [
                            "save_note",
                            "set_reminder",
                            "set_calendar_event",
                            "send_report",
                            "location_alarm",
                        ],
                    },
                    "details": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "content": {"type": "string"},
                            "category": {
                                "type": "string",
                                "enum": [
                                    "Trabajo",
                                    "Personal",
                                    "Idea",
                                    "Finanzas",
                                    "Estudio",
                                    "Seguridad",
                                    "Otro",
                                ],
                            },
                            "priority": {
                                "type": "string",
                                "enum": ["Alta", "Media", "Baja"],
                            },
                            "schedule_time": {"type": "string"},
                            "destination": {"type": "string"},
                            "report_type": {
                                "type": "string",
                                "enum": ["diario", "semanal", "ideas", "tasks", "mixed"],
                            },
                        },
                        "required": ["content"],
                    },
                },
                "required": ["action_name", "details"],
            },
        },
    },
]

SYSTEM_PROMPT = f"""
Eres {APP_NAME}, una asistente de IA avanzada creada por {CREATOR_NAME}, también conocido como {CREATOR_ALIAS}.

Reglas:
- Responde en el idioma del usuario.
- No inventes información.
- Si una función no está realmente activa, dilo claramente.
- Puedes usar herramientas para buscar en internet, consultar biblioteca y ejecutar acciones.
- Si el usuario pide guardar algo o recordar algo, puedes usar execute_action.
- Si el usuario pide datos actuales, usa search_web.
- Sé clara, útil, breve y elegante.
"""


async def ask_nexora(user_id: str, text: str, channel: str):
    if not client:
        return "⚠️ Nexora está en modo limitado: falta OPENAI_API_KEY. Configúrala para habilitar respuestas inteligentes."

    if not await check_rate_limit(user_id):
        return "⚠️ Límite de mensajes alcanzado. Espera un minuto."

    history = await load_chat_memory(user_id)
    profile = "Usuario nuevo."
    if r:
        profile = await r.get(f"profile:{user_id}") or profile

    sys_prompt = f"{SYSTEM_PROMPT}\nPerfil del usuario: {profile}\nCanal: {channel}"
    messages = [{"role": "system", "content": sys_prompt}] + history + [{"role": "user", "content": text}]

    response = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        tools=tools,
        tool_choice="auto",
        max_tokens=800,
    )

    msg = response.choices[0].message

    if msg.tool_calls:
        messages.append(msg)

        for tool_call in msg.tool_calls:
            if tool_call.function.name == "search_web":
                args = json.loads(tool_call.function.arguments)
                res = await search_web(args["query"])
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": "search_web",
                        "content": json.dumps(res, ensure_ascii=False),
                    }
                )

            elif tool_call.function.name == "consultar_biblioteca":
                args = json.loads(tool_call.function.arguments)
                res = await consultar_biblioteca(args["query"])
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": "consultar_biblioteca",
                        "content": json.dumps(res, ensure_ascii=False),
                    }
                )

            elif tool_call.function.name == "execute_action":
                args = json.loads(tool_call.function.arguments)
                res = await execute_action(args["action_name"], args["details"])
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": "execute_action",
                        "content": res,
                    }
                )

        final = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            max_tokens=800,
        )
        answer = final.choices[0].message.content or "No pude generar una respuesta."
    else:
        answer = msg.content or "No pude generar una respuesta."

    await save_chat_memory(user_id, "user", text)
    await save_chat_memory(user_id, "assistant", answer)
    return answer


class ChatRequest(BaseModel):
    texto: str
    usuario: str | None = "web_user"


@app.get("/")
async def home():
    return {"app": APP_NAME, "status": "active", "model": MODEL_NAME}


@app.get("/health")
async def health():
    redis_status = "disabled"
    if r:
        try:
            await r.ping()
            redis_status = "ok"
        except Exception:
            redis_status = "error"

    openai_status = "ok" if client else "missing_key"
    tavily_status = "ok" if tavily else "disabled"

    telegram_ready = bool(BOT_TOKEN and _is_valid_base_url(BASE_URL))
    telegram_status = "ok" if tg_app else ("disabled" if not telegram_ready else "error")

    overall_status = "ok" if redis_status != "error" and telegram_status != "error" else "degraded"

    return {
        "status": overall_status,
        "app": APP_NAME,
        "model": MODEL_NAME,
        "services": {
            "redis": redis_status,
            "openai": openai_status,
            "tavily": tavily_status,
            "telegram": telegram_status,
        },
    }


@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        answer = await ask_nexora(req.usuario or "web_user", req.texto, "Web")
        return {"respuesta": answer}
    except Exception as e:
        return {"error": str(e)}


@app.post("/reset-web")
async def reset_web(req: ChatRequest):
    await reset_memory(req.usuario or "web_user")
    if not r:
        return {"ok": True, "mensaje": "Memoria deshabilitada (REDIS_URL no configurada)."}
    return {"ok": True, "mensaje": "Memoria reiniciada."}


@app.post("/whatsapp")
async def whatsapp_webhook(Body: str = Form(...), From: str = Form(...)):
    try:
        answer = await ask_nexora(From, Body, "WhatsApp")
        twiml = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Response>
    <Message>{html.escape(answer)}</Message>
</Response>"""
        return Response(content=twiml, media_type="application/xml")
    except Exception as e:
        twiml = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Response>
    <Message>{html.escape(str(e))}</Message>
</Response>"""
        return Response(content=twiml, media_type="application/xml")


async def tg_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Acceso no autorizado.")
        return
    await reset_memory(str(update.effective_user.id))
    await update.message.reply_text(f"{APP_NAME} activa. Memoria limpia y lista.")


async def tg_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Acceso no autorizado.")
        return
    msg = (
        f"Estado: activa\n"
        f"Modelo: {MODEL_NAME}\n"
        f"Web search: {'on' if TAVILY_API_KEY else 'off'}\n"
        f"Redis: {'ok' if r else 'off'}\n"
        f"Actions webhook: {'on' if ACTION_WEBHOOK_URL else 'off'}"
    )
    await update.message.reply_text(msg)


async def tg_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Acceso no autorizado.")
        return
    await reset_memory(str(update.effective_user.id))
    await update.message.reply_text("Memoria reiniciada.")


async def handle_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID or not update.message:
        return

    user_id = str(update.effective_user.id)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    try:
        if update.message.document:
            await update.message.reply_text("📥 Documento recibido. La biblioteca privada está lista para integrarse.")
            return

        if update.message.photo and client:
            file = await context.bot.get_file(update.message.photo[-1].file_id)
            prompt = update.message.caption or "Analiza esta imagen."

            response = await client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": file.file_path}},
                        ],
                    },
                ],
                max_tokens=800,
            )

            answer = response.choices[0].message.content or "No pude analizar la imagen."
            await save_chat_memory(user_id, "user", prompt)
            await save_chat_memory(user_id, "assistant", answer)
            await update.message.reply_text(answer)
            return

        if update.message.voice and client:
            file = await context.bot.get_file(update.message.voice.file_id)
            audio_data = io.BytesIO()
            await file.download_to_memory(audio_data)
            audio_data.name = "audio.ogg"
            audio_data.seek(0)

            transcription = await client.audio.transcriptions.create(model="whisper-1", file=audio_data)
            answer = await ask_nexora(user_id, transcription.text, "Telegram")
            await update.message.reply_text(answer)
            return

        if update.message.text:
            res = await ask_nexora(user_id, update.message.text, "Telegram")
            await update.message.reply_text(res)
            return

        await update.message.reply_text("Formato no soportado en este momento.")
    except Exception as e:
        logger.error(f"Error Telegram: {e}")
        await update.message.reply_text("Error interno. Intenta de nuevo más tarde.")


@app.on_event("startup")
async def startup():
    global tg_app, r

    if r:
        try:
            await r.ping()
            logger.info("Redis conectado")
        except Exception as e:
            logger.warning(f"Redis no disponible: {e}. Se desactiva memoria.")
            r = None
    else:
        logger.info("REDIS_URL no configurada. Memoria deshabilitada.")

    telegram_ready = bool(BOT_TOKEN and _is_valid_base_url(BASE_URL))
    if not telegram_ready:
        logger.info("Telegram deshabilitado: BOT_TOKEN o BASE_URL inválidos/faltantes.")
        tg_app = None
        return

    try:
        tg_app = ApplicationBuilder().token(BOT_TOKEN).build()
        tg_app.add_handler(CommandHandler("start", tg_start))
        tg_app.add_handler(CommandHandler("status", tg_status))
        tg_app.add_handler(CommandHandler("reset", tg_reset))
        tg_app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_telegram))

        await tg_app.initialize()
        await tg_app.start()
        await tg_app.bot.set_webhook(url=f"{BASE_URL}/tg/{BOT_TOKEN}")
        logger.info("Telegram webhook activo")
    except Exception as e:
        logger.warning(f"Telegram no pudo iniciar: {e}")
        tg_app = None


@app.post("/tg/{token}")
async def tg_webhook(token: str, request: Request):
    if token != BOT_TOKEN:
        return Response(status_code=403)
    if tg_app is None:
        return Response(status_code=503)

    data = await request.json()
    await tg_app.process_update(Update.de_json(data, tg_app.bot))
    return {"ok": True}


@app.on_event("shutdown")
async def shutdown():
    global tg_app

    try:
        if tg_app:
            if BASE_URL:
                await tg_app.bot.delete_webhook()
            await tg_app.stop()
            await tg_app.shutdown()
    except Exception as e:
        logger.warning(f"Error apagando Telegram: {e}")

    try:
        if r:
            await r.close()
    except Exception as e:
        logger.warning(f"Error cerrando Redis: {e}")
