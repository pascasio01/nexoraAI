import unittest

from nexoraAI.orchestrator import Orchestrator


class TestOrchestratorArchitecture(unittest.TestCase):
    def test_lifecycle_controls_running_state(self):
        orchestrator = Orchestrator()
        self.assertFalse(orchestrator.is_running)
        self.assertEqual(orchestrator.start(), "orchestrator_started")
        self.assertTrue(orchestrator.is_running)
        self.assertEqual(orchestrator.stop(), "orchestrator_stopped")
        self.assertFalse(orchestrator.is_running)

    def test_level3_architecture_contains_all_required_sections(self):
        blueprint = Orchestrator().level3_architecture()
        sections = blueprint["sections"]
        self.assertEqual(blueprint["agent_level"], "L3")
        self.assertEqual(len(sections), 12)
        section_names = {section["name"] for section in sections}
        self.assertSetEqual(
            section_names,
            {
                "Knowledge Graph Memory",
                "Agentic Workflows",
                "Multimodal Reasoning",
                "Cross-Ecosystem Interoperability",
                "Post-Quantum Security",
                "Proactive Intelligence",
                "Self-Verification System",
                "Micro-Agent Orchestration",
                "Sensor and Location Memory",
                "Agent-to-Agent Negotiation",
                "Custom Ethical Guardrails",
                "Adaptive Interface",
            },
        )

    def test_blueprint_includes_pqc_and_uncertainty_controls(self):
        sections = Orchestrator().level3_architecture()["sections"]
        post_quantum = next(
            section for section in sections if section["name"] == "Post-Quantum Security"
        )
        self.assertIn("CRYSTALS-Kyber", " ".join(post_quantum["components"]))
        self.assertIn("Dilithium", " ".join(post_quantum["components"]))
        self.assertIn("Falcon", " ".join(post_quantum["components"]))

        self_verification = next(
            section for section in sections if section["name"] == "Self-Verification System"
        )
        self.assertIn(
            "Confidence scoring with explicit uncertainty when below threshold",
            self_verification["capabilities"],
        )


if __name__ == "__main__":
    unittest.main()
