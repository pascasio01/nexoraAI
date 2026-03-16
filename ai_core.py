from __future__ import annotations

import html

from config import settings
from tools_impl import ToolExecutor

MAX_SAFE_MESSAGE_LENGTH = 500


class AgentManager:
    def __init__(self, memory_store, openai_client=None, tool_executor: ToolExecutor | None = None):
        self.memory_store = memory_store
        self.openai_client = openai_client
        self.tool_executor = tool_executor

    def get_or_create_agent(self, user_id: str) -> dict:
        state = self.memory_store.ensure_user(user_id)
        return {
            "user_id": user_id,
            "profile": state.profile,
            "settings": state.settings,
            "tools": [
                "web_search",
                "create_note",
                "create_task",
                "create_reminder",
                "webhook_action",
            ],
        }

    async def route_request(self, user_id: str, message: str, channel: str = "web") -> str:
        self.memory_store.add_message(user_id, "user", message, channel)
        response_text = await self._generate_response(user_id=user_id, message=message, channel=channel)
        self.memory_store.add_message(user_id, "assistant", response_text, channel)
        return response_text

    async def execute_tool(self, user_id: str, tool_name: str, arguments: dict) -> dict:
        if not self.tool_executor:
            return {"ok": False, "message": "Tool executor unavailable."}
        tool = getattr(self.tool_executor, tool_name, None)
        if not callable(tool):
            return {"ok": False, "message": f"Unknown tool '{tool_name}'."}
        return await tool(user_id=user_id, **arguments)

    async def _generate_response(self, user_id: str, message: str, channel: str) -> str:
        profile = self.memory_store.get_profile(user_id)
        long_term = self.memory_store.get_long_term_memory(user_id)
        if not self.openai_client:
            prefix = "[safe-fallback]"
            details = f"channel={channel}; profile={'set' if profile else 'empty'}; ltm={len(long_term)}"
            safe_message = html.escape(message.strip())[:MAX_SAFE_MESSAGE_LENGTH]
            return f"{prefix} {details}. You said: {safe_message}"

        history = self.memory_store.get_history(user_id)
        prompt = (
            f"You are Sora, the personal assistant for user {user_id}. "
            f"Channel: {channel}. Profile: {profile or 'none'}. "
            f"Long-term memories: {long_term[-5:] if long_term else []}."
        )
        messages = [{"role": "system", "content": prompt}] + [
            {"role": item["role"], "content": item["content"]} for item in history[-8:]
        ]
        completion = await self.openai_client.chat.completions.create(
            model=settings.model_name,
            messages=messages,
            max_tokens=300,
        )
        return completion.choices[0].message.content or ""
