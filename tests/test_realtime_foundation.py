import unittest

from fastapi.testclient import TestClient

from app import app


class RealtimeFoundationTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_http_health_and_chat(self):
        self.assertEqual(self.client.get("/health").status_code, 200)
        response = self.client.post("/chat", json={"texto": "hola", "usuario": "u1"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("respuesta", response.json())

    def test_ws_message_flow_emits_states_and_assistant_message(self):
        with self.client.websocket_connect("/ws?user_id=u1&session_id=s1") as ws:
            first_event = ws.receive_json()
            self.assertEqual(first_event["event"], "assistant.state")
            self.assertEqual(first_event["data"]["state"], "idle")

            ws.send_json({"event": "message.user", "data": {"text": "hello realtime"}})
            events = []
            for _ in range(20):
                event = ws.receive_json()
                events.append(event)
                if event["event"] == "assistant.state" and event["data"].get("state") == "idle":
                    break
            event_types = [event["event"] for event in events]

            self.assertIn("message.user", event_types)
            self.assertIn("assistant.state", event_types)
            self.assertIn("typing.start", event_types)
            self.assertIn("message.assistant", event_types)
            self.assertIn("typing.stop", event_types)

            assistant_messages = [event for event in events if event["event"] == "message.assistant"]
            self.assertTrue(assistant_messages)
            self.assertIn("text", assistant_messages[0]["data"])


if __name__ == "__main__":
    unittest.main()
