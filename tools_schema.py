"""OpenAI-compatible tool schema definitions."""

tools = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Busca información reciente en internet.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "manage_notes_tasks",
            "description": "Crear notas o tareas personales del usuario.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "action": {"type": "string", "enum": ["note", "task", "list_notes", "list_tasks"]},
                    "content": {"type": "string"},
                    "title": {"type": "string"},
                },
                "required": ["user_id", "action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_webhook",
            "description": "Ejecuta automatizaciones por webhook con un payload estructurado.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action_name": {"type": "string"},
                    "details": {"type": "object"},
                    "user_id": {"type": "string"},
                    "agent_id": {"type": "string"},
                },
                "required": ["action_name", "details", "user_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_reminder",
            "description": "Programa un recordatorio como tarea persistente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "reminder_text": {"type": "string"},
                    "when": {"type": "string"},
                },
                "required": ["user_id", "reminder_text", "when"],
            },
        },
    },
]
