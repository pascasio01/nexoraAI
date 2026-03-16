"""Main AI assistant logic shared by all channels."""

from __future__ import annotations

import json

from config import APP_NAME, CREATOR_ALIAS, CREATOR_NAME, MODEL_NAME, logger
from memory import MemoryStore
from tools_schema import ToolRegistry


class AICore:
    """Channel-agnostic assistant core."""

    def __init__(self, memory: MemoryStore, tools: ToolRegistry, openai_client=None) -> None:
        self.memory = memory
        self.tools = tools
        self.client = openai_client

    @property
    def system_prompt(self) -> str:
        return (
            f"You are {APP_NAME}, an AI assistant created by {CREATOR_NAME} ({CREATOR_ALIAS}). "
            "Be helpful, clear, and honest. Use tools when they provide real value."
        )

    async def _update_user_summary(self, user_id: str, text: str) -> None:
        current = await self.memory.get_memory_summary(user_id)
        combined = f"{current} {text}".strip()
        await self.memory.set_memory_summary(user_id, combined[-1000:])

    async def _fallback_reply(self, user_id: str, text: str, channel: str) -> str:
        profile = await self.memory.get_user_profile(user_id)
        return (
            "OpenAI is not configured right now. "
            f"I received your message through {channel}. Profile: {profile}. "
            "I can still store memory and run local tools."
        )

    async def _run_openai(self, user_id: str, session_id: str, text: str, channel: str) -> str:
        history = await self.memory.load_chat_history(user_id, session_id)
        profile = await self.memory.get_user_profile(user_id)
        summary = await self.memory.get_memory_summary(user_id)
        cfg = await self.memory.get_assistant_config(user_id)
        enabled_tools = cfg.get("enabled_tools") or []
        denied_tools = cfg.get("denied_tools") or []

        messages = [
            {
                "role": "system",
                "content": (
                    f"{self.system_prompt}\n"
                    f"Channel: {channel}\n"
                    f"User profile: {profile}\n"
                    f"Memory summary: {summary}\n"
                    "If you use tools, summarize outcomes clearly."
                ),
            },
            *history,
            {"role": "user", "content": text},
        ]

        tools = self.tools.list_schemas(enabled_tools, denied_tools)
        model = cfg.get("model") or MODEL_NAME
        temperature = float(cfg.get("temperature", 0.3))

        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools or None,
            temperature=temperature,
        )
        message = response.choices[0].message

        if not message.tool_calls:
            return message.content or "I do not have a response right now."

        normalized_tool_calls = [
            {
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.function.name,
                    "arguments": call.function.arguments,
                },
            }
            for call in message.tool_calls
        ]
        messages.append({"role": "assistant", "content": message.content or "", "tool_calls": normalized_tool_calls})
        for call in message.tool_calls:
            args = json.loads(call.function.arguments or "{}")
            tool_result = await self.tools.invoke(call.function.name, user_id, args)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "name": call.function.name,
                    "content": tool_result,
                }
            )

        second = await self.client.chat.completions.create(model=model, messages=messages, temperature=temperature)
        return second.choices[0].message.content or "Action executed without a textual response."

    async def ask(self, user_id: str, session_id: str, text: str, channel: str) -> str:
        if not await self.memory.check_rate_limit(user_id):
            return "⚠️ Message rate limit reached. Please wait one minute."

        await self.memory.save_chat_message(user_id, session_id, "user", text)
        await self._update_user_summary(user_id, text)

        try:
            if self.client is None:
                reply = await self._fallback_reply(user_id, text, channel)
            else:
                reply = await self._run_openai(user_id, session_id, text, channel)
        except Exception as exc:
            logger.exception("AI core error: %s", exc)
            reply = "I had a temporary issue while processing your request."

        await self.memory.save_chat_message(user_id, session_id, "assistant", reply)
        return reply
