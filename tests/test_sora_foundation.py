import unittest

from fastapi.testclient import TestClient

from app import app


class TestSoraFoundationIntegration(unittest.TestCase):
    def test_safe_startup_health(self):
        with TestClient(app) as client:
            data = client.get("/health").json()
            self.assertEqual(data["status"], "ok")
            self.assertIn("openai", data)
            self.assertIn("redis", data)
            self.assertIn("telegram", data)

    def test_user_scoped_profile_settings_memory_and_agent(self):
        with TestClient(app) as client:
            profile = client.post(
                "/assistant-profile", json={"user_id": "u1", "profile": "Loves productivity"}
            ).json()
            self.assertTrue(profile["ok"])

            settings = client.post(
                "/assistant-settings", json={"user_id": "u1", "settings": {"voice_enabled": False}}
            ).json()
            self.assertEqual(settings["settings"]["voice_enabled"], False)

            memory = client.post(
                "/personal-memory", json={"user_id": "u1", "memory": "User prefers concise answers"}
            ).json()
            self.assertEqual(memory["memory_count"], 1)

            agent = client.get("/agents/u1").json()
            self.assertEqual(agent["user_id"], "u1")
            self.assertEqual(agent["profile"], "Loves productivity")

    def test_chat_and_tools(self):
        with TestClient(app) as client:
            chat = client.post(
                "/chat", json={"user_id": "u2", "message": "hello", "channel": "web"}
            ).json()
            self.assertIn("reply", chat)

            note = client.post(
                "/tools/execute",
                json={
                    "user_id": "u2",
                    "tool_name": "create_note",
                    "arguments": {"title": "Idea", "content": "Build Sora avatar"},
                },
            ).json()
            self.assertTrue(note["ok"])


if __name__ == "__main__":
    unittest.main()
