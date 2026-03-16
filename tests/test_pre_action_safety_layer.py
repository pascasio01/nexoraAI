import unittest

from nexoraAI.orchestrator import Orchestrator
from nexoraAI.pre_action_safety_layer import PreActionSafetyLayer


class PreActionSafetyLayerTests(unittest.TestCase):
    def test_structured_output_contains_required_fields(self):
        layer = PreActionSafetyLayer()

        result = layer.analyze_action(
            user_input="Please send the weekly report ASAP.",
            available_context={"network_trust": "safe", "session_protected": True, "device_trusted": True},
            action_metadata={"action_name": "send_report", "urgency": "high"},
        )

        expected_keys = {
            "detected_objective",
            "recommended_action",
            "alternative_options",
            "confidence_score",
            "potential_risks",
            "likely_consequences",
            "urgency",
            "best_next_step",
            "scenario_model",
            "secure_practices",
            "risk_severity",
            "requires_confirmation",
            "sensitive_action",
        }
        self.assertTrue(expected_keys.issubset(result.keys()))
        self.assertTrue(
            PreActionSafetyLayer.MIN_CONFIDENCE
            <= result["confidence_score"]
            <= PreActionSafetyLayer.MAX_CONFIDENCE
        )
        self.assertIn("optimistic_scenario", result["scenario_model"])
        self.assertIn("probable_scenario", result["scenario_model"])
        self.assertIn("risky_scenario", result["scenario_model"])

    def test_sensitive_action_requires_confirmation(self):
        layer = PreActionSafetyLayer()

        result = layer.analyze_action(
            user_input="Delete all customer history now.",
            available_context={"network_trust": "safe", "session_protected": True, "device_trusted": True},
            action_metadata={"action_name": "delete_data"},
        )

        self.assertTrue(result["requires_confirmation"])
        self.assertTrue(result["sensitive_action"])
        self.assertGreaterEqual(len(result["potential_risks"]), 1)

    def test_vpn_recommendation_is_security_framed(self):
        layer = PreActionSafetyLayer()

        result = layer.analyze_action(
            user_input="Send report from cafe wifi",
            available_context={"network_trust": "unsafe", "session_protected": False, "device_trusted": False},
            action_metadata={"action_name": "send_report"},
        )

        practices = result["secure_practices"]
        vpn_practice = next((item for item in practices if "vpn" in item.lower()), "")
        self.assertTrue(vpn_practice)
        vpn_practice_lower = vpn_practice.lower()
        self.assertIn("privacy", vpn_practice_lower)
        self.assertIn("security", vpn_practice_lower)
        self.assertIn("bypass", vpn_practice_lower)
        self.assertIn("rules", vpn_practice_lower)


class OrchestratorIntegrationTests(unittest.TestCase):
    def test_orchestrator_exposes_pre_action_review_and_blueprint(self):
        orchestrator = Orchestrator()
        review = orchestrator.review_before_action(
            user_input="Set a reminder for tomorrow",
            available_context={"network_trust": "safe", "session_protected": True, "device_trusted": True},
            action_metadata={"action_name": "set_reminder"},
        )
        blueprint = orchestrator.get_pre_action_architecture()

        self.assertEqual(review["detected_objective"], "Set a reminder")
        self.assertFalse(review["requires_confirmation"])
        self.assertEqual(review["risk_severity"], "low")
        self.assertEqual(review["potential_risks"], [])
        self.assertTrue(
            PreActionSafetyLayer.MIN_CONFIDENCE
            <= review["confidence_score"]
            <= PreActionSafetyLayer.MAX_CONFIDENCE
        )
        self.assertIn("architecture_for_pre_action_analysis", blueprint)
        self.assertIn("mvp_implementation_plan", blueprint)


if __name__ == "__main__":
    unittest.main()
