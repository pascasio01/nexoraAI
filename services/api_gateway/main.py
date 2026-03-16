from datetime import UTC, datetime

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from services.orchestrator.engine import Orchestrator

from .auth import (
    create_session,
    get_current_user_id,
    hash_password,
    revoke_refresh_token,
    validate_refresh_token,
    verify_password,
)
from .database import ROOT, get_db, init_db
from .schemas import (
    ConversationCreateRequest,
    DeviceUpsertRequest,
    LoginRequest,
    MemoryCreateRequest,
    MessageCreateRequest,
    NotificationReadRequest,
    ProfileUpdateRequest,
    RefreshRequest,
    RegisterRequest,
    TaskCreateRequest,
    TaskUpdateRequest,
)

app = FastAPI(title="NEXORA OMNI API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = Orchestrator()


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/")
def root() -> FileResponse:
    return FileResponse(ROOT / "apps" / "web" / "index.html")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "nexora-omni"}


@app.post("/auth/register")
def register(req: RegisterRequest):
    with get_db() as conn:
        exists = conn.execute("SELECT id FROM users WHERE email = ?", (req.email,)).fetchone()
        if exists:
            raise HTTPException(status_code=409, detail="Email already registered")
        cur = conn.execute(
            "INSERT INTO users (email, password_hash, full_name) VALUES (?, ?, ?)",
            (req.email, hash_password(req.password), req.full_name),
        )
        user_id = cur.lastrowid
    access, refresh = create_session(user_id)
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer", "user_id": user_id}


