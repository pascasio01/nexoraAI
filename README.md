# nexoraAI

## Realtime frontend MVP

The repository now includes a Next.js realtime web UI at:

- `./frontend`

### Run locally

1. Start backend (FastAPI) from repo root:

```bash
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

2. Start frontend in a new terminal:

```bash
cd frontend
npm install
npm run dev
```

3. Open `http://localhost:3000`.

### WebSocket connection

The frontend `RealtimeProvider` builds the websocket URL in this order:

1. `NEXT_PUBLIC_WS_URL` (full explicit ws/wss URL)
2. `NEXT_PUBLIC_BACKEND_URL` + `/ws/{NEXT_PUBLIC_SITE_ID}/{NEXT_PUBLIC_ROOM_ID}`
3. Defaults to `ws://127.0.0.1:8000/ws/web/main`

Example environment variables for `frontend/.env.local`:

```bash
NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8000
NEXT_PUBLIC_SITE_ID=web
NEXT_PUBLIC_ROOM_ID=main
```
