tools = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Busca información en tiempo real usando web search cuando está habilitado.",
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
            "name": "consultar_biblioteca",
            "description": "Consulta memoria/documentación interna del usuario (placeholder extensible).",
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
            "name": "execute_action",
            "description": "Ejecuta acciones remotas opcionales en un webhook de automatización.",
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
