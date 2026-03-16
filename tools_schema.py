tools = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Busca en internet información reciente y resumida.",
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
            "description": "Consulta conocimiento privado/base documental del asistente.",
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
            "description": "Dispara acciones externas mediante webhook (notas, recordatorios, reportes).",
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
