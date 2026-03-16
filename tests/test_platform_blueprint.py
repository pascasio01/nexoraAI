import unittest

from nexoraAI.orchestrator import Orchestrator


class PlatformBlueprintTests(unittest.TestCase):
    def test_blueprint_contains_required_realtime_events(self):
        blueprint = Orchestrator().platform_blueprint()
        events = set(blueprint["realtime_contracts"]["events"])

        self.assertTrue(
            {
                "message.send",
                "message.receive",
                "message.delivered",
                "message.read",
                "typing.start",
                "typing.stop",
                "user.online",
                "user.offline",
                "assistant.state",
            }.issubset(events)
        )

    def test_blueprint_security_and_transfer_foundation(self):
        blueprint = Orchestrator().platform_blueprint()
        security = blueprint["security_architecture"]
        transfer = blueprint["file_transfer_architecture"]

        self.assertIn("e2ee_path", security)
        self.assertGreaterEqual(len(security["e2ee_path"]), 3)
        self.assertIn("future_interfaces", transfer)
        self.assertIn("local_wifi", transfer["future_interfaces"])
        self.assertIn("bluetooth", transfer["future_interfaces"])
        self.assertIn("qr_pairing", transfer["future_interfaces"])

    def test_blueprint_data_model_and_ids_for_continuity(self):
        blueprint = Orchestrator().platform_blueprint()
        continuity = blueprint["identity_and_continuity"]
        models = blueprint["data_model_suggestions"]

        self.assertIn("user_id", continuity["primary_ids"])
        self.assertIn("session_id", continuity["primary_ids"])
        self.assertIn("device_id", continuity["primary_ids"])
        self.assertIn("room_id", continuity["primary_ids"])
        self.assertIn("devices", models)
        self.assertIn("messages", models)
        self.assertIn("attachments", models)


if __name__ == "__main__":
    unittest.main()
