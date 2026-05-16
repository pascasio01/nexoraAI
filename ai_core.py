"""Safe tool-calling core for NexoraAI."""

from __future__ import annotations

import json
import inspect
from typing import Any

from tools_impl import TOOL_IMPLEMENTATIONS
from tools_schema import TOOLS_SCHEMA


SCHEMA_BY_NAME = {tool["function"]["name"]: tool["function"]["parameters"] for tool in TOOLS_SCHEMA}
HANDLER_PARAMS = {
    name: set(inspect.signature(handler).parameters.keys())
    for name, handler in TOOL_IMPLEMENTATIONS.items()
}


class ToolCallError(ValueError):
    """Raised when a tool call is not valid or not allowed."""


def _type_matches(value: Any, expected: str) -> bool:
    if expected == "string":
        return isinstance(value, str)
    if expected == "object":
        return isinstance(value, dict)
    if expected == "number":
        return isinstance(value, (int, float))
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "array":
        return isinstance(value, list)
    return True


def _validate_args(tool_name: str, arguments: dict) -> None:
    schema = SCHEMA_BY_NAME.get(tool_name)
    if not schema:
        raise ToolCallError(f"unknown tool: {tool_name}")

    if not isinstance(arguments, dict):
        raise ToolCallError("tool arguments must be an object")

    properties = schema.get("properties", {})
    required = schema.get("required", [])
    additional = schema.get("additionalProperties", True)

    for key in required:
        if key not in arguments:
            raise ToolCallError(f"missing required argument: {key}")

    if not additional:
        unknown = [key for key in arguments if key not in properties]
        if unknown:
            raise ToolCallError(f"unexpected argument(s): {', '.join(unknown)}")

    for key, value in arguments.items():
        prop = properties.get(key)
        if not prop:
            continue

        expected_type = prop.get("type")
        if expected_type and not _type_matches(value, expected_type):
            raise ToolCallError(f"invalid type for '{key}', expected {expected_type}")

        if "enum" in prop and value not in prop["enum"]:
            raise ToolCallError(f"invalid value for '{key}'")


def _parse_arguments(arguments: dict | str | None) -> dict:
    if arguments is None:
        return {}
    if isinstance(arguments, dict):
        return arguments
    if isinstance(arguments, str):
        try:
            parsed = json.loads(arguments)
        except json.JSONDecodeError as exc:
            raise ToolCallError("invalid JSON in tool arguments") from exc
        if not isinstance(parsed, dict):
            raise ToolCallError("parsed tool arguments must be an object")
        return parsed
    raise ToolCallError("tool arguments must be dict, json string, or null")


async def execute_tool_call(tool_name: str, arguments: dict | str | None = None, *, user_id: str | None = None) -> dict:
    """Safely execute a single tool call from the AI model."""

    handler = TOOL_IMPLEMENTATIONS.get(tool_name)
    if handler is None:
        raise ToolCallError(f"tool not allowed: {tool_name}")

    args = _parse_arguments(arguments)
    _validate_args(tool_name, args)

    if "user_id" in HANDLER_PARAMS.get(tool_name, set()) and "user_id" not in args:
        args["user_id"] = user_id

    result = await handler(**args)
    if isinstance(result, dict):
        return result
    return {"ok": True, "result": result}
