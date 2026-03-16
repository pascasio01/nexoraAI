import json
import unittest
from collections.abc import AsyncGenerator
from unittest.mock import patch

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

        legacy_chat = self.client.post("/chat", json={"usuario": "u1", "texto": "hola legacy"})
        self.assertEqual(legacy_chat.status_code, 200)
        self.assertIn("reply", legacy_chat.json())

    def test_websocket_streams_state_and_chunks(self) -> None:
        with self.client.websocket_connect("/ws/roomA/session1?user_id=u1") as ws:
            joined = ws.receive_json()
            self.assertEqual(joined["event"], "session.joined")

            initial_state = ws.receive_json()
            self.assertEqual(initial_state["event"], "assistant.state")
            self.assertEqual(initial_state["state"], "idle")

            ws.send_text(json.dumps({"type": "chat", "message": "hello realtime"}))

            events = []
            while True:
                event = ws.receive_json()
                events.append(event)
                if event.get("event") == "assistant.response.complete":
                    break

            events.append(ws.receive_json())
            states = [e.get("state") for e in events if e.get("event") == "assistant.state"]
            self.assertIn("listening", states)
            self.assertIn("thinking", states)
            self.assertIn("responding", states)
            self.assertIn("idle", states)

            chunk_events = [e for e in events if e.get("event") == "assistant.response.chunk"]
            self.assertGreaterEqual(len(chunk_events), 1)
            complete = [e for e in events if e.get("event") == "assistant.response.complete"]
            self.assertEqual(len(complete), 1)
            reconstructed = "".join(e["chunk"] for e in chunk_events)
            self.assertEqual(reconstructed, complete[0]["message"])

    def test_voice_placeholder_ack(self) -> None:
        with self.client.websocket_connect("/ws/roomV/sessionV?user_id=u2") as ws:
            joined_event = ws.receive_json()
            initial_state_event = ws.receive_json()
            self.assertEqual(joined_event["event"], "session.joined")
            self.assertEqual(initial_state_event["event"], "assistant.state")
            ws.send_text(json.dumps({"type": "voice.input.chunk", "meta": {"seq": 1}}))
            ack = ws.receive_json()
            self.assertEqual(ack["event"], "voice.input.ack")
            self.assertEqual(ack["status"], "accepted")

    def test_empty_message_returns_error_event(self) -> None:
        with self.client.websocket_connect("/ws/roomE/sessionE?user_id=u3") as ws:
            _ = ws.receive_json()
            _ = ws.receive_json()
            ws.send_text(json.dumps({"type": "chat", "message": "   "}))
            error_event = ws.receive_json()
            self.assertEqual(error_event["event"], "error")
            self.assertEqual(error_event["code"], "empty_message")

    def test_websocket_internal_error_event(self) -> None:
        async def broken_stream(*args, **kwargs) -> AsyncGenerator[str, None]:  # pragma: no cover - testing failure path
            # keeps async-generator shape while forcing the runtime failure path
            if False:
                yield ""
            raise RuntimeError("forced stream failure")

        with patch("routes.stream_assistant_reply", broken_stream):
            with self.client.websocket_connect("/ws/roomX/sessionX?user_id=u4") as ws:
                _ = ws.receive_json()
                _ = ws.receive_json()
                ws.send_text(json.dumps({"type": "chat", "message": "trigger error"}))
                events = [ws.receive_json() for _ in range(4)]
                error_events = [event for event in events if event.get("event") == "error"]
                self.assertEqual(len(error_events), 1)
                self.assertEqual(error_events[0]["code"], "internal_error")


if __name__ == "__main__":
    unittest.main()
