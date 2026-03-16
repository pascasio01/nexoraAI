from __future__ import annotations

import os
from asyncio import Lock
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Form, HTTPException, Request
from pydantic import BaseModel, Field

APP_NAME = os.getenv("APP_NAME", "Nexora")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")

app = FastAPI(title=f"{APP_NAME} AI OS")

SYSTEM_ARCHITECT_PROMPT = """Act as a principal AI systems architect, futurist product designer, and competitive strategy analyst.

You are tasked with evolving the Nexora / SORA assistant platform into a next-generation personal AI system that surpasses current assistants such as ChatGPT, Siri, Alexa, Gemini, and other conversational AI tools.

Your task is not only technical implementation but also strategic architecture.

First analyze what current AI assistants lack, including weaknesses such as:
- lack of persistent life memory
- lack of cross-device identity
- weak multi-agent orchestration
- minimal autonomy
- poor transparency
- lack of personal security intelligence
- lack of long-term personal knowledge modeling

Then design a platform architecture that solves these gaps.

The assistant must evolve from a chatbot into a personal intelligence layer for the user's life.

Key strategic features to design:
1. Life Memory Engine
2. Persistent Identity
3. Multi-Agent Orchestration
4. Decision Engine (levels 0-3 with logging and explainability)
5. Personal Security Layer
6. Cross-Device Presence
7. Real-Time Interaction
8. Long-Term Evolution

Output:
- analysis of current AI assistant limitations
- architectural strategy to surpass them
- modules required to achieve this
- evolution roadmap for the platform
- technical implementation suggestions
- risks and mitigation strategies

Important: Focus on building a sustainable platform architecture, not just features."""

TARGET_ARCHITECTURE: dict[str, Any] = {
    "assistant_limitations": [
        "Session-scoped memory instead of durable life memory",
        "Device-fragmented identity and context loss across channels",
        "Single-agent bottlenecks and weak specialist coordination",
        "Low autonomy maturity and weak action governance",
        "Limited transparency, auditability, and explainability",
        "Reactive safety instead of proactive personal security intelligence",
        "No deep personal knowledge graph that evolves over years",
    ],
    "architectural_strategy": {
        "north_star": "Build a persistent personal intelligence layer that compounds value over time.",
        "principles": [
            "Memory-first architecture with explicit knowledge schemas",
            "Identity continuity across all channels",
            "Orchestrated multi-agent specialization",
            "Policy-driven autonomy with human override",
            "Security-by-default and explainable decisions",
        ],
    },
    "required_modules": [
        "Life Memory Engine",
        "Identity & Trust Fabric",
        "Agent Orchestrator",
        "Decision Engine",
        "Personal Security Intelligence",
        "Cross-Device Presence Gateway",
        "Realtime Interaction Layer",
        "Knowledge Evolution & Archive",
        "Observability, Audit & Governance",
    ],
    "evolution_roadmap": [
        "Phase 1: Foundation (memory schemas, identity, orchestration skeleton)",
        "Phase 2: Guided autonomy (decision levels 0-2, permission workflows)",
        "Phase 3: Trusted automation (level 3 for narrowly approved domains)",
        "Phase 4: Life OS (continuous planning, proactive support, deep knowledge graph)",
    ],
    "technical_implementation": [
        "Event-driven architecture with append-only memory log",
        "Structured profile graph for habits, preferences, relationships, goals",
        "Policy engine for autonomy thresholds and channel-specific permissions",
        "WebSocket/SSE for state streaming and voice-ready session events",
        "Cryptographic identity tokens with device-bound trust signals",
        "Scam and risk detection models in security preflight checks",
    ],
    "risks_and_mitigations": [
        {
            "risk": "Privacy overreach from excessive memory capture",
            "mitigation": "Consent scopes, memory review UI, retention controls, user deletion rights",
        },
        {
            "risk": "Autonomous action errors",
            "mitigation": "Tiered autonomy, dry-runs, approvals, immutable action logs",
        },
        {
            "risk": "Prompt/tool injection across channels",
            "mitigation": "Input provenance checks, tool allowlists, policy sandboxing",
        },
        {
            "risk": "Model drift and opaque recommendations",
            "mitigation": "Evaluation pipelines, explanation traces, rollback-safe deployments",
        },
    ],
}


