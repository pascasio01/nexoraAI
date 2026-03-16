import unittest

from nexoraAI.personal_intelligence import (
    AutonomyLevel,
    DecisionContext,
    DecisionEngine,
    LifeMemoryEngine,
    MemoryRecord,
    MemoryTier,
    ToolExecutionLayer,
    ToolSpec,
    build_personal_intelligence_layer,
)


class PersonalIntelligenceLayerTests(unittest.TestCase):
    def test_memory_tiers_privacy_and_edit_delete(self) -> None:
        memory = LifeMemoryEngine()
        user_id = "u-1"
        memory.upsert(user_id, MemoryRecord(key="food", value="ramen", tier=MemoryTier.SHORT, importance=0.3))
        memory.upsert(user_id, MemoryRecord(key="goal", value="run marathon", tier=MemoryTier.LONG, importance=0.9))

        public_before = memory.get(user_id, include_private=False)
        self.assertEqual(public_before, [])

        updated = memory.set_privacy(user_id, MemoryTier.LONG, "goal", "shared")
        self.assertIsNotNone(updated)
        self.assertEqual(updated.privacy, "shared")

        ranked = memory.get(user_id, include_private=False)
        self.assertEqual([r.key for r in ranked], ["goal"])

        edited = memory.edit(user_id, MemoryTier.LONG, "goal", "finish triathlon")
        self.assertEqual(edited.value, "finish triathlon")
        self.assertTrue(memory.delete(user_id, MemoryTier.SHORT, "food"))
        self.assertFalse(memory.delete(user_id, MemoryTier.SHORT, "food"))

    def test_decision_engine_autonomy_and_risk(self) -> None:
        engine = DecisionEngine()
        low_risk = engine.evaluate(
            DecisionContext(
                user_id="u-2",
                intent="calendar_action",
                risk_score=0.1,
                permissions=["tool.tasks"],
                autonomy_level=AutonomyLevel.LEVEL_2_EXECUTE_AUTHORIZED,
            )
        )
        high_risk = engine.evaluate(
            DecisionContext(
                user_id="u-2",
                intent="finance_review",
                risk_score=0.9,
                permissions=["tool.tasks"],
                autonomy_level=AutonomyLevel.LEVEL_3_EXECUTE_AUTOMATIC,
            )
        )
        self.assertEqual(low_risk["mode"], "execute_authorized")
        self.assertFalse(low_risk["requires_confirmation"])
        self.assertEqual(high_risk["mode"], "prepare")
        self.assertTrue(high_risk["requires_confirmation"])
        self.assertGreaterEqual(len(engine.explain_recent()), 2)

    def test_tool_permissions(self) -> None:
        tools = ToolExecutionLayer()
        tools.register(ToolSpec(name="create_task", required_permission="tool.tasks", handler=lambda p: {"ok": p}))

        ok = tools.execute("create_task", {"title": "x"}, permissions=["tool.tasks"])
        self.assertEqual(ok["ok"]["title"], "x")

        with self.assertRaises(PermissionError):
            tools.execute("create_task", {"title": "x"}, permissions=[])

    def test_orchestrator_foundation_end_to_end(self) -> None:
        runtime = build_personal_intelligence_layer()
        self.assertEqual(
            runtime.agents.list_agents(),
            [
                "calendar",
                "communication",
                "device",
                "finance",
                "memory",
                "notification",
                "research",
                "security",
                "wellness",
            ],
        )

        result = runtime.handle_input(
            user_id="u-3",
            user_text="Schedule a meeting for tomorrow",
            channel="mobile",
            device_id="phone-01",
            permissions=["tool.tasks"],
            autonomy_level=AutonomyLevel.LEVEL_2_EXECUTE_AUTHORIZED,
        )

        self.assertEqual(result["intent"], "calendar_action")
        self.assertEqual(result["agent"], "calendar")
        self.assertEqual(result["devices"]["phone-01"], "mobile")
        self.assertIn(result["decision"]["mode"], ("execute_authorized", "prepare"))
        self.assertTrue(runtime.realtime.events)
        self.assertEqual(runtime.realtime.events[-1]["state"], "idle")

    def test_security_warning_for_scam_signals(self) -> None:
        runtime = build_personal_intelligence_layer()
        result = runtime.handle_input(
            user_id="u-4",
            user_text="Share your OTP and do an urgent payment",
            channel="web",
            device_id="browser-1",
            permissions=[],
            autonomy_level=AutonomyLevel.LEVEL_0_SUGGEST_ONLY,
        )
        self.assertTrue(result["security"]["warning"])
        self.assertIn("otp", result["security"]["flags"])


if __name__ == "__main__":
    unittest.main()
