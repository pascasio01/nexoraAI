import unittest

from nexoraAI.orchestrator import Orchestrator


class ReminderPlugin:
    name = "reminder"

    def setup(self, orchestrator: Orchestrator) -> None:
        orchestrator.register_tool("create_reminder", lambda payload: f"reminder:{payload['title']}")


class OrchestratorFoundationTests(unittest.TestCase):
    def test_personal_agent_uses_memory_and_updates_long_term_memory(self):
        orchestrator = Orchestrator()
        seen_histories = []
        automation_events = []

        def coach_agent(user_text, context):
            seen_histories.append(list(context["history"]))
            return f"coach:{user_text}"

        orchestrator.register_agent("coach", coach_agent)
        orchestrator.set_personal_agent("u1", "coach")
        orchestrator.remember("u1", "assistant:welcome")
        orchestrator.register_automation("message_processed", lambda payload: automation_events.append(payload))

        response = orchestrator.run_personal_agent("u1", "hello")

        self.assertEqual(response, "coach:hello")
        self.assertEqual(seen_histories, [["assistant:welcome"]])
        self.assertEqual(
            orchestrator.recall("u1"),
            ["assistant:welcome", "user:hello", "assistant:coach:hello"],
        )
        self.assertEqual(automation_events, [{"user_id": "u1", "text": "hello"}])

    def test_tool_execution_and_plugin_registration(self):
        orchestrator = Orchestrator()
        orchestrator.register_plugin(ReminderPlugin())

        result = orchestrator.execute_tool("create_reminder", {"title": "pay rent"})

        self.assertEqual(result, "reminder:pay rent")
        self.assertEqual(orchestrator.registered_plugins(), ["reminder"])

    def test_multi_channel_dispatch(self):
        orchestrator = Orchestrator()
        sent = []

        def telegram_sender(user_id, message):
            sent.append((user_id, message))
            return "ok"

        orchestrator.register_channel("telegram", telegram_sender)

        output = orchestrator.send_message("telegram", "u2", "hola")

        self.assertEqual(output, "ok")
        self.assertEqual(sent, [("u2", "hola")])

    def test_validation_errors_for_unregistered_components(self):
        orchestrator = Orchestrator()
        orchestrator.remember("u3", "assistant:seed")

        with self.assertRaisesRegex(ValueError, "No personal agent"):
            orchestrator.run_personal_agent("u3", "hi")

        with self.assertRaisesRegex(ValueError, "Tool 'missing'"):
            orchestrator.execute_tool("missing")

        with self.assertRaisesRegex(ValueError, "Channel 'sms'"):
            orchestrator.send_message("sms", "u3", "hi")

        self.assertEqual(orchestrator.recall("u3", limit=0), [])


if __name__ == "__main__":
    unittest.main()
