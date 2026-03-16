import unittest

from nexoraAI.orchestrator import Orchestrator


class AgenticPlatformBlueprintTests(unittest.TestCase):
    def test_blueprint_covers_core_2026_2030_requirements(self):
        blueprint = Orchestrator().get_blueprint()

        self.assertEqual(blueprint["agentic_core"]["type"], "action_agent")
        self.assertIn("workflow_execution", blueprint["agentic_core"]["capabilities"])
        self.assertIn("memory_agent", blueprint["multi_agent_architecture"]["specialized_agents"])
        self.assertIn("long_term_life_memory", blueprint["memory_system"]["layers"])
        self.assertIn("privacy_sensitive_tasks", blueprint["hybrid_ai"]["on_device_ai"])
        self.assertIn("video_ready", blueprint["multimodal_interaction"]["supported_inputs"])
        self.assertIn("assistant.thinking", blueprint["realtime_system"]["events"])
        self.assertIn("conversation_id", blueprint["cross_device_continuity"]["identity_entities"])
        self.assertEqual(blueprint["security_model"]["sensitive_action_policy"], "never_execute_silently")

    def test_autonomy_levels_and_logging_contract_exist(self):
        blueprint = Orchestrator().get_blueprint()
        autonomy_levels = blueprint["autonomy_levels"]
        level_names = {item["level"]: item["name"] for item in autonomy_levels}

        self.assertEqual(level_names[0], "suggestion_only")
        self.assertEqual(level_names[3], "bounded_autonomy")
        self.assertIn("action_log", blueprint["implementation_strategy"]["data_models"])

    def test_trip_goal_workflow_reflects_action_orchestration(self):
        workflow = Orchestrator().plan_goal_workflow(
            "Organize my trip to Japan within a $2000 budget.", budget_usd=2000
        )

        self.assertEqual(workflow["constraints"]["budget_usd"], 2000)
        self.assertIn("task.decompose", workflow["orchestration_flow"])
        self.assertEqual(
            workflow["sample_trip_workflow"],
            [
                "search_flights",
                "compare_hotels",
                "generate_itinerary",
                "present_options",
                "confirm_with_user",
                "complete_booking_actions",
            ],
        )


if __name__ == "__main__":
    unittest.main()
