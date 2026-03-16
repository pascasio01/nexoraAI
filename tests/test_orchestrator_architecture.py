import unittest

from nexoraAI.orchestrator import (
    Orchestrator,
    analyze_ai_assistant_ecosystem,
    build_evolution_roadmap,
    build_personal_intelligence_architecture,
)


class OrchestratorArchitectureTests(unittest.TestCase):
    def test_ecosystem_analysis_includes_key_assistants_and_gaps(self):
        analysis = analyze_ai_assistant_ecosystem()

        systems = {item["system"] for item in analysis["landscape"]}
        self.assertTrue({"ChatGPT", "Google Search", "Siri", "Alexa", "Gemini"}.issubset(systems))

        self.assertIn("lack of persistent life memory", analysis["major_gaps"])
        self.assertIn("lack of multi-agent orchestration", analysis["major_gaps"])

    def test_architecture_contains_required_core_layers(self):
        architecture = build_personal_intelligence_architecture()

        expected_sections = {
            "persistent_identity_layer",
            "orchestrator_core",
            "multi_agent_intelligence_system",
            "decision_engine",
            "life_memory_engine",
            "tool_execution_layer",
            "real_time_interaction_system",
            "personal_security_intelligence",
            "user_experience_design",
            "technology_architecture",
        }
        self.assertTrue(expected_sections.issubset(set(architecture.keys())))

        self.assertIn("phone", architecture["persistent_identity_layer"]["surfaces"])
        self.assertIn("future IoT devices", architecture["persistent_identity_layer"]["surfaces"])
        self.assertEqual(
            architecture["decision_engine"]["autonomy_levels"]["level_3"],
            "Execute automatically under strict safety rules",
        )

    def test_roadmap_has_six_phases(self):
        roadmap = build_evolution_roadmap()

        self.assertEqual(len(roadmap), 6)
        self.assertEqual(roadmap[0]["phase"], "Phase 1")
        self.assertEqual(roadmap[-1]["phase"], "Phase 6")

    def test_orchestrator_facade_builds_blueprint(self):
        orchestrator = Orchestrator()
        self.assertFalse(orchestrator.active)

        orchestrator.start()
        self.assertTrue(orchestrator.active)

        blueprint = orchestrator.build_blueprint()
        self.assertIn("major_gaps", blueprint.ecosystem_analysis)
        self.assertIn("technology_architecture", blueprint.platform_architecture)
        self.assertEqual(len(blueprint.evolution_roadmap), 6)

        orchestrator.stop()
        self.assertFalse(orchestrator.active)


if __name__ == "__main__":
    unittest.main()
