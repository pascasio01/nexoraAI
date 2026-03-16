import unittest

from nexoraAI.orchestrator import (
    Orchestrator,
    get_nexora_2030_blueprint,
    get_orchestrator_architecture,
    get_platform_blueprint,
)


class TestNexora2030Blueprint(unittest.TestCase):
    def test_blueprint_covers_required_cross_platform_scope(self):
        blueprint = get_nexora_2030_blueprint()
        expected_platforms = {
            "iPhone",
            "Android",
            "Web",
            "Desktop",
            "Wearables",
            "Smart devices",
            "Spatial computing devices",
        }
        self.assertTrue(expected_platforms.issubset(set(blueprint["platforms"])))

    def test_agentic_architecture_includes_multi_agent_orchestrator(self):
        architecture = get_orchestrator_architecture()
        self.assertEqual(architecture["orchestrator_model"], "multi-agent")
        self.assertIn("memory_agent", architecture["agents"])
        self.assertIn("security_agent", architecture["agents"])
        self.assertIn("notification_agent", architecture["agents"])

    def test_core_services_and_roadmaps_exist(self):
        blueprint = get_platform_blueprint()
        for service_key in (
            "api_gateway",
            "orchestrator",
            "decision_engine",
            "memory_engine",
            "messaging_service",
            "file_transfer_service",
            "security_service",
            "device_service",
            "notification_service",
            "voice_engine",
        ):
            self.assertIn(service_key, blueprint["core_services"])
        self.assertGreaterEqual(len(blueprint["mvp_roadmap"]), 4)
        self.assertGreaterEqual(len(blueprint["future_roadmap"]), 4)

    def test_orchestrator_lifecycle_exposes_agentic_mode(self):
        orchestrator = Orchestrator()
        started = orchestrator.start()
        self.assertEqual(started["status"], "running")
        self.assertEqual(started["mode"], "agentic")
        self.assertEqual(started["orchestrator_model"], "multi-agent")
        stopped = orchestrator.stop()
        self.assertEqual(stopped["status"], "stopped")


if __name__ == "__main__":
    unittest.main()
