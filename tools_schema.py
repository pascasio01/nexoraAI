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
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_biblioteca",
            "description": "Consulta documentos y archivos privados del usuario.",
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
            "description": "Guarda notas, crea recordatorios, agenda eventos o genera reportes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action_name": {
                        "type": "string",
                        "enum": [
                            "save_note",
                            "set_reminder",
                            "set_calendar_event",
                            "send_report",
                            "location_alarm",
                        ],
                    },
                    "details": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "content": {"type": "string"},
                            "category": {
                                "type": "string",
                                "enum": ["Trabajo", "Personal", "Idea", "Finanzas", "Estudio", "Seguridad", "Otro"],
                            },
                            "priority": {"type": "string", "enum": ["Alta", "Media", "Baja"]},
                            "schedule_time": {"type": "string"},
                            "destination": {"type": "string"},
                            "report_type": {"type": "string", "enum": ["diario", "semanal", "ideas", "tasks", "mixed"]},
                        },
                        "required": ["content"],
                    },
                },
                "required": ["action_name", "details"],
            },
        },
    },
]
