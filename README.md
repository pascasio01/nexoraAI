# nexoraAI

Sora-ready backend foundation for a personal AI companion.

## Current architecture

- `app.py`: FastAPI entrypoint (Railway compatible, safe optional startup)
- `routes.py`: channel/API routing
- `ai_core.py`: `AgentManager` for user-scoped agent orchestration
- `memory.py`: per-user profile, settings, conversation, and long-term memory store
- `tools_impl.py` / `tools_schema.py`: modular tool system
- `telegram_actor.py`: optional Telegram webhook integration

## Core API

- `POST /chat` with `{user_id, message, channel}`
- `POST /assistant-profile`
- `POST /assistant-settings`
- `POST /personal-memory`
- `GET /agents/{user_id}`
- `GET /tools`
- `POST /tools/execute`
- `POST /whatsapp`
- `POST /tg/{token}`
