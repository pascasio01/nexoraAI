"""Tool schemas for NexoraAI.

This module keeps tool definitions isolated from implementation details so the
AI core can expose a stable, extensible tool contract.
"""

from copy import deepcopy

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for up-to-date information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query text."}
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "notes",
            "description": "Create, list, or delete personal notes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["add", "list", "delete"]},
                    "text": {"type": "string"},
                    "note_id": {"type": "string"},
                },
                "required": ["action"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tasks",
            "description": "Manage tasks (add, list, complete, delete).",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["add", "list", "complete", "delete"],
                    },
                    "title": {"type": "string"},
                    "task_id": {"type": "string"},
                },
                "required": ["action"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reminders",
            "description": "Manage reminders (add, list, delete).",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["add", "list", "delete"]},
                    "text": {"type": "string"},
                    "when": {"type": "string"},
                    "reminder_id": {"type": "string"},
                },
                "required": ["action"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "webhook_action",
            "description": "Send a structured action payload to a configured webhook.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "payload": {"type": "object"},
                    "method": {"type": "string", "enum": ["POST", "PUT", "PATCH"]},
                },
                "required": ["url", "payload"],
                "additionalProperties": False,
            },
        },
    },
]

# Backwards-compatible alias expected by existing callers.
tools = TOOLS_SCHEMA


def get_tools_schema():
    """Return a defensive copy so callers cannot mutate global schemas."""

    return deepcopy(TOOLS_SCHEMA)
