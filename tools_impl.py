from __future__ import annotations

from datetime import datetime, timezone
import httpx

from config import settings


class ToolExecutor:
    def __init__(self, memory_store, tavily_client=None):
        self.memory_store = memory_store
        self.tavily_client = tavily_client

    async def web_search(self, user_id: str, query: str) -> dict:
        if not self.tavily_client:
            return {"ok": False, "message": "Web search unavailable (missing TAVILY_API_KEY)."}
        result = self.tavily_client.search(query=query, max_results=3)
        return {"ok": True, "results": result.get("results", [])}

    async def create_note(self, user_id: str, title: str, content: str) -> dict:
        note = {
            "title": title,
            "content": content,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.memory_store.create_note(user_id, note)
        return {"ok": True, "note": note}

    async def create_task(self, user_id: str, title: str, due_at: str | None = None) -> dict:
        task = {
            "title": title,
            "due_at": due_at,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "open",
        }
        self.memory_store.create_task(user_id, task)
        return {"ok": True, "task": task}

    async def create_reminder(self, user_id: str, text: str, remind_at: str | None = None) -> dict:
        reminder = {
            "text": text,
            "remind_at": remind_at,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.memory_store.create_reminder(user_id, reminder)
        return {"ok": True, "reminder": reminder}

    async def webhook_action(self, user_id: str, action: str, payload: dict) -> dict:
        if not settings.action_webhook_url:
            return {"ok": False, "message": "Webhook unavailable (missing ACTION_WEBHOOK_URL)."}
        body = {
            "user_id": user_id,
            "action": action,
            "payload": payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(settings.action_webhook_url, json=body)
        return {"ok": True, "status_code": response.status_code}
