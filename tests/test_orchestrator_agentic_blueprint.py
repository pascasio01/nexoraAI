import unittest

from nexoraAI.orchestrator import Orchestrator


class TestOrchestratorAgenticBlueprint(unittest.TestCase):
    def test_four_layer_architecture_is_defined(self):
        blueprint = Orchestrator().get_agentic_platform_blueprint()
        architecture = blueprint["four_layer_agent_architecture"]

        self.assertIn("layer_1_persistent_graph_memory", architecture)
        self.assertIn("layer_2_action_layer_tools", architecture)
        self.assertIn("layer_3_multi_step_reasoning_engine", architecture)
        self.assertIn("layer_4_verification_layer", architecture)

    def test_action_execution_and_workflow_automation_focus(self):
        blueprint = Orchestrator().get_agentic_platform_blueprint()
        required_capabilities = blueprint["competitive_landscape"]["assistant_capabilities_required"]

        self.assertIn("Autonomous task completion", required_capabilities)
        self.assertEqual(
            blueprint["workflow_automation"]["maintenance_issue_workflow"],
            [
                "Retrieve technical documentation",
                "Identify required repair",
                "Notify technician",
                "Generate repair report",
                "Store historical record",
            ],
        )

    def test_specialization_privacy_and_trust_principles_are_present(self):
        blueprint = Orchestrator().get_agentic_platform_blueprint()

        self.assertIn(
            "technical maintenance systems",
            blueprint["strategic_differentiation"]["priority_domains"],
        )
        self.assertIn(
            "self-hosted deployments",
            blueprint["privacy_strategy"]["controls"],
        )
        self.assertIn(
            "admit_when_unknown",
            blueprint["product_philosophy"],
        )


if __name__ == "__main__":
    unittest.main()
