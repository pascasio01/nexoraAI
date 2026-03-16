import json
import unittest

from fastapi.testclient import TestClient

from app import app


class RealtimeFoundationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_http_health_and_chat(self) -> None:
        health = self.client.get("/health")
        self.assertEqual(health.status_code, 200)

        chat = self.client.post("/chat", json={"user_id": "u1", "message": "hola"})
        self.assertEqual(chat.status_code, 200)
        self.assertIn("reply", chat.json())

    def test_websocket_streams_state_and_chunks(self) -> None:
        with self.client.websocket_connect("/ws/roomA/session1?user_id=u1") as ws:
            joined = ws.receive_json()
            self.assertEqual(joined["event"], "session.joined")

            initial_state = ws.receive_json()
            self.assertEqual(initial_state["event"], "assistant.state")
            self.assertEqual(initial_state["state"], "idle")

            ws.send_text(json.dumps({"type": "chat", "message": "hello realtime"}))

            events = [ws.receive_json() for _ in range(8)]
            states = [e.get("state") for e in events if e.get("event") == "assistant.state"]
            self.assertIn("listening", states)
            self.assertIn("thinking", states)
            self.assertIn("responding", states)
            self.assertIn("idle", states)

            chunk_events = [e for e in events if e.get("event") == "assistant.response.chunk"]
            self.assertGreaterEqual(len(chunk_events), 1)
            complete = [e for e in events if e.get("event") == "assistant.response.complete"]
            self.assertEqual(len(complete), 1)

    def test_voice_placeholder_ack(self) -> None:
        with self.client.websocket_connect("/ws/roomV/sessionV?user_id=u2") as ws:
            _ = ws.receive_json()
            _ = ws.receive_json()
            ws.send_text(json.dumps({"type": "voice.input.chunk", "meta": {"seq": 1}}))
            ack = ws.receive_json()
            self.assertEqual(ack["event"], "voice.input.ack")
            self.assertEqual(ack["status"], "accepted")


if __name__ == "__main__":
    unittest.main()
