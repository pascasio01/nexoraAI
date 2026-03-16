from __future__ import annotations

import json

from config import APP_NAME, CREATOR_ALIAS, CREATOR_NAME, MODEL_NAME, logger
import deps
from memory import (
    check_rate_limit,
    get_assistant_settings,
    get_profile,
    load_chat_memory,
    load_long_memory,
    save_chat_memory,
    save_long_memory,
)
from tools_impl import notes_tasks, web_search, webhook_action
from tools_schema import tools

SYSTEM_PROMPT = f"""
You are {APP_NAME}, an AI assistant created by {CREATOR_NAME} ({CREATOR_ALIAS}).
Follow user language, be accurate, and do not invent facts.
When tools are unavailable or disabled, explain it clearly.
""".strip()


def _safe_tool_args(raw_args: str | None) -> dict:
    if not raw_args:
        return {}
    try:
        parsed = json.loads(raw_args)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


async def _run_tool(user_id: str, tool_name: str, args: dict):
    if tool_name == "web_search":
        return await web_search(args.get("query", ""))
    if tool_name == "notes_tasks":
        return await notes_tasks(
            user_id=user_id,
            operation=args.get("operation", ""),
            content=args.get("content", ""),
        )
    if tool_name == "webhook_action":
        return await webhook_action(
            action_name=args.get("action_name", ""),
            details=args.get("details", {}),
        )
    return {"error": f"Unknown tool: {tool_name}"}


async def ask_nexora(user_id: str, text: str, channel: str) -> str:
    if not await check_rate_limit(user_id):
        return "⚠️ Message limit reached. Please wait a minute and try again."

    if not deps.client:
        return "🤖 Nexora is online, but AI responses are temporarily unavailable because OPENAI_API_KEY is not configured."

    history = await load_chat_memory(user_id)
    profile = await get_profile(user_id)
    assistant_settings = await get_assistant_settings(user_id)
    long_term_memory = await load_long_memory(user_id)

    sys_prompt = (
        f"{SYSTEM_PROMPT}\n"
        f"User profile: {profile}\n"
        f"Channel: {channel}\n"
        f"Assistant settings: {json.dumps(assistant_settings, ensure_ascii=False)}\n"
        f"Relevant long-term memory: {json.dumps(long_term_memory, ensure_ascii=False)}"
    )
    messages = [{"role": "system", "content": sys_prompt}] + history + [{"role": "user", "content": text}]

    try:
        response = await deps.client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=800,
        )
    except Exception as exc:
        logger.error("OpenAI request failed: %s", exc)
        return "⚠️ I couldn't process your request right now. Please try again shortly."

    msg = response.choices[0].message

    if msg.tool_calls:
        messages.append(
            {
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [tool_call.model_dump(exclude_none=True) for tool_call in msg.tool_calls],
            }
        )

        for tool_call in msg.tool_calls:
            args = _safe_tool_args(tool_call.function.arguments)
            result = await _run_tool(user_id, tool_call.function.name, args)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_call.function.name,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

        try:
            second = await deps.client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                max_tokens=800,
            )
            final_text = (second.choices[0].message.content or "").strip()
        except Exception as exc:
            logger.error("OpenAI tool follow-up failed: %s", exc)
            final_text = "⚠️ Tool executed, but I couldn't generate the final response."
    else:
        final_text = (msg.content or "").strip()

    await save_chat_memory(user_id, "user", text)
    await save_chat_memory(user_id, "assistant", final_text)
    await save_long_memory(user_id, f"{channel}: {text[:180]}")

    return final_text or "I don't have an answer right now."
