tools = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Busca en tiempo real en internet.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    }
]
