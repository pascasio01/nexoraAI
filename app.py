import os
import json
import logging

from fastapi import FastAPI, Request, Response
from dotenv import load_dotenv
from openai import AsyncOpenAI
import redis.asyncio as redis
from tavily import TavilyClient

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# CONFIG
# =========================
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("Nexora")

APP_NAME = os.getenv("APP_NAME", "Nexora")
BASE_URL = os.getenv("BASE_URL", "").rstrip("/")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
REDIS_URL = os.getenv("REDIS_URL")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")

OWNER_ID_RAW = os.getenv("OWNER_ID", "0")
OWNER_ID = int(OWNER_ID_RAW) if OWNER_ID_RAW.isdigit() else 0

# =========================
# CLIENTES SEGUROS
# =========================
client = None
r = None
tavily = None
tg_app = None

if not OPENAI_API_KEY:
    logger.warning("⚠️ OPENAI_API_KEY no configurada. IA desactivada.")
else:
    try:
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:
        logger.warning(f"⚠️ No se pudo inicializar OpenAI: {e}")
        client = None

if not REDIS_URL:
    logger.warning("⚠️ REDIS_URL no configurada. Memoria desactivada.")
else:
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
    except Exception as e:
        logger.warning(f"⚠️ No se pudo inicializar Redis: {e}")
        r = None

if not TAVILY_API_KEY:
    logger.warning("⚠️ TAVILY_API_KEY no configurada. Búsqueda web desactivada.")
else:
    try:
        tavily = TavilyClient(api_key=TAVILY_API_KEY)
    except Exception as e:
        logger.warning(f"⚠️ No se pudo inicializar Tavily: {e}")
        tavily = None

if not BOT_TOKEN:
    logger.warning("⚠️ BOT_TOKEN no configurado. Telegram desactivado.")

# =========================
# APP
# =========================
app = FastAPI(title=APP_NAME)

MAX_CHAT_HISTORY = 12

# =========================
# MEMORIA / RATE LIMIT (TOLERANTE)
# =========================
async def check_rate_limit(user_id: str) -> bool:
    if r is None:
        return True
    try:
        key = f"rate_limit:{user_id}"
        count = await r.incr(key)
        if count == 1:
            await r.expire(key, 60)
        return count <= 8
    except Exception as e:
        logger.warning(f"Rate limit desactivado por error Redis: {e}")
        return True

async def save_chat_memory(user_id: str, role: str, content: str) -> None:
    if r is None:
        return
    try:
        await r.rpush(f"chat:{user_id}", json.dumps({"role": role, "content": content}))
        await r.ltrim(f"chat:{user_id}", -MAX_CHAT_HISTORY, -1)
    except Exception as e:
        logger.warning(f"No se pudo guardar memoria: {e}")

async def load_chat_memory(user_id: str):
    if r is None:
        return []
    try:
        history_raw = await r.lrange(f"chat:{user_id}", 0, -1)
        return [json.loads(m) for m in history_raw]
    except Exception as e:
        logger.warning(f"No se pudo cargar memoria: {e}")
        return []

async def reset_memory(user_id: str) -> None:
    if r is None:
        return
    try:
        await r.delete(f"chat:{user_id}")
    except Exception as e:
        logger.warning(f"No se pudo reiniciar memoria: {e}")

# =========================
# WEB SEARCH (TOLERANTE)
# =========================
async def search_web(query: str):
    if tavily is None:
        return [{"error": "Búsqueda web desactivada"}]
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
        logger.warning(f"Error buscando en web: {e}")
        return [{"error": f"Error de búsqueda: {e}"}]

# =========================
# IA (TOLERANTE)
# =========================
async def ask_nexora(user_id: str, text: str, channel: str) -> str:
    if client is None:
        return "⚠️ OpenAI no está configurado ahora mismo."

    if not await check_rate_limit(user_id):
        return "⚠️ Límite de mensajes alcanzado. Espera un minuto."

    history = await load_chat_memory(user_id)

    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=history + [{"role": "user", "content": text}],
            max_tokens=500,
        )
        answer = response.choices[0].message.content or "No pude generar respuesta."
    except Exception as e:
        logger.error(f"Error OpenAI: {e}")
        return "⚠️ Hubo un problema generando la respuesta."

    await save_chat_memory(user_id, "user", text)
    await save_chat_memory(user_id, "assistant", answer)
    return answer

# =========================
# TELEGRAM (HANDLERS MÍNIMOS)
# =========================
async def tg_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if OWNER_ID and update.effective_user and update.effective_user.id != OWNER_ID:
        return
    if update.message:
        await update.message.reply_text("✅ Nexora está activa.")

