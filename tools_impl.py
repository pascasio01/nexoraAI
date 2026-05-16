"""Concrete tool implementations for NexoraAI."""

from __future__ import annotations

import asyncio
import ipaddress
import os
from datetime import datetime, timezone
from uuid import uuid4
from urllib.parse import urlparse

import httpx

_NOTES: dict[str, list[dict]] = {}
_TASKS: dict[str, list[dict]] = {}
_REMINDERS: dict[str, list[dict]] = {}
_NOTES_LOCK = asyncio.Lock()
_TASKS_LOCK = asyncio.Lock()
_REMINDERS_LOCK = asyncio.Lock()


def _store_for_user(store: dict[str, list[dict]], user_id: str | None) -> list[dict]:
    key = user_id or "default"
    if key not in store:
        store[key] = []
    return store[key]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def web_search(query: str) -> dict:
    query = (query or "").strip()
    if not query:
        return {"ok": False, "error": "query is required"}

    tavily_key = os.getenv("TAVILY_API_KEY")
    if not tavily_key:
        return {
            "ok": True,
            "query": query,
            "results": [],
            "message": "Web search provider not configured.",
        }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={"api_key": tavily_key, "query": query, "max_results": 5},
            )
            response.raise_for_status()
            data = response.json()
        return {
            "ok": True,
            "query": query,
            "results": data.get("results", []),
            "answer": data.get("answer"),
        }
    except Exception as exc:
        return {"ok": False, "error": f"web search failed: {exc}"}


async def notes(action: str, text: str | None = None, note_id: str | None = None, user_id: str | None = None) -> dict:
    async with _NOTES_LOCK:
        bucket = _store_for_user(_NOTES, user_id)

        if action == "add":
            if not text:
                return {"ok": False, "error": "text is required for add"}
            item = {"id": str(uuid4()), "text": text, "created_at": _utc_now_iso()}
            bucket.append(item)
            return {"ok": True, "note": item}

        if action == "list":
            return {"ok": True, "notes": list(bucket)}

        if action == "delete":
            if not note_id:
                return {"ok": False, "error": "note_id is required for delete"}
            before = len(bucket)
            bucket[:] = [n for n in bucket if n["id"] != note_id]
            return {"ok": True, "deleted": before - len(bucket)}

        return {"ok": False, "error": f"unsupported action: {action}"}


async def tasks(action: str, title: str | None = None, task_id: str | None = None, user_id: str | None = None) -> dict:
    async with _TASKS_LOCK:
        bucket = _store_for_user(_TASKS, user_id)

        if action == "add":
            if not title:
                return {"ok": False, "error": "title is required for add"}
            item = {
                "id": str(uuid4()),
                "title": title,
                "completed": False,
                "created_at": _utc_now_iso(),
            }
            bucket.append(item)
            return {"ok": True, "task": item}

        if action == "list":
            return {"ok": True, "tasks": list(bucket)}

        if action == "complete":
            if not task_id:
                return {"ok": False, "error": "task_id is required for complete"}
            for task in bucket:
                if task["id"] == task_id:
                    task["completed"] = True
                    task["completed_at"] = _utc_now_iso()
                    return {"ok": True, "task": task}
            return {"ok": False, "error": "task not found"}

        if action == "delete":
            if not task_id:
                return {"ok": False, "error": "task_id is required for delete"}
            before = len(bucket)
            bucket[:] = [t for t in bucket if t["id"] != task_id]
            return {"ok": True, "deleted": before - len(bucket)}

        return {"ok": False, "error": f"unsupported action: {action}"}


async def reminders(
    action: str,
    text: str | None = None,
    when: str | None = None,
    reminder_id: str | None = None,
    user_id: str | None = None,
) -> dict:
    async with _REMINDERS_LOCK:
        bucket = _store_for_user(_REMINDERS, user_id)

        if action == "add":
            if not text or not when:
                return {"ok": False, "error": "text and when are required for add"}
            item = {
                "id": str(uuid4()),
                "text": text,
                "when": when,
                "created_at": _utc_now_iso(),
            }
            bucket.append(item)
            return {"ok": True, "reminder": item}

        if action == "list":
            return {"ok": True, "reminders": list(bucket)}

        if action == "delete":
            if not reminder_id:
                return {"ok": False, "error": "reminder_id is required for delete"}
            before = len(bucket)
            bucket[:] = [r for r in bucket if r["id"] != reminder_id]
            return {"ok": True, "deleted": before - len(bucket)}

        return {"ok": False, "error": f"unsupported action: {action}"}


async def webhook_action(url: str, payload: dict, method: str = "POST") -> dict:
    parsed = urlparse(url or "")
    if parsed.scheme != "https" or not parsed.netloc:
        return {"ok": False, "error": "invalid webhook url"}
    if parsed.hostname in {"localhost", "::1"}:
        return {"ok": False, "error": "webhook hostname is not allowed"}
    try:
        host_ip = ipaddress.ip_address(parsed.hostname or "")
        if host_ip.is_private or host_ip.is_loopback or host_ip.is_link_local:
            return {"ok": False, "error": "webhook hostname is not allowed"}
    except ValueError:
        pass

    safe_method = (method or "POST").upper()
    if safe_method not in {"POST", "PUT", "PATCH"}:
        return {"ok": False, "error": "invalid method"}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.request(safe_method, url, json=payload)
        if response.is_error:
            return {
                "ok": False,
                "status_code": response.status_code,
                "error": response.text[:500],
            }
        return {"ok": True, "status_code": response.status_code}
    except Exception as exc:
        return {"ok": False, "error": f"webhook failed: {exc}"}


TOOL_IMPLEMENTATIONS = {
    "web_search": web_search,
    "notes": notes,
    "tasks": tasks,
    "reminders": reminders,
    "webhook_action": webhook_action,
}
