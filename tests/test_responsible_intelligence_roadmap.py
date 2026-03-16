import unittest

from nexoraAI.orchestrator import Orchestrator


class TestResponsibleIntelligenceRoadmap(unittest.TestCase):
    def test_roadmap_has_required_sections(self):
        roadmap = Orchestrator().get_responsible_intelligence_roadmap()

        self.assertIn("prioritization", roadmap)
        self.assertIn("module_boundaries", roadmap)
        self.assertIn("architecture_proposal", roadmap)
        self.assertIn("phases", roadmap)
        self.assertIn("risks_and_mitigation", roadmap)
        self.assertIn("implementation_roadmap", roadmap)

    def test_prioritization_order_is_realistic(self):
        roadmap = Orchestrator().get_responsible_intelligence_roadmap()
        ordered_modules = [item["module"] for item in roadmap["prioritization"]]

        self.assertEqual(
            ordered_modules,
            [
                "Immutable Audit Log",
                "Stress Simulator",
                "Self-Healing Security Layer",
                "Negotiation Workflow Layer",
                "Spatial / Asset Intelligence Layer",
            ],
        )

    def test_stress_simulator_scope_mentions_requested_scenarios(self):
        roadmap = Orchestrator().get_responsible_intelligence_roadmap()
        scope = " ".join(roadmap["module_boundaries"]["stress_simulator"]["owns"]).lower()

        self.assertIn("rates", scope)
        self.assertIn("failures", scope)
        self.assertIn("vacancy", scope)
        self.assertIn("inflation", scope)
        self.assertIn("fines", scope)
        self.assertIn("ocf stress", scope)


if __name__ == "__main__":
    unittest.main()
