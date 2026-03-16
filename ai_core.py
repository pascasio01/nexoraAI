from __future__ import annotations

import json
from typing import Any, Dict, List

from config import APP_NAME, CREATOR_ALIAS, CREATOR_NAME, MODEL_NAME, logger
from deps import get_openai_client
from memory import check_rate_limit, get_profile, load_chat_memory, save_chat_memory, set_profile
from tools_impl import execute_action, manage_note, search_web
from tools_schema import tools

SYSTEM_PROMPT = f"""
You are {APP_NAME}, an advanced personal AI assistant created by {CREATOR_NAME} ({CREATOR_ALIAS}).
Rules:
- Be accurate and practical.
- Use available tools only when helpful.
- If a service is not configured, explain that clearly and continue gracefully.
- Keep answers concise and user-friendly.
""".strip()


async def _run_tool(name: str, args: Dict[str, Any]) -> Any:
    if name == "search_web":
        return await search_web(args.get("query", ""))
    if name == "manage_note":
        return await manage_note(args.get("title", ""), args.get("content", ""))
    if name == "execute_action":
        return await execute_action(args.get("action_name", "generic_action"), args.get("details", {}))
    return {"error": f"Unknown tool: {name}"}


def _should_search(text: str) -> bool:
    keywords = ("today", "latest", "news", "search", "web", "actual")
    lower = text.lower()
    return any(word in lower for word in keywords)


async def _maybe_update_profile(user_id: str, text: str) -> None:
    lower = text.lower()
    if "my name is" in lower or "i am" in lower:
        current = await get_profile(user_id)
        updated = f"{current}\n{text}".strip() if current else text
        await set_profile(user_id, updated[:1000])


async def ask_nexora(user_id: str, text: str, channel: str = "web") -> str:
    clean_text = (text or "").strip()
    if not clean_text:
        return "Please send a message so I can help you."

    if not await check_rate_limit(user_id):
        return "⚠️ Message rate limit reached. Please wait a minute and try again."

    await _maybe_update_profile(user_id, clean_text)

    history = await load_chat_memory(user_id)
    profile = await get_profile(user_id)
    base_messages: List[Dict[str, str]] = [
        {
            "role": "system",
            "content": f"{SYSTEM_PROMPT}\nChannel: {channel}\nUser profile: {profile or 'No profile data yet.'}",
        }
    ]
    base_messages.extend(history)
    base_messages.append({"role": "user", "content": clean_text})

    client = get_openai_client()
    if client is None:
        if _should_search(clean_text):
            results = await search_web(clean_text)
            if results and "error" not in results[0]:
                top = results[0]
                answer = f"OpenAI is not configured, but I found this: {top.get('title')} - {top.get('url')}"
            else:
                answer = "OpenAI is not configured and web search is unavailable right now."
        else:
            answer = "OpenAI is not configured yet. I can still keep context and basic assistant behavior online."
        await save_chat_memory(user_id, "user", clean_text)
        await save_chat_memory(user_id, "assistant", answer)
        return answer

    try:
        completion = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=base_messages,
            tools=tools,
            tool_choice="auto",
        )

        message = completion.choices[0].message
        tool_calls = message.tool_calls or []
        conversation: List[Dict[str, Any]] = list(base_messages)

        if message.content:
            conversation.append({"role": "assistant", "content": message.content})

        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            try:
                arguments = json.loads(tool_call.function.arguments or "{}")
            except json.JSONDecodeError:
                arguments = {}
            tool_result = await _run_tool(tool_name, arguments)
            conversation.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result, ensure_ascii=False),
                }
            )

        if tool_calls:
            followup = await client.chat.completions.create(model=MODEL_NAME, messages=conversation)
            answer = (followup.choices[0].message.content or "").strip() or "Done."
        else:
            answer = (message.content or "").strip() or "Done."

    except Exception as exc:
        logger.warning("ask_nexora fallback due to OpenAI issue: %s", exc)
        answer = "I could not reach the AI provider right now. Please try again in a moment."

    await save_chat_memory(user_id, "user", clean_text)
    await save_chat_memory(user_id, "assistant", answer)
    return answer