@app.post("/auth/login")
def login(req: LoginRequest):
    with get_db() as conn:
        user = conn.execute("SELECT id, password_hash FROM users WHERE email = ?", (req.email,)).fetchone()
        if not user or not verify_password(req.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        device = conn.execute(
            "SELECT id FROM devices WHERE user_id = ? AND name = ? AND platform = ?",
            (user["id"], req.device_name, req.device_platform),
        ).fetchone()
        if device:
            device_id = device["id"]
            conn.execute("UPDATE devices SET last_seen = CURRENT_TIMESTAMP WHERE id = ?", (device_id,))
        else:
            cur = conn.execute(
                "INSERT INTO devices (user_id, name, platform, last_seen) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                (user["id"], req.device_name, req.device_platform),
            )
            device_id = cur.lastrowid

    access, refresh = create_session(user["id"], device_id=device_id)
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer", "user_id": user["id"]}


@app.post("/auth/refresh")
def refresh(req: RefreshRequest):
    user_id = validate_refresh_token(req.refresh_token)
    access, refresh_token = create_session(user_id)
    revoke_refresh_token(req.refresh_token)
    return {"access_token": access, "refresh_token": refresh_token, "token_type": "bearer", "user_id": user_id}


@app.post("/auth/logout")
def logout(req: RefreshRequest):
    revoke_refresh_token(req.refresh_token)
    return {"ok": True}


@app.get("/user/profile")
def get_profile(user_id: int = Depends(get_current_user_id)):
    with get_db() as conn:
        row = conn.execute("SELECT id, email, full_name, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row)


@app.put("/user/profile")
def update_profile(req: ProfileUpdateRequest, user_id: int = Depends(get_current_user_id)):
    with get_db() as conn:
        conn.execute("UPDATE users SET full_name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (req.full_name, user_id))
    return {"ok": True}


@app.post("/conversations")
def create_conversation(req: ConversationCreateRequest, user_id: int = Depends(get_current_user_id)):
    with get_db() as conn:
        cur = conn.execute("INSERT INTO conversations (user_id, title) VALUES (?, ?)", (user_id, req.title))
    return {"conversation_id": cur.lastrowid, "title": req.title}


@app.get("/conversations")
def list_conversations(user_id: int = Depends(get_current_user_id)):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, title, created_at, updated_at FROM conversations WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


@app.get("/conversations/{conversation_id}/messages")
def list_messages(conversation_id: int, user_id: int = Depends(get_current_user_id)):
    with get_db() as conn:
        owner = conn.execute("SELECT id FROM conversations WHERE id = ? AND user_id = ?", (conversation_id, user_id)).fetchone()
        if not owner:
            raise HTTPException(status_code=404, detail="Conversation not found")

        rows = conn.execute(
            "SELECT id, role, content, created_at FROM messages WHERE conversation_id = ? ORDER BY id ASC",
            (conversation_id,),
        ).fetchall()
    return [dict(row) for row in rows]


@app.post("/conversations/{conversation_id}/messages")
def create_message(conversation_id: int, req: MessageCreateRequest, user_id: int = Depends(get_current_user_id)):
    with get_db() as conn:
        owner = conn.execute("SELECT id FROM conversations WHERE id = ? AND user_id = ?", (conversation_id, user_id)).fetchone()
        if not owner:
            raise HTTPException(status_code=404, detail="Conversation not found")

        conn.execute(
            "INSERT INTO messages (conversation_id, user_id, role, content) VALUES (?, ?, 'user', ?)",
            (conversation_id, user_id, req.content),
        )

        assistant_reply, meta = orchestrator.respond(req.content)
        conn.execute(
            "INSERT INTO messages (conversation_id, user_id, role, content) VALUES (?, ?, 'assistant', ?)",
            (conversation_id, user_id, assistant_reply),
        )
        conn.execute("UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (conversation_id,))
        conn.execute(
            "INSERT INTO decision_logs (user_id, conversation_id, autonomy_level, risk_score, reason, action) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, conversation_id, meta["autonomy_level"], meta["risk_score"], meta["reason"], meta["action"]),
        )

        memory_candidate = meta.get("memory_candidate")
        if memory_candidate:
            conn.execute(
                "INSERT INTO memory_items (user_id, tier, content, summary, importance, sensitive) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    user_id,
                    memory_candidate.tier,
                    memory_candidate.content,
                    memory_candidate.summary,
                    memory_candidate.importance,
                    1 if memory_candidate.sensitive else 0,
                ),
            )

    return {"assistant_reply": assistant_reply, "decision": {k: v for k, v in meta.items() if k != "memory_candidate"}}


@app.get("/memory")
def list_memory(user_id: int = Depends(get_current_user_id)):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, tier, content, summary, importance, sensitive, created_at FROM memory_items WHERE user_id = ? ORDER BY id DESC",
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


@app.post("/memory")
def create_memory(req: MemoryCreateRequest, user_id: int = Depends(get_current_user_id)):
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO memory_items (user_id, tier, content, summary, importance, sensitive) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, req.tier, req.content, req.summary, req.importance, 1 if req.sensitive else 0),
        )
    return {"id": cur.lastrowid}


@app.delete("/memory/{memory_id}")
def delete_memory(memory_id: int, user_id: int = Depends(get_current_user_id)):
    with get_db() as conn:
        conn.execute("DELETE FROM memory_items WHERE id = ? AND user_id = ?", (memory_id, user_id))
    return {"ok": True}


@app.get("/tasks")
def list_tasks(user_id: int = Depends(get_current_user_id)):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, title, status, due_at, created_at FROM tasks WHERE user_id = ? ORDER BY id DESC",
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


@app.post("/tasks")
def create_task(req: TaskCreateRequest, user_id: int = Depends(get_current_user_id)):
    with get_db() as conn:
        cur = conn.execute("INSERT INTO tasks (user_id, title, due_at) VALUES (?, ?, ?)", (user_id, req.title, req.due_at))
    return {"id": cur.lastrowid}


@app.patch("/tasks/{task_id}")
def update_task(task_id: int, req: TaskUpdateRequest, user_id: int = Depends(get_current_user_id)):
    with get_db() as conn:
        conn.execute(
            "UPDATE tasks SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
            (req.status, task_id, user_id),
        )
    return {"ok": True}


@app.get("/devices")
def list_devices(user_id: int = Depends(get_current_user_id)):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, name, platform, last_seen, created_at FROM devices WHERE user_id = ? ORDER BY id DESC",
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


@app.post("/devices")
def upsert_device(req: DeviceUpsertRequest, user_id: int = Depends(get_current_user_id)):
    with get_db() as conn:
        row = conn.execute(
            "SELECT id FROM devices WHERE user_id = ? AND name = ? AND platform = ?",
            (user_id, req.name, req.platform),
        ).fetchone()
        if row:
            conn.execute("UPDATE devices SET last_seen = CURRENT_TIMESTAMP WHERE id = ?", (row["id"],))
            return {"id": row["id"], "updated": True}

        cur = conn.execute(
            "INSERT INTO devices (user_id, name, platform, last_seen) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
            (user_id, req.name, req.platform),
        )
    return {"id": cur.lastrowid, "updated": False}


@app.get("/notifications")
def list_notifications(user_id: int = Depends(get_current_user_id)):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, title, body, is_read, created_at FROM notifications WHERE user_id = ? ORDER BY id DESC",
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


@app.post("/notifications/read")
def mark_notification_read(req: NotificationReadRequest, user_id: int = Depends(get_current_user_id)):
    with get_db() as conn:
        conn.execute("UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?", (req.notification_id, user_id))
    return {"ok": True}


@app.get("/security/logs")
def list_security_logs(user_id: int = Depends(get_current_user_id)):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, event, severity, details, created_at FROM security_logs WHERE user_id = ? OR user_id IS NULL ORDER BY id DESC LIMIT 200",
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


@app.websocket("/ws/live-chat")
async def ws_live_chat(websocket: WebSocket):
    token = websocket.query_params.get("token", "")
    conversation_id = websocket.query_params.get("conversation_id", "")

    if not token:
        await websocket.close(code=4401)
        return

    from .auth import decode_token

    try:
        payload = decode_token(token, "access")
        user_id = int(payload["sub"])
    except HTTPException:
        await websocket.close(code=4401)
        return

    await websocket.accept()
    await websocket.send_json({"type": "avatar_state", "state": "idle"})

    try:
        while True:
            incoming = await websocket.receive_text()
            await websocket.send_json({"type": "typing_state", "state": "listening"})
            await websocket.send_json({"type": "avatar_state", "state": "listening"})

            conversation = int(conversation_id) if conversation_id.isdigit() else None
            if conversation is None:
                with get_db() as conn:
                    cur = conn.execute("INSERT INTO conversations (user_id, title) VALUES (?, ?)", (user_id, "Chat en tiempo real"))
                    conversation = cur.lastrowid
                    conversation_id = str(conversation)

            with get_db() as conn:
                conn.execute(
                    "INSERT INTO messages (conversation_id, user_id, role, content) VALUES (?, ?, 'user', ?)",
                    (conversation, user_id, incoming),
                )

            await websocket.send_json({"type": "typing_state", "state": "thinking"})
            await websocket.send_json({"type": "avatar_state", "state": "thinking"})
            response, decision_meta = orchestrator.respond(incoming)

            with get_db() as conn:
                conn.execute(
                    "INSERT INTO messages (conversation_id, user_id, role, content) VALUES (?, ?, 'assistant', ?)",
                    (conversation, user_id, response),
                )
                conn.execute(
                    "INSERT INTO decision_logs (user_id, conversation_id, autonomy_level, risk_score, reason, action) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        user_id,
                        conversation,
                        decision_meta["autonomy_level"],
                        decision_meta["risk_score"],
                        decision_meta["reason"],
                        decision_meta["action"],
                    ),
                )

            await websocket.send_json({"type": "typing_state", "state": "responding"})
            await websocket.send_json(
                {
                    "type": "message",
                    "role": "assistant",
                    "content": response,
                    "decision": {
                        "autonomy_level": decision_meta["autonomy_level"],
                        "risk_score": decision_meta["risk_score"],
                        "reason": decision_meta["reason"],
                        "action": decision_meta["action"],
                    },
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )
            await websocket.send_json({"type": "typing_state", "state": "idle"})
            await websocket.send_json({"type": "avatar_state", "state": "idle"})
    except WebSocketDisconnect:
        return
    except Exception as exc:  # noqa: BLE001
        await websocket.send_json({"type": "error", "detail": str(exc)})
        await websocket.close(code=1011)
