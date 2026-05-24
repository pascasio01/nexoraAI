import unittest

from nexoraAI.orchestrator import AgentEvent, Orchestrator


class OrchestratorTests(unittest.TestCase):
    def test_get_or_create_agent_creates_personal_agent_for_new_user(self):
        orchestrator = Orchestrator()
        agent = orchestrator.get_or_create_agent("new-user")
        self.assertEqual(agent.user_id, "new-user")
        self.assertEqual(agent.received_events, [])

    def test_get_or_create_agent_reuses_existing_user_agent(self):
        orchestrator = Orchestrator()
        a1 = orchestrator.get_or_create_agent("user-1")
        a2 = orchestrator.get_or_create_agent("user-1")
        self.assertIs(a1, a2)

    def test_request_task_creates_expected_event_payload(self):
        orchestrator = Orchestrator()
        orchestrator.start()

        event = orchestrator.request_task(
            source_user_id="user-1",
            target_user_id="user-2",
            task_name="summarize",
            task_payload={"doc_id": "abc"},
        )

        self.assertEqual(event.event_type, "task.requested")
        self.assertEqual(event.payload["task_name"], "summarize")
        self.assertEqual(event.payload["task_payload"]["doc_id"], "abc")
        receiver = orchestrator.get_or_create_agent("user-2")
        self.assertIn(event, receiver.received_events)

    def test_send_event_requires_running_orchestrator(self):
        orchestrator = Orchestrator()
        with self.assertRaises(RuntimeError):
            orchestrator.send_event(
                AgentEvent(
                    event_type="agent.message",
                    source_user_id="user-1",
                    target_user_id="user-2",
                    payload={"text": "hello"},
                )
            )

    def test_send_message_builds_and_routes_structured_event(self):
        orchestrator = Orchestrator()
        orchestrator.start()
        event = orchestrator.send_message(
            source_user_id="user-1",
            target_user_id="user-2",
            event_type="agent.message",
            payload={"text": "hello"},
        )
        self.assertEqual(event.event_type, "agent.message")
        self.assertEqual(event.source_user_id, "user-1")
        self.assertEqual(event.target_user_id, "user-2")
        self.assertEqual(event.payload, {"text": "hello"})


if __name__ == "__main__":
    unittest.main()