class ChatRequest(BaseModel):
    user_id: str = Field(default="web-user")
    message: str = Field(min_length=1)
    channel: str = Field(default="web")


class MemoryWriteRequest(BaseModel):
    user_id: str = Field(default="web-user")
    habits: list[str] = Field(default_factory=list)
    preferences: list[str] = Field(default_factory=list)
    relationships: list[str] = Field(default_factory=list)
    important_events: list[str] = Field(default_factory=list)
    long_term_goals: list[str] = Field(default_factory=list)
    personal_context: list[str] = Field(default_factory=list)


class ToolExecuteRequest(BaseModel):
    autonomy_level: int = Field(default=0, ge=0, le=3)
    action: str = Field(default="unspecified")
    explanation: str = Field(default="No explanation provided.")


_MEMORY_STORE: dict[str, dict[str, list[str]]] = {}
_DECISION_LOG: list[dict[str, Any]] = []
_STORE_LOCK = Lock()


def _decision_status(level: int) -> str:
    return {
        0: "prepared",
        1: "prepared",
        2: "awaiting_permission",
        3: "auto_executed",
    }.get(level, "prepared")


@app.get("/")
async def home() -> dict[str, str]:
    return {"app": APP_NAME, "status": "online", "model": MODEL_NAME}


@app.get("/health")
async def health() -> dict[str, bool | str]:
    return {
        "status": "ok",
        "openai": bool(os.getenv("OPENAI_API_KEY")),
        "telegram": bool(os.getenv("BOT_TOKEN")),
    }


@app.get("/assistant-settings")
async def assistant_settings() -> dict[str, Any]:
    return {
        "app_name": APP_NAME,
        "future_prompt": SYSTEM_ARCHITECT_PROMPT,
        "future_architecture": TARGET_ARCHITECTURE,
    }


@app.post("/chat")
async def chat(req: ChatRequest) -> dict[str, Any]:
    profile = _MEMORY_STORE.get(req.user_id, {})
    return {
        "reply": (
            f"{APP_NAME} online. I can operate as a life-intelligence layer with persistent memory, "
            "multi-agent orchestration, and policy-governed autonomy."
        ),
        "user_id": req.user_id,
        "channel": req.channel,
        "memory_summary": {k: len(v) for k, v in profile.items()},
    }


@app.post("/personal-memory")
async def write_personal_memory(req: MemoryWriteRequest) -> dict[str, Any]:
    async with _STORE_LOCK:
        _MEMORY_STORE[req.user_id] = {
            "habits": req.habits,
            "preferences": req.preferences,
            "relationships": req.relationships,
            "important_events": req.important_events,
            "long_term_goals": req.long_term_goals,
            "personal_context": req.personal_context,
        }
        stored_keys = list(_MEMORY_STORE[req.user_id].keys())
    return {"ok": True, "user_id": req.user_id, "stored_keys": stored_keys}


@app.get("/personal-memory/{user_id}")
async def read_personal_memory(user_id: str) -> dict[str, Any]:
    return {"user_id": user_id, "memory": _MEMORY_STORE.get(user_id, {})}


@app.post("/tools/execute")
async def execute_tool(payload: ToolExecuteRequest) -> dict[str, Any]:
    level = payload.autonomy_level
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "autonomy_level": level,
        "action": payload.action,
        "explanation": payload.explanation,
        "status": _decision_status(level),
    }
    async with _STORE_LOCK:
        _DECISION_LOG.append(entry)
    return {"ok": True, "decision": entry}


@app.get("/decision-log")
async def decision_log() -> dict[str, Any]:
    return {"count": len(_DECISION_LOG), "entries": _DECISION_LOG}


@app.post("/whatsapp")
async def whatsapp_webhook(body: str = Form(..., alias="Body"), sender: str = Form(..., alias="From")) -> dict[str, str]:
    return {"ok": "true", "from": sender, "echo": body}


@app.post("/tg/{token}")
async def tg_webhook(token: str, request: Request) -> dict[str, Any]:
    payload = await request.json()
    return {"ok": True, "token": token, "received": bool(payload)}
