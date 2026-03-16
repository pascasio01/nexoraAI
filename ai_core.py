"""AI orchestration for personal agents, tools, and agent-to-agent events."""

from __future__ import annotations

import json

from config import APP_NAME, CREATOR_ALIAS, CREATOR_NAME, MODEL_NAME, logger
from deps import openai_client
from memory import (
    check_rate_limit,
    get_agent_descriptor,
    get_agent_settings,
    get_profile,
    get_summary,
    load_chat_memory,
    save_agent_event,
    save_chat_memory,
    set_profile,
    set_summary,
)
from models import AgentMessageEvent
from tools_impl import execute_webhook, manage_note_task, schedule_reminder, search_web
from tools_schema import tools

SYSTEM_PROMPT = f"""
You are {APP_NAME}, a personal AI agent platform created by {CREATOR_NAME} ({CREATOR_ALIAS}).
You support personal agents, secure structured inter-agent communication, and user-controlled tools.
Respond clearly and safely in the user's language.
""".strip()

TOOL_IMPLS = {
    "search_web": search_web,
    "manage_note_task": manage_note_task,
    "schedule_reminder": schedule_reminder,
    "execute_webhook": execute_webhook,
}


async def _refresh_profile_and_summary(user_id: str, text: str, answer: str) -> None:
    profile = await get_profile(user_id)
    new_profile = profile
    if text and text not in profile:
        new_profile = (profile + " " + text).strip()[:400]
    await set_profile(user_id, new_profile)

    summary = await get_summary(user_id)
    updated = (summary + " " + answer).strip()[:500]
    await set_summary(user_id, updated)


async def get_personal_agent(user_id: str):
    return await get_agent_descriptor(user_id)


async def update_agent_permissions(user_id: str, tools_list: list[str] | None, permissions: dict[str, bool] | None):
    descriptor = await get_agent_descriptor(user_id)
    if tools_list is not None:
        descriptor.tools = tools_list
    if permissions is not None:
        descriptor.permissions.update(permissions)
    from memory import set_agent_descriptor  # local import to avoid cycles

    await set_agent_descriptor(user_id, descriptor)
    return descriptor


async def send_agent_message(event: AgentMessageEvent) -> dict:
    await save_agent_event(event.model_dump())
    return {"ok": True, "event_id": event.event_id}


async def ask_nexora(user_id: str, text: str, channel: str) -> str:
    if not await check_rate_limit(user_id):
        return "⚠️ Message rate limit reached. Please retry in one minute."

    agent = await get_agent_descriptor(user_id)
    settings = await get_agent_settings(user_id)
    history = await load_chat_memory(user_id)
    profile = await get_profile(user_id)
    summary = await get_summary(user_id)

    await save_chat_memory(user_id, "user", text)

    # No OpenAI configured -> graceful fallback
    if not openai_client:
        fallback = f"[{agent.agent_id} via {channel}] I received: {text}"
        await save_chat_memory(user_id, "assistant", fallback)
        await _refresh_profile_and_summary(user_id, text, fallback)
        return fallback

    enabled_tools = [
        item
        for item in tools
        if item["function"]["name"] in agent.tools and agent.permissions.get(item["function"]["name"], False)
    ]

    messages = [
        {
            "role": "system",
            "content": (
                f"{SYSTEM_PROMPT}\n"
                f"Profile: {profile}\n"
                f"Summary: {summary}\n"
                f"Channel: {channel}\n"
                f"Agent ID: {agent.agent_id}\n"
            ),
        },
        *history,
        {"role": "user", "content": text},
    ]

    try:
        response = await openai_client.chat.completions.create(
            model=settings.model or MODEL_NAME,
            temperature=settings.temperature,
            messages=messages,
            tools=enabled_tools,
            tool_choice="auto",
        )
        message = response.choices[0].message

        if message.tool_calls:
            tool_results = []
            for call in message.tool_calls:
                fn_name = call.function.name
                tool = TOOL_IMPLS.get(fn_name)
                if not tool:
                    tool_results.append(f"Tool not implemented: {fn_name}")
                    continue

                args = json.loads(call.function.arguments or "{}")
                if fn_name in {"manage_note_task", "schedule_reminder"} and "user_id" not in args:
                    args["user_id"] = user_id
                result = await tool(**args)
                tool_results.append(f"{fn_name}: {result}")

            final_text = "\n".join(tool_results)
        else:
            final_text = message.content or ""

    except Exception as exc:
        logger.exception("OpenAI request failed")
        final_text = f"Service fallback response: {text} ({exc})"

    await save_chat_memory(user_id, "assistant", final_text)
    await _refresh_profile_and_summary(user_id, text, final_text)
    return final_text
