import unittest

from nexoraAI.device_ecosystem_blueprint import build_device_ecosystem_blueprint


class DeviceEcosystemBlueprintTests(unittest.TestCase):
    def test_blueprint_includes_required_capability_domains(self):
        blueprint = build_device_ecosystem_blueprint()
        capabilities = blueprint["capabilities"]

        expected_domains = {
            "cross_device_continuity",
            "realtime_system",
            "voice_readiness",
            "hybrid_cloud_device_intelligence",
            "privacy_and_security",
            "assistant_presence",
            "system_integration_readiness",
            "file_and_device_transfer",
            "multimodal_io",
            "personal_agent_per_user",
            "tool_system",
            "offline_and_resilience",
            "agent_to_agent_readiness",
        }

        self.assertTrue(expected_domains.issubset(set(capabilities)))

    def test_blueprint_separates_now_vs_deferred_work(self):
        blueprint = build_device_ecosystem_blueprint()

        add_now = blueprint["add_now"]
        defer_for_later = blueprint["defer_for_later"]

        self.assertIn("device-scoped session model with revocation endpoints", add_now)
        self.assertIn("agent-to-agent federation network", defer_for_later)
        self.assertGreaterEqual(len(add_now), 5)
        self.assertGreaterEqual(len(defer_for_later), 4)
        self.assertTrue(set(add_now).isdisjoint(set(defer_for_later)))

    def test_blueprint_has_multi_phase_roadmap(self):
        roadmap = build_device_ecosystem_blueprint()["roadmap"]
        phases = [phase["phase"] for phase in roadmap]

        self.assertEqual(
            phases,
            ["phase_1_foundation", "phase_2_experience", "phase_3_expansion"],
        )


if __name__ == "__main__":
    unittest.main()
