import unittest

from nexoraAI.self_improvement_architecture import get_self_improvement_architecture


class SelfImprovementArchitectureTest(unittest.TestCase):
    def test_required_modules_are_defined(self):
        architecture = get_self_improvement_architecture()
        modules = architecture["modules"]

        self.assertIn("dev_agent", modules)
        self.assertIn("repair_agent", modules)
        self.assertIn("update_agent", modules)
        self.assertIn("task_orchestrator", modules)
        self.assertIn("self_improvement_engine", modules)

    def test_safety_rules_and_autonomy_levels(self):
        architecture = get_self_improvement_architecture()
        safety_rules = architecture["safety_rules"]
        autonomy_levels = architecture["autonomy_levels"]

        self.assertIn("Never silently change production code.", safety_rules)
        self.assertIn("Support rollback for every applied change.", safety_rules)
        self.assertIn("Require human approval for risky changes.", safety_rules)

        level_names = [level["level"] for level in autonomy_levels]
        self.assertEqual(
            level_names,
            [
                "analyze_only",
                "propose_changes",
                "create_branch_pr",
                "apply_safe_fixes_controlled_env",
            ],
        )

    def test_file_structure_and_roadmap_exist(self):
        architecture = get_self_improvement_architecture()

        self.assertGreater(len(architecture["suggested_file_structure"]), 5)
        self.assertGreater(len(architecture["implementation_roadmap"]), 3)


if __name__ == "__main__":
    unittest.main()