async def tg_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if OWNER_ID and update.effective_user and update.effective_user.id != OWNER_ID:
        return
    if update.message:
        await update.message.reply_text("Nexora status: activa.")

async def tg_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if OWNER_ID and update.effective_user and update.effective_user.id != OWNER_ID:
        return
    if update.effective_user:
        await reset_memory(str(update.effective_user.id))
    if update.message:
        await update.message.reply_text("Memoria reiniciada.")

async def handle_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if OWNER_ID and update.effective_user and update.effective_user.id != OWNER_ID:
        return
    if update.message and update.message.text:
        reply = await ask_nexora(str(update.effective_user.id), update.message.text, "telegram")
        await update.message.reply_text(reply)

# =========================
# STARTUP / SHUTDOWN (SEGURO)
# =========================
@app.on_event("startup")
async def startup():
    global r, tg_app

    if r is not None:
        try:
            await r.ping()
            logger.info("✅ Redis conectado")
        except Exception as e:
            logger.warning(f"⚠️ Redis no disponible al startup: {e}")
            r = None

    if BOT_TOKEN:
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

            logger.info("✅ Telegram activo")
        except Exception as e:
            logger.warning(f"⚠️ Telegram no pudo iniciar: {e}")
            tg_app = None

@app.on_event("shutdown")
async def shutdown():
    global tg_app, r

    try:
        if tg_app:
            if BASE_URL:
                await tg_app.bot.delete_webhook()
            await tg_app.stop()
            await tg_app.shutdown()
    except Exception as e:
        logger.warning(f"⚠️ Error apagando Telegram: {e}")

    try:
        if r:
            await r.close()
    except Exception as e:
        logger.warning(f"⚠️ Error cerrando Redis: {e}")

# =========================
# ROUTES
# =========================
@app.get("/")
async def home():
    return {"app": APP_NAME, "status": "online", "model": MODEL_NAME}

@app.get("/health")
async def health():
    redis_ok = False
    try:
        if r:
            await r.ping()
            redis_ok = True
    except Exception:
        redis_ok = False

    return {
        "status": "ok",
        "redis": redis_ok,
        "openai": client is not None,
        "tavily": tavily is not None,
        "telegram": tg_app is not None,
    }

@app.post("/tg/{token}")
async def tg_webhook(token: str, request: Request):
    if not BOT_TOKEN or token != BOT_TOKEN:
        return {"ok": False, "error": "token inválido"}

    if tg_app is None:
        return {"ok": False, "error": "telegram no iniciado"}

    data = await request.json()
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return {"ok": True}# core/memory_store.py

async def save_long_memory(user_id, memory):
    return None

async def load_long_memory(user_id):
    return None(function(){
  const site_id = document.currentScript.getAttribute('data-site-id');# core/__init__.py
  let visitor_id = localStorage.getItem(site_id+"_visitor");
  if (!visitor_id) {
    const name = prompt("¿Cómo te llamas?");
    fetch("/visitor/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ site_id, name })
    })
    .then(res => res.json())
    .then(data => {
      visitor_id = data.visitor_id;
      localStorage.setItem(site_id+"_visitor", visitor_id);
      startChat();
    });
  } else {
    startChat();
  }
  function startChat() {
    fetch("/room/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ site_id, type: "soporte" })
    })
    .then(res => res.json())
    .then(data => {
      const room_id = data.room_id;
      const chatDiv = document.createElement('div');
      chatDiv.innerHTML = `<div id="nexora-widget" style="position:fixed;bottom:24px;right:24px;background:#fff;padding:12px;border-radius:8px;box-shadow:0 2px 8px #aaa;">
          <div id="msgs" style="max-height:150px;overflow:auto;margin-bottom:8px;"></div>
          <input id="msg" placeholder="Escribe..." style="width:120px;">
          <button id="send">Enviar</button>
        </div>`;
      document.body.appendChild(chatDiv);
      const ws = new WebSocket("wss://TU_BACKEND/ws/" + site_id + "/" + room_id);
      ws.onmessage = evt => {
        const msgData = JSON.parse(evt.data);
        const msgBox = document.getElementById('msgs');
        const msgElem = document.createElement('div');
        msgElem.textContent = msgData.content;
        msgBox.appendChild(msgElem);
        msgBox.scrollTop = msgBox.scrollHeight;
      };
      document.getElementById('send').onclick = () => {
        const content = document.getElementById('msg').value;
        ws.send(JSON.stringify({
          visitor_id,
          content
        }));
        document.getElementById('msg').value = "";
      };
    });
  }
})();<script src="https://TU_DOMINIO/widget.js" data-site-id="abc123"></script>connections = {}

