import unittest

from nexoraAI.orchestrator import Orchestrator


class TestLevel3Architecture(unittest.TestCase):
    def test_architecture_includes_all_required_capability_domains(self):
        architecture = Orchestrator().get_architecture()
        capabilities = architecture["capabilities"]

        expected_domains = {
            "knowledge_graph_memory",
            "agentic_workflows",
            "multimodal_reasoning",
            "cross_ecosystem_interoperability",
            "post_quantum_security",
            "proactive_intelligence",
            "self_verification_system",
            "micro_agent_orchestration",
            "sensor_and_location_memory",
            "agent_to_agent_negotiation",
            "custom_ethical_guardrails",
            "adaptive_interface",
        }
        self.assertTrue(expected_domains.issubset(set(capabilities.keys())))

    def test_knowledge_graph_memory_models_long_horizon_relationships(self):
        kg_memory = Orchestrator().get_architecture()["capabilities"]["knowledge_graph_memory"]

        self.assertIn("people", kg_memory["entities"])
        self.assertIn("documents", kg_memory["entities"])
        self.assertIn("depends_on", kg_memory["relationships"])
        self.assertEqual(
            kg_memory["example_chain"],
            [
                "Basement leak in March",
                "Repair budget for June",
                "Maintenance contract renewal",
            ],
        )

    def test_security_verification_and_guardrails_are_explicit(self):
        capabilities = Orchestrator().get_architecture()["capabilities"]

        pq_security = capabilities["post_quantum_security"]
        self.assertIn("CRYSTALS-Kyber", pq_security["algorithms"])
        self.assertIn("Dilithium", pq_security["algorithms"])
        self.assertIn("Falcon", pq_security["algorithms"])

        verification = capabilities["self_verification_system"]
        self.assertIn("confidence_scoring", verification["methods"])
        self.assertIn("explicit uncertainty", verification["low_confidence_policy"])

        guardrails = capabilities["custom_ethical_guardrails"]
        self.assertIn("biometric confirmation", guardrails["example_rule"])

    def test_start_and_stop_expose_operational_state(self):
        orchestrator = Orchestrator()

        start_result = orchestrator.start()
        self.assertEqual(start_result["status"], "running")
        self.assertEqual(start_result["mode"], "level-3-agent")
        self.assertIn("architecture", start_result)

        stop_result = orchestrator.stop()
        self.assertEqual(stop_result, {"status": "stopped", "mode": "level-3-agent"})


if __name__ == "__main__":
    unittest.main()
