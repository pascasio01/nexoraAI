tools = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search public information on the web.",
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
            "name": "notes_tasks",
            "description": "Store or list user notes/tasks for long-term memory support.",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {"type": "string", "enum": ["add", "list"]},
                    "content": {"type": "string"},
                },
                "required": ["operation"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "webhook_action",
            "description": "Trigger an external webhook action safely.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action_name": {"type": "string"},
                    "details": {"type": "object"},
                },
                "required": ["action_name"],
            },
        },
    },
]