@app.websocket("/ws/{site_id}/{room_id}")
async def websocket_room(websocket: WebSocket, site_id: str, room_id: str):
    await websocket.accept()
    key = f"{site_id}:{room_id}"
    if key not in connections:
        connections[key] = []
    connections[key].append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            visitor_id = payload.get("visitor_id")
            content = payload.get("content")
            with engine.connect() as conn:
                conn.execute(insert(messages).values(room_id=room_id, visitor_id=visitor_id, content=content))
            for ws in connections[key]:
                await ws.send_text(json.dumps({
                    "visitor_id": visitor_id,
                    "content": content
                }))
    except WebSocketDisconnect:
        connections[key].remove(websocket)@app.post("/visitor/register")
async def register_visitor(site_id: str, name: str = "", email: str = ""):
    visitor_id = f"{site_id}_{uuid.uuid4().hex[:10]}"
    with engine.connect() as conn:
        conn.execute(insert(visitors).values(visitor_id=visitor_id, site_id=site_id, name=name, email=email))
    return {"visitor_id": visitor_id}

@app.post("/room/create")
async def create_room(site_id: str, type: str = "soporte"):
    room_id = f"{site_id}_{type}_{uuid.uuid4().hex[:8]}"
    with engine.connect() as conn:
        conn.execute(insert(rooms).values(room_id=room_id, site_id=site_id, type=type))
    return {"room_id": room_id}

@app.get("/rooms/{site_id}")
async def list_rooms(site_id: str):
    with engine.connect() as conn:
        result = conn.execute(select(rooms).where(rooms.c.site_id == site_id)).fetchall()
    return [{"room_id": r.room_id, "type": r.type, "created_at": r.created_at} for r in result]

@app.post("/message/send")
async def send_message(room_id: str, visitor_id: str, content: str):
    with engine.connect() as conn:
        conn.execute(insert(messages).values(room_id=room_id, visitor_id=visitor_id, content=content))
    return {"ok": True}

@app.get("/messages/{room_id}")
async def get_messages(room_id: str):
    with engine.connect() as conn:
        result = conn.execute(select(messages).where(messages.c.room_id == room_id)).fetchall()
    return [{"visitor_id": r.visitor_id, "content": r.content, "timestamp": r.timestamp} for r in result]sites = Table("sites", metadata,
    Column("id", Integer, primary_key=True),
    Column("site_id", String, unique=True),
    Column("name", String),
    Column("theme", String),
    Column("bot_name", String)
)

visitors = Table("visitors", metadata,
    Column("id", Integer, primary_key=True),
    Column("visitor_id", String, unique=True),
    Column("site_id", String),
    Column("name", String),
    Column("email", String),
    Column("created_at", TIMESTAMP)
)

rooms = Table("rooms", metadata,
    Column("id", Integer, primary_key=True),
    Column("room_id", String, unique=True),
    Column("site_id", String),
    Column("type", String),
    Column("created_at", TIMESTAMP)
)

messages = Table("messages", metadata,
    Column("id", Integer, primary_key=True),
    Column("room_id", String),
    Column("visitor_id", String),
    Column("content", Text),
    Column("timestamp", TIMESTAMP)
)

# Descomenta solo para crear tablas la primera vez
# metadata.create_all(bind=engine)# ========== NUEVAS IMPORTS ==========
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, Text, TIMESTAMP
from sqlalchemy.sql import insert, select
from fastapi import WebSocket, WebSocketDisconnect
import uuid

# ========== VARIABLES DE ENTORNO ==========
DATABASE_URL = os.getenv("DATABASE_URL")  # Railway variable
engine = create_engine(DATABASE_URL)
metadata = MetaData()import os
import json
import html
import io
import logging
import asyncio
from datetime import datetime

from fastapi import FastAPI, Form, Response, Request
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import AsyncOpenAI
import redis.asyncio as redis
from tavily import TavilyClient
import httpx

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

# =========================
# CONFIGURACIÓN & LOGS
# =========================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Nexora")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
REDIS_URL = os.getenv("REDIS_URL")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
BASE_URL = os.getenv("BASE_URL", "https://nexoraai-production.up.railway.app").rstrip("/")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
ACTION_WEBHOOK_URL = os.getenv("ACTION_WEBHOOK_URL")

MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")
APP_NAME = os.getenv("APP_NAME", "Nexora")
CREATOR_NAME = os.getenv("CREATOR_NAME", "Pascasio Emmanuel Reynoso Reyes")
CREATOR_ALIAS = os.getenv("CREATOR_ALIAS", "Emmanuel Reynoso")

if not OPENAI_API_KEY:
    raise ValueError("Falta OPENAI_API_KEY")
if not BOT_TOKEN:
    raise ValueError("Falta BOT_TOKEN")
if not REDIS_URL:
    raise ValueError("Falta REDIS_URL")
if not BASE_URL:
    raise ValueError("Falta BASE_URL")

client = AsyncOpenAI(api_key=OPENAI_API_KEY)
r = redis.from_url(REDIS_URL, decode_responses=True)
tavily = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None

app = FastAPI(title=f"{APP_NAME} AI OS")
tg_app = None

MAX_CHAT_HISTORY = 12

# =========================
# SEGURIDAD Y MEMORIA
# =========================
async def check_rate_limit(user_id: str):
    key = f"rate_limit:{user_id}"
    count = await r.incr(key)
    if count == 1:
        await r.expire(key, 60)
    return count <= 8

async def update_user_profile(user_id: str, last_interaction: str):
    try:
        profile_key = f"profile:{user_id}"
        old_profile = await r.get(profile_key) or "Sin datos previos."

        prompt = (
            f"Perfil actual: {old_profile}\n"
            f"Interacción: {last_interaction}\n"
            "Actualiza el perfil con hechos útiles y relativamente estables del usuario. "
            "No inventes. Sé breve."
        )

        res = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=120
        )
        await r.set(profile_key, res.choices[0].message.content)
    except Exception as e:
        logger.error(f"Error actualizando perfil: {e}")

async def save_chat_memory(user_id: str, role: str, content: str):
    await r.rpush(f"chat:{user_id}", json.dumps({"role": role, "content": content}))
    await r.ltrim(f"chat:{user_id}", -MAX_CHAT_HISTORY, -1)

async def load_chat_memory(user_id: str):
    history_raw = await r.lrange(f"chat:{user_id}", 0, -1)
    return [json.loads(m) for m in history_raw]

async def reset_memory(user_id: str):
    await r.delete(f"chat:{user_id}")

# =========================
# HERRAMIENTAS
# =========================
async def search_web(query: str):
    if not tavily:
        return [{"error": "TAVILY_API_KEY no configurada"}]

    try:
        result = tavily.search(query=query, max_results=3)
        return [
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("content", "")
            }
            for item in result.get("results", [])
        ]
    except Exception as e:
        return [{"error": f"Error de búsqueda: {e}"}]

async def consultar_biblioteca(query: str):
    return {
        "resultado": "Sistema RAG listo para indexar PDFs y documentos. Búsqueda privada aún en fase inicial.",
        "query": query
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
                "data": {
                    **details,
                    "timestamp": datetime.utcnow().isoformat()
                }
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
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_biblioteca",
            "description": "Consulta documentos y archivos privados del usuario.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"]
            }
        }
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
                            "location_alarm"
                        ]
                    },
                    "details": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "content": {"type": "string"},
                            "category": {
                                "type": "string",
                                "enum": ["Trabajo", "Personal", "Idea", "Finanzas", "Estudio", "Seguridad", "Otro"]
                            },
                            "priority": {
                                "type": "string",
                                "enum": ["Alta", "Media", "Baja"]
                            },
                            "schedule_time": {"type": "string"},
                            "destination": {"type": "string"},
                            "report_type": {
                                "type": "string",
                                "enum": ["diario", "semanal", "ideas", "tasks", "mixed"]
                            }
                        },
                        "required": ["content"]
                    }
                },
                "required": ["action_name", "details"]
            }
        }
    }
]

