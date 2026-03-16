import unittest

from nexoraAI.orchestrator import Orchestrator, build_security_awareness_alert_layer


class TestSecurityAwarenessAlertLayer(unittest.TestCase):
    def test_blueprint_contains_required_sections(self):
        blueprint = build_security_awareness_alert_layer()

        self.assertIn("architecture", blueprint)
        self.assertIn("modules_services", blueprint)
        self.assertIn("data_flow", blueprint)
        self.assertIn("alert_schema", blueprint)
        self.assertIn("trust_scoring_model", blueprint)
        self.assertIn("mvp_implementation_plan", blueprint)

    def test_alert_levels_and_required_fields(self):
        schema = build_security_awareness_alert_layer()["alert_schema"]
        self.assertEqual(
            schema["allowed_levels"],
            ["Safe", "Low Risk", "Medium Risk", "High Risk", "Critical"],
        )
        for required_field in (
            "title",
            "summary",
            "why_it_matters",
            "confidence_level",
            "recommended_action",
            "urgency",
        ):
            self.assertIn(required_field, schema["required_fields"])

    def test_privacy_first_vpn_rule_disallows_bypass_positioning(self):
        rules = build_security_awareness_alert_layer()["privacy_first_recommendation_rules"]
        vpn_policy = rules["vpn_guidance_policy"].lower()
        self.assertIn("privacy", vpn_policy)
        self.assertIn("security", vpn_policy)
        self.assertIn("never", vpn_policy)
        self.assertIn("bypass", vpn_policy)

    def test_orchestrator_exposes_security_awareness_blueprint(self):
        orchestrator = Orchestrator()
        self.assertEqual(orchestrator.start(), "running")
        blueprint = orchestrator.security_awareness_alert_layer()
        self.assertIn("developer_creator_protection", blueprint)
        self.assertIn("session_security_engine", blueprint["modules_services"])
        self.assertEqual(orchestrator.stop(), "stopped")


if __name__ == "__main__":
    unittest.main()
