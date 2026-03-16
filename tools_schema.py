"""Tool schemas available to personal agents."""

tools = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search public web sources for up-to-date information.",
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
            "name": "manage_note_task",
            "description": "Create a user note or task item in personal memory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "kind": {"type": "string", "enum": ["note", "task"]},
                    "content": {"type": "string"},
                },
                "required": ["user_id", "kind", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_reminder",
            "description": "Save a reminder entry for a user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "content": {"type": "string"},
                    "schedule_time": {"type": "string"},
                },
                "required": ["user_id", "content", "schedule_time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_webhook",
            "description": "Trigger webhook automation workflows.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action_name": {"type": "string"},
                    "details": {"type": "object"},
                },
                "required": ["action_name", "details"],
            },
        },
    },
]