# =========================
# NÚCLEO DE INTELIGENCIA
# =========================
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
    if not await check_rate_limit(user_id):
        return "⚠️ Límite de mensajes alcanzado. Espera un minuto."

    history = await load_chat_memory(user_id)
    profile = await r.get(f"profile:{user_id}") or "Usuario nuevo."

    sys_prompt = f"{SYSTEM_PROMPT}\nPerfil del usuario: {profile}\nCanal: {channel}"
    messages = [{"role": "system", "content": sys_prompt}] + history + [{"role": "user", "content": text}]

    response = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        tools=tools,
        tool_choice="auto",
        max_tokens=800
    )

    msg = response.choices[0].message

    if msg.tool_calls:
        messages.append(msg)

        for tool in msg.tool_calls:
            if tool.function.name == "search_web":
                args = json.loads(tool.function.arguments)
                res = await search_web(args["query"])
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool.id,
                    "name": "search_web",
                    "content": json.dumps(res, ensure_ascii=False)
                })

            elif tool.function.name == "consultar_biblioteca":
                args = json.loads(tool.function.arguments)
                res = await consultar_biblioteca(args["query"])
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool.id,
                    "name": "consultar_biblioteca",
                    "content": json.dumps(res, ensure_ascii=False)
                })

            elif tool.function.name == "execute_action":
                args = json.loads(tool.function.arguments)
                res = await execute_action(args["action_name"], args["details"])
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool.id,
                    "name": "execute_action",
                    "content": res
                })

        final = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            max_tokens=800
        )
        answer = final.choices[0].message.content or "No pude generar una respuesta."
    else:
        answer = msg.content or "No pude generar una respuesta."

    await save_chat_memory(user_id, "user", text)
    await save_chat_memory(user_id, "assistant", answer)

    asyncio.create_task(update_user_profile(user_id, f"User: {text} | Nexora: {answer}"))
    return answer

# =========================
# MODELOS WEB
# =========================
class ChatRequest(BaseModel):
    texto: str
    usuario: str | None = "web_user"

# =========================
# WEB & HEALTH
# =========================
@app.get("/")
async def home():
    return {
        "app": APP_NAME,
        "status": "active",
        "model": MODEL_NAME
    }

@app.get("/health")
async def health():
    try:
        pong = await r.ping()
        return {"ok": True, "redis": pong, "telegram": tg_app is not None}
    except Exception as e:
        return {"ok": False, "error": str(e)}

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
    return {"ok": True, "mensaje": "Memoria reiniciada."}

# =========================
# WHATSAPP
# =========================
@app.post("/whatsapp")
async def whatsapp_webhook(Body: str = Form(...), From: str = Form(...)):
    try:
        answer = await ask_nexora(From, Body, "WhatsApp")
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{html.escape(answer)}</Message>
</Response>"""
        return Response(content=twiml, media_type="application/xml")
    except Exception as e:
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{html.escape(str(e))}</Message>
</Response>"""
        return Response(content=twiml, media_type="application/xml")

# =========================
# TELEGRAM HANDLERS
# =========================
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
        f"Redis: ok\n"
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
    if update.effective_user.id != OWNER_ID:
        return

    if not update.message:
        return

    user_id = str(update.effective_user.id)
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )

    try:
        if update.message.document:
            await update.message.reply_text("📥 Documento recibido. La biblioteca privada está lista para integrarse.")
            return

        if update.message.photo:
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
                            {"type": "image_url", "image_url": {"url": file.file_path}}
                        ]
                    }
                ],
                max_tokens=800
            )

            answer = response.choices[0].message.content or "No pude analizar la imagen."
            await save_chat_memory(user_id, "user", prompt)
            await save_chat_memory(user_id, "assistant", answer)
            await update.message.reply_text(answer)
            return

        if update.message.voice:
            file = await context.bot.get_file(update.message.voice.file_id)
            audio_data = io.BytesIO()
            await file.download_to_memory(audio_data)
            audio_data.name = "audio.ogg"
            audio_data.seek(0)

            transcription = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_data
            )

            answer = await ask_nexora(user_id, transcription.text, "Telegram")
            await update.message.reply_text(answer)
            return

        if update.message.text:
            res = await ask_nexora(user_id, update.message.text, "Telegram")
            await update.message.reply_text(res)
            return

    except Exception as e:
        logger.error(f"Error Telegram: {e}")
        await update.message.reply_text(f"Error interno: {e}")

# =========================
# LIFECYCLE
# =========================
@app.on_event("startup")
async def startup():
    global tg_app
    tg_app = ApplicationBuilder().token(BOT_TOKEN).build()
    tg_app.add_handler(CommandHandler("start", tg_start))
    tg_app.add_handler(CommandHandler("status", tg_status))
    tg_app.add_handler(CommandHandler("reset", tg_reset))
    tg_app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_telegram))

    await tg_app.initialize()
    await tg_app.start()
    await tg_app.bot.set_webhook(url=f"{BASE_URL}/tg/{BOT_TOKEN}")
    logger.info("Telegram webhook activo")

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
    if tg_app:
        await tg_app.bot.delete_webhook()
        await tg_app.stop()
        await tg_app.shutdown()
