# NexoraAI Frontend

Next.js App Router frontend for the NexoraAI realtime assistant MVP.

## Run

```bash
npm install
npm run dev
```

Open `http://localhost:3000`.

## Realtime backend websocket

The app connects to websocket in this priority:

1. `NEXT_PUBLIC_WS_URL`
2. `NEXT_PUBLIC_BACKEND_URL` + `/ws/{NEXT_PUBLIC_SITE_ID}/{NEXT_PUBLIC_ROOM_ID}`
3. Default: `ws://127.0.0.1:8000/ws/web/main`

Create `.env.local` if needed:

```bash
NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8000
NEXT_PUBLIC_SITE_ID=web
NEXT_PUBLIC_ROOM_ID=main
```
