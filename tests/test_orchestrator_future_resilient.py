import unittest

from nexoraAI.orchestrator import Orchestrator


class FutureResilientOrchestratorTests(unittest.TestCase):
    def test_blueprint_covers_future_domains(self):
        blueprint = Orchestrator().build_future_resilient_blueprint()

        architecture = blueprint["architecture_proposal"]
        integrations = blueprint["integration_capabilities"]

        self.assertIn("future AR/VR/spatial devices", architecture["interaction_surfaces"])
        self.assertIn("smart grids", integrations["energy_and_edge"])
        self.assertIn("collaborative robotics APIs", integrations["industry_5_0"])
        self.assertIn("wearable health monitoring", integrations["healthtech"])
        self.assertIn("autonomous vehicles", integrations["autonomous_systems"])

    def test_security_framework_is_crypto_agile(self):
        framework = Orchestrator().build_future_resilient_blueprint()["security_framework"]

        self.assertIn("post-quantum", framework["encryption_strategy"].lower())
        self.assertIn("hybrid key exchange compatibility", framework["key_management"])
        self.assertIn("decision trace for recommendations", framework["explainability"])

    def test_product_strategy_has_four_stages(self):
        roadmap = Orchestrator().implementation_roadmap()

        self.assertEqual(4, len(roadmap))
        self.assertIn("Stage 1 — conversational assistant", roadmap)
        self.assertIn("Stage 4 — collaborative digital partner", roadmap)

    def test_start_and_stop_control_runtime_state(self):
        orchestrator = Orchestrator()
        self.assertFalse(orchestrator.running)

        orchestrator.start()
        self.assertTrue(orchestrator.running)

        orchestrator.stop()
        self.assertFalse(orchestrator.running)


if __name__ == "__main__":
    unittest.main()
