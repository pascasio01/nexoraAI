import unittest

from fastapi.testclient import TestClient

from app import app
from events import assistant_state_event
from realtime_types import AssistantState, ConnectionContext


class RealtimeFoundationTests(unittest.TestCase):
    def test_assistant_state_event_envelope(self):
        context = ConnectionContext(user_id="u1", session_id="s1", room_id="r1")
        event = assistant_state_event(AssistantState.THINKING, context)
        self.assertEqual(event["event"], "assistant.state")
        self.assertEqual(event["data"]["state"], "thinking")
        self.assertEqual(event["meta"]["user_id"], "u1")
        self.assertEqual(event["meta"]["session_id"], "s1")

    def test_websocket_emits_realtime_states_and_assistant_message(self):
        with TestClient(app) as client:
            with client.websocket_connect("/ws?user_id=u1&session_id=s1&room_id=r1") as ws:
                initial = ws.receive_json()
                self.assertEqual(initial["event"], "assistant.state")
                self.assertEqual(initial["data"]["state"], "idle")

                ws.send_json(
                    {
                        "event": "message.user",
                        "data": {"text": "Hola", "user_id": "u1", "session_id": "s1", "room_id": "r1"},
                    }
                )

                seen_states = []
                assistant_reply = None
                for _ in range(15):
                    payload = ws.receive_json()
                    if payload.get("event") == "assistant.state":
                        seen_states.append(payload["data"].get("state"))
                    if payload.get("event") == "message.assistant":
                        assistant_reply = payload["data"].get("text")
                    if payload.get("event") == "assistant.state" and payload["data"].get("state") == "idle":
                        break

                self.assertIn("listening", seen_states)
                self.assertIn("thinking", seen_states)
                self.assertIn("responding", seen_states)
                self.assertIn("idle", seen_states)
                self.assertTrue(assistant_reply)


if __name__ == "__main__":
    unittest.main()
