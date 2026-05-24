import unittest

from nexoraAI.decision_engine import AutonomyLevel, DecisionContext, DecisionEngine
from nexoraAI.memory_engine import MemoryEngine
from nexoraAI.orchestrator import Orchestrator


class DecisionEngineTests(unittest.TestCase):
    def test_level_zero_is_suggest_only(self):
        engine = DecisionEngine()
        result = engine.evaluate(
            "calendar",
            DecisionContext(
                permissions={"calendar": True},
                autonomy_level=AutonomyLevel.LEVEL_0_SUGGEST_ONLY,
                risk=1,
                priority=5,
            ),
        )
        self.assertFalse(result.should_execute)
        self.assertEqual(result.mode, "suggest_only")

    def test_level_three_blocks_high_risk(self):
        engine = DecisionEngine(max_auto_risk=2)
        result = engine.evaluate(
            "device",
            DecisionContext(
                permissions={"device": True},
                autonomy_level=AutonomyLevel.LEVEL_3_EXECUTE_AUTOMATICALLY,
                risk=6,
                priority=8,
            ),
        )
        self.assertFalse(result.should_execute)
        self.assertEqual(result.mode, "auto_execute_restricted")


class MemoryEngineTests(unittest.TestCase):
    def test_structured_knowledge_extraction(self):
        memory = MemoryEngine()
        memory.record_interaction(
            user_id="u1",
            user_text="I prefer tea. My goal is to run a marathon. Remember to book the doctor.",
            assistant_text="Noted.",
        )
        context = memory.get_memory_context("u1")
        self.assertEqual(len(context["knowledge"]["preferences"]), 1)
        self.assertEqual(len(context["knowledge"]["goals"]), 1)
        self.assertEqual(len(context["knowledge"]["tasks"]), 1)


class OrchestratorTests(unittest.IsolatedAsyncioTestCase):
    async def test_orchestrator_routes_and_combines(self):
        orchestrator = Orchestrator()
        result = await orchestrator.process(
            user_id="u2",
            user_input="Please schedule a calendar meeting for tomorrow.",
            autonomy_level=AutonomyLevel.LEVEL_2_EXECUTE_WITH_PRIOR_PERMISSION,
            permissions={"calendar": True},
            has_prior_permission=True,
        )
        self.assertEqual(result.intent, "calendar")
        self.assertTrue(result.should_execute)
        self.assertIn("calendar_agent", result.agent_outputs)
        self.assertIn("Intent detected: calendar.", result.response)


if __name__ == "__main__":
    unittest.main()
