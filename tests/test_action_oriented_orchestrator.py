import unittest

from nexoraAI.orchestrator import (
    Orchestrator,
    RELIABILITY_FALLBACK_MESSAGE,
)


def _ok_tool(name):
    def _handler(payload):
        return {"tool": name, "payload": payload, "status": "ok"}

    return _handler


class TestActionOrientedOrchestrator(unittest.TestCase):
    def setUp(self):
        self.orchestrator = Orchestrator()

    def test_personal_knowledge_graph_supports_temporal_relationships(self):
        graph = self.orchestrator.knowledge_graph
        graph.upsert_entity("Building_A", "assets", {"name": "Building A"})
        graph.upsert_entity("Company_X", "people", {"name": "Company X"})

        rel = graph.add_relationship("Building_A", "maintenance_contract", "Company_X")
        rels = graph.related_to("Building_A", "maintenance_contract")

        self.assertEqual(1, len(rels))
        self.assertEqual("Company_X", rel.target_id)
        self.assertTrue(rel.observed_at)

    def test_tool_execution_uses_reasoning_and_verification(self):
        self.orchestrator.tools.register_tool("generate_reports", _ok_tool("generate_reports"))
        result = self.orchestrator.process_goal(
            goal="create_monthly_report",
            plan=[{"tool": "generate_reports", "payload": {"month": "2026-03"}}],
        )

        self.assertTrue(result["approved"])
        self.assertEqual(0.9, result["confidence"])
        self.assertEqual("generate_reports", result["message"][0]["tool"])
        self.assertEqual(1, len(self.orchestrator.transparent_reasoning_logs))

    def test_low_confidence_results_use_reliability_fallback(self):
        response = self.orchestrator.verification.verify(
            {"validated": True, "confidence": 0.3, "result": "unsafe answer"}
        )
        self.assertFalse(response["approved"])
        self.assertEqual(RELIABILITY_FALLBACK_MESSAGE, response["message"])

    def test_critical_actions_require_confirmation(self):
        result = self.orchestrator.process_goal(goal="send_payment", plan=[], critical=True)
        self.assertTrue(result["approved"])
        self.assertEqual("Confirmation required before critical action.", result["message"])

    def test_building_issue_workflow_executes_end_to_end(self):
        self.orchestrator.tools.register_tool("analyze_photo", _ok_tool("analyze_photo"))
        self.orchestrator.tools.register_tool(
            "retrieve_maintenance_manual", _ok_tool("retrieve_maintenance_manual")
        )
        self.orchestrator.tools.register_tool("draft_inspection_report", _ok_tool("draft_inspection_report"))
        self.orchestrator.tools.register_tool(
            "send_message_to_technician", _ok_tool("send_message_to_technician")
        )
        self.orchestrator.tools.register_tool("log_maintenance_issue", _ok_tool("log_maintenance_issue"))

        result = self.orchestrator.automate_building_issue(
            {
                "photo": "photo-binary",
                "asset_id": "Building_A",
                "description": "water leak in hall",
                "technician_id": "tech-1",
                "issue_id": "issue-42",
            }
        )
        self.assertTrue(result["approved"])
        executed_tools = [entry["tool"] for entry in result["message"]]
        self.assertEqual(
            [
                "analyze_photo",
                "retrieve_maintenance_manual",
                "draft_inspection_report",
                "send_message_to_technician",
                "log_maintenance_issue",
            ],
            executed_tools,
        )


if __name__ == "__main__":
    unittest.main()
