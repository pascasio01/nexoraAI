import os
import html
from collections import defaultdict

from fastapi import FastAPI, Form, Response
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import AsyncOpenAI

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
APP_NAME = os.getenv("APP_NAME", "Nexora")
CREATOR_NAME = os.getenv("CREATOR_NAME", "Pascasio Emmanuel Reynoso Reyes")
CREATOR_ALIAS = os.getenv("CREATOR_ALIAS", "Emmanuel Reynoso")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

NEWS_MODE = os.getenv("NEWS_MODE", "off").lower()
DOCS_MODE = os.getenv("DOCS_MODE", "off").lower()
VISION_MODE = os.getenv("VISION_MODE", "off").lower()
AUTOMATION_MODE = os.getenv("AUTOMATION_MODE", "off").lower()

if not OPENAI_API_KEY:
    raise ValueError("Falta OPENAI_API_KEY")

client = AsyncOpenAI(api_key=OPENAI_API_KEY)
app = FastAPI(title=APP_NAME)

SYSTEM_PROMPT = f"""
Eres {APP_NAME}, una asistente inteligente avanzada, clara, útil, humana, precisa y con estilo tecnológico elegante.
Fuiste creada por {CREATOR_NAME}, también conocido como {CREATOR_ALIAS}.
Respondes en el idioma del usuario.
Si el usuario escribe con errores, sin comas o de forma desordenada, entiendes su intención real.
No inventas información. Si no sabes algo, lo dices con honestidad.
No finges ser doctora, abogada ni profesional licenciada.
En salud, legal y finanzas solo orientas de forma general y segura.
Tu misión es ayudar a pensar mejor, aprender mejor y construir mejor con tecnología.
También puedes actuar como mentor tecnológico, asistente productiva y guía digital.
Si el usuario pregunta quién te creó, respondes con el nombre del creador.
Si el usuario pide noticias en tiempo real y no hay conexión de búsqueda habilitada, lo dices claramente.
"""

memory_store = defaultdict(list)
MAX_HISTORY = 10

def save_memory(memory_key: str, user_text: str, answer: str):
    memory_store[memory_key].append({"role": "user", "content": user_text})
    memory_store[memory_key].append({"role": "assistant", "content": answer})
    memory_store[memory_key] = memory_store[memory_key][-MAX_HISTORY:]

async def ask_nexora(memory_key: str, user_text: str, channel_name: str):
    history = memory_store[memory_key]

    system_text = SYSTEM_PROMPT + f"\nEstás respondiendo por {channel_name}."
    if NEWS_MODE != "on":
        system_text += "\nLa búsqueda y noticias en tiempo real no están habilitadas aún."
    if DOCS_MODE != "on":
        system_text += "\nEl análisis de documentos no está habilitado aún."
    if VISION_MODE != "on":
        system_text += "\nLa visión por computadora no está habilitada aún."
    if AUTOMATION_MODE != "on":
        system_text += "\nLa automatización avanzada no está habilitada aún."

    messages = [{"role": "system", "content": system_text}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_text})

    response = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        max_tokens=500,
    )

    answer = response.choices[0].message.content or "No pude generar una respuesta."
    save_memory(memory_key, user_text, answer)
    return answer

class ChatRequest(BaseModel):
    texto: str
    usuario: str | None = "web_user"

@app.get("/")
async def home():
    return {
        "app": APP_NAME,
        "status": "activa",
        "creador": CREATOR_NAME,
        "alias": CREATOR_ALIAS,
        "news_mode": NEWS_MODE,
        "docs_mode": DOCS_MODE,
        "vision_mode": VISION_MODE,
        "automation_mode": AUTOMATION_MODE,
    }

@app.get("/health")
async def health():
    return {"ok": True}

@app.get("/about")
async def about():
    return {
        "nombre": APP_NAME,
        "creador": CREATOR_NAME,
        "alias": CREATOR_ALIAS,
        "descripcion": "Asistente inteligente con enfoque en tecnología, productividad, educación y guía digital."
    }

@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        memory_key = f"web:{req.usuario}"
        answer = await ask_nexora(memory_key, req.texto, "web")
        return {"respuesta": answer}
    except Exception as e:
        return {"error": str(e)}

@app.post("/reset-web")
async def reset_web(req: ChatRequest):
    memory_key = f"web:{req.usuario}"
    memory_store[memory_key] = []
    return {"ok": True, "mensaje": "Memoria web reiniciada."}

@app.post("/whatsapp")
async def whatsapp_webhook(Body: str = Form(...), From: str = Form(...)):
    try:
        memory_key = f"wa:{From}"
        answer = await ask_nexora(memory_key, Body, "WhatsApp")
        answer = html.escape(answer)

        twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{answer}</Message>
</Response>"""

        return Response(content=twiml_response, media_type="application/xml")

    except Exception as e:
        error_text = html.escape(f"Tuve un problema procesando tu mensaje: {e}")
        twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{error_text}</Message>
</Response>"""
        return Response(content=twiml_response, media_type="application/xml")

telegram_app = None

async def tg_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Acceso no autorizado.")
        return

    memory_store[f"tg:{update.effective_user.id}"] = []
    await update.message.reply_text(
        f"Hola. Soy {APP_NAME}. Estoy activa, privada y lista para ayudarte."
    )

async def tg_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Acceso no autorizado.")
        return

    memory_store[f"tg:{update.effective_user.id}"] = []
    await update.message.reply_text("Memoria reiniciada.")

async def tg_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Acceso no autorizado.")
        return

    await update.message.reply_text(
        f"{APP_NAME} activa.\n"
        f"Modelo: {MODEL_NAME}\n"
        f"Noticias tiempo real: {NEWS_MODE}\n"
        f"Documentos: {DOCS_MODE}\n"
        f"Visión: {VISION_MODE}\n"
        f"Automatización: {AUTOMATION_MODE}"
    )

async def tg_responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Acceso no autorizado.")
        return

    if not update.message or not update.message.text:
        return

    texto = update.message.text.strip().lower()

    if "quién te creó" in texto or "quien te creo" in texto:
        await update.message.reply_text(
            f"Fui creada por {CREATOR_NAME}, también conocido como {CREATOR_ALIAS}."
        )
        return

    try:
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING
        )

        memory_key = f"tg:{update.effective_user.id}"
        answer = await ask_nexora(memory_key, update.message.text, "Telegram")
        await update.message.reply_text(answer)

    except Exception as e:
        await update.message.reply_text(f"Tuve un problema: {e}")

@app.on_event("startup")
async def startup_event():
    global telegram_app

    if BOT_TOKEN:
        telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()
        telegram_app.add_handler(CommandHandler("start", tg_start))
        telegram_app.add_handler(CommandHandler("reset", tg_reset))
        telegram_app.add_handler(CommandHandler("status", tg_status))
        telegram_app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, tg_responder)
        )

        await telegram_app.initialize()
        await telegram_app.start()
        await telegram_app.updater.start_polling()
        print("Telegram activo.")

@app.on_event("shutdown")
async def shutdown_event():
    global telegram_app

    if telegram_app:
        await telegram_app.updater.stop()
        await telegram_app.stop()
        await telegram_app.shutdown()
        print("Telegram detenido.")
