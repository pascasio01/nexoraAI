import unittest

from nexoraAI.orchestrator import Orchestrator, build_nexora_2030_strategy


class Nexora2030StrategyTests(unittest.TestCase):
    def test_strategy_contains_required_top_level_sections(self):
        strategy = build_nexora_2030_strategy()
        self.assertIn("competitive_analysis_2030", strategy)
        self.assertIn("nexora_differentiation_strategy", strategy)
        self.assertIn("target_layered_architecture", strategy)
        self.assertIn("service_module_suggestions", strategy)
        self.assertIn("data_model_suggestions", strategy)
        self.assertIn("roadmap_phases", strategy)
        self.assertIn("risk_analysis_and_mitigations", strategy)
        self.assertIn("immediate_codebase_recommendations", strategy)

    def test_competitive_analysis_covers_major_companies_and_blind_spots(self):
        analysis = build_nexora_2030_strategy()["competitive_analysis_2030"]
        self.assertTrue({"apple", "google", "openai"}.issubset(set(analysis.keys())))
        blind_spots = " ".join(analysis["cross_ecosystem_blind_spots"]).lower()
        self.assertIn("memory", blind_spots)
        self.assertIn("fragmented", blind_spots)
        self.assertIn("trust", blind_spots)

    def test_layered_architecture_covers_required_layers(self):
        layers = build_nexora_2030_strategy()["target_layered_architecture"]
        for required in (
            "interface_layer",
            "api_gateway",
            "orchestrator",
            "reasoning_decision_engine",
            "memory_engine",
            "agent_layer",
            "tool_layer",
            "verification_layer",
            "security_layer",
        ):
            self.assertIn(required, layers)

    def test_orchestrator_exposes_strategy_blueprint(self):
        orchestrator = Orchestrator()
        self.assertFalse(orchestrator.active)
        self.assertTrue(orchestrator.start())
        self.assertFalse(orchestrator.stop())
        self.assertIn("roadmap_phases", orchestrator.strategy_blueprint())


if __name__ == "__main__":
    unittest.main()
