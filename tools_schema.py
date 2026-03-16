tools = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Busca información actual en internet.",
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
            "description": "Consulta memoria documental privada del usuario.",
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
            "description": "Dispara automatizaciones externas seguras (notas/tareas/eventos/reportes).",
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
