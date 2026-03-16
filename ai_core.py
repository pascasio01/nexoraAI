import hashlib
import hmac
import json
import time

from config import (
    APP_NAME,
    AUTH_SIGNING_KEY,
    AUTH_TOKEN_MAX_AGE_SECONDS,
    CREATOR_ALIAS,
    CREATOR_NAME,
    MODEL_NAME,
)
from deps import client
from memory import (
    check_rate_limit,
    get_assistant_settings,
    get_profile,
    get_user_session,
    load_chat_memory,
    save_chat_memory,
    set_profile,
)
from tools_impl import search_web
from tools_schema import tools

SYSTEM_PROMPT = f"""
Eres {APP_NAME}, una asistente personal premium creada por {CREATOR_NAME}, también conocido como {CREATOR_ALIAS}.
Debes priorizar respuestas útiles, humanas, seguras y claras.
Si una capacidad no está disponible aún, dilo con honestidad y ofrece alternativa.
""".strip()


def verify_identity_token(token: str) -> str | None:
    if not AUTH_SIGNING_KEY:
        return None
    try:
        user_id, ts, signature = token.split(".", 2)
        body = f"{user_id}.{ts}".encode()
        expected = hmac.new(AUTH_SIGNING_KEY.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None
        if time.time() - int(ts) > AUTH_TOKEN_MAX_AGE_SECONDS:
            return None
        return user_id
    except Exception:
        return None


def resolve_user_id(request_user_id: str | None, auth_header: str | None) -> str:
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        verified_user = verify_identity_token(token)
        if verified_user:
            return verified_user
    if request_user_id:
        return request_user_id
    return "web_user"


async def update_user_profile(user_id: str, last_interaction: str):
    if client is None:
        return
    old_profile = await get_profile(user_id)
    prompt = (
        f"Perfil actual: {old_profile}\n"
        f"Interacción: {last_interaction}\n"
        "Actualiza solo con hechos estables del usuario. Sé breve y no inventes."
    )
    try:
        res = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=120,
        )
        if res.choices and res.choices[0].message and res.choices[0].message.content:
            await set_profile(user_id, res.choices[0].message.content)
    except Exception:
        return


async def ask_nexora(user_id: str, text: str, channel: str) -> str:
    if client is None:
        return "⚠️ OpenAI no está configurado ahora mismo."

    if not await check_rate_limit(user_id):
        return "⚠️ Límite de mensajes alcanzado. Espera un minuto."

    history = await load_chat_memory(user_id)
    profile = await get_profile(user_id)
    settings = await get_assistant_settings(user_id)
    session = await get_user_session(user_id)

    sys_prompt = (
        f"{SYSTEM_PROMPT}\n"
        f"Perfil del usuario: {profile}\n"
        f"Canal: {channel}\n"
        f"Sesión: {json.dumps(session, ensure_ascii=False)}\n"
        f"Ajustes: {json.dumps(settings, ensure_ascii=False)}"
    )
    messages = [{"role": "system", "content": sys_prompt}] + history + [{"role": "user", "content": text}]

    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=700,
        )
        msg = response.choices[0].message
        answer = msg.content or "No pude generar respuesta."

        if msg.tool_calls:
            for tool_call in msg.tool_calls:
                args = json.loads(tool_call.function.arguments or "{}")
                if tool_call.function.name == "search_web" and args.get("query"):
                    web_data = await search_web(args["query"])
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": "search_web",
                            "content": json.dumps(web_data, ensure_ascii=False),
                        }
                    )
            final = await client.chat.completions.create(model=MODEL_NAME, messages=messages, max_tokens=700)
            answer = final.choices[0].message.content or answer

        await save_chat_memory(user_id, "user", text)
        await save_chat_memory(user_id, "assistant", answer)
        await update_user_profile(user_id, f"User: {text} | Assistant: {answer}")
        return answer
    except Exception:
        return "⚠️ Hubo un problema generando la respuesta."
