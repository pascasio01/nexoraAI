import unittest

from nexoraAI.orchestrator import Orchestrator


class OrchestratorDeviceStrategyTests(unittest.TestCase):
    def test_start_returns_running_state_and_blueprint(self):
        orchestrator = Orchestrator()

        payload = orchestrator.start()

        self.assertEqual(payload["status"], "running")
        self.assertIn("platform_blueprint", payload)
        self.assertIn("platform_targets", payload["platform_blueprint"])

    def test_stop_returns_stopped_status(self):
        orchestrator = Orchestrator()
        orchestrator.start()

        payload = orchestrator.stop()

        self.assertEqual(payload["status"], "stopped")


if __name__ == "__main__":
    unittest.main()

