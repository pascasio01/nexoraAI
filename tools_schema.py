tools = [
    {
        "type": "function",
        "function": {
            "name": "save_note",
            "description": "Guarda una nota del usuario en su memoria personal.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "category": {"type": "string"},
                },
                "required": ["content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Crea una tarea para el usuario.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                    "due_at": {"type": "string"},
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "Lista las tareas actuales del usuario.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Busca información actualizada en la web usando Tavily.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "webhook_action",
            "description": "Dispara una acción externa por webhook para automatizaciones.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string"},
                    "payload": {"type": "object"},
                },
                "required": ["action"],
            },
        },
    },
]
