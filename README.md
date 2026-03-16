# nexoraAI

Modular FastAPI backend for a lightweight AI assistant.

## Run

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

## Environment

All integrations are optional and fail-safe:

- `OPENAI_API_KEY`
- `REDIS_URL`
- `TAVILY_API_KEY`
- `BOT_TOKEN`
- `BASE_URL` (only needed for Telegram webhook setup)

## Core endpoints

- `GET /health`
- `POST /chat` with `{ "text": "...", "user_id": "..." }`
- `POST /memory/reset`
- `GET /memory/{user_id}`
- `POST /tg/{token}` (Telegram webhook)
