"""Tool schemas and plugin-aware registry."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

ToolHandler = Callable[[str, dict[str, Any]], Awaitable[str]]


def function_tool(name: str, description: str, parameters: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": parameters,
        },
    }


class ToolRegistry:
    """Stores tools and allows plugin registration."""

    def __init__(self) -> None:
        self._schemas: dict[str, dict[str, Any]] = {}
        self._handlers: dict[str, ToolHandler] = {}
        self._plugins: dict[str, set[str]] = {}

    def register(self, name: str, schema: dict[str, Any], handler: ToolHandler, plugin_name: str = "core") -> None:
        self._schemas[name] = schema
        self._handlers[name] = handler
        self._plugins.setdefault(plugin_name, set()).add(name)

    def list_schemas(self, allowed_tools: list[str] | None = None, denied_tools: list[str] | None = None) -> list[dict[str, Any]]:
        denied = set(denied_tools or [])
        if allowed_tools:
            allowed = set(allowed_tools)
            return [schema for name, schema in self._schemas.items() if name in allowed and name not in denied]
        return [schema for name, schema in self._schemas.items() if name not in denied]

    async def invoke(self, name: str, user_id: str, args: dict[str, Any]) -> str:
        handler = self._handlers.get(name)
        if not handler:
            return f"Tool '{name}' is not registered."
        return await handler(user_id, args)

    def plugin_index(self) -> dict[str, list[str]]:
        return {plugin: sorted(tools) for plugin, tools in self._plugins.items()}
