import unittest

from nexoraAI.orchestrator import Orchestrator
from nexoraAI.stress_simulator import StressSimulator


class StressSimulatorTests(unittest.TestCase):
    def setUp(self):
        self.simulator = StressSimulator()
        self.base_request = {
            "asset_metadata": {"asset_id": "asset-001", "asset_value": 1250000},
            "maintenance_history": {"last_failures": 2},
            "operating_costs": {"monthly": 22000},
            "vendor_costs": {"primary_vendor_indexed": True},
            "invoices": {"avg_days_outstanding": 35},
            "financials": {
                "monthly_cash_inflow": 90000,
                "monthly_operating_cost": 65000,
                "cash_reserves": 140000,
            },
            "debt_payment_obligations": {"monthly_debt_service": 12000},
            "insurance_costs": {"monthly_premium": 1800},
            "regulatory_exposure": {"sector": "utilities"},
            "scenarios": [
                {"type": "interest_rate_increase", "name": "Rate +150bps", "mode": "monte_carlo", "iterations": 120},
                {"type": "equipment_failure", "name": "Main compressor failure", "mode": "deterministic"},
                {"type": "delayed_payment", "name": "Top tenant delays", "mode": "parameter_stress", "assumptions": {"stress_multipliers": {"cash_flow": 1.25}}},
                {"type": "material_cost_inflation", "name": "Steel and parts inflation", "mode": "deterministic"},
                {"type": "emergency_outage", "name": "Regional power outage", "mode": "deterministic"},
            ],
        }

    def test_blueprint_contains_required_sections(self):
        blueprint = self.simulator.blueprint()
        for key in (
            "architecture",
            "module_responsibilities",
            "data_model_suggestions",
            "api_design",
            "mvp_implementation_roadmap",
            "future_roadmap",
        ):
            self.assertIn(key, blueprint)
        self.assertIn("scenario_builder", blueprint["architecture"]["components"])
        self.assertIn("audit_logger", blueprint["architecture"]["components"])

    def test_mvp_simulation_returns_structured_outputs(self):
        response = self.simulator.run(self.base_request)
        self.assertFalse(response["not_enough_data"])
        self.assertEqual(len(response["scenarios"]), 5)

        first = response["scenarios"][0]
        required_fields = (
            "scenario_name",
            "assumptions_used",
            "probability_range",
            "best_case",
            "expected_case",
            "worst_case",
            "impact_score",
            "urgency_level",
            "recommended_mitigation_actions",
            "confidence_score",
            "evidence_inputs_used",
            "executive_summary",
            "risk_to_cash_flow",
            "risk_to_operations",
            "risk_to_asset_value",
            "suggested_next_action",
        )
        for field in required_fields:
            self.assertIn(field, first)

    def test_not_enough_data_is_explicit_and_auditable(self):
        response = self.simulator.run({"scenarios": [{"type": "interest_rate_increase"}]})
        self.assertTrue(response["not_enough_data"])
        self.assertGreaterEqual(len(response["missing_inputs"]), 1)
        self.assertIn("audit", response)

    def test_orchestrator_exposes_simulator_entrypoints(self):
        orchestrator = Orchestrator()
        self.assertIn("architecture", orchestrator.stress_simulator_blueprint())
        result = orchestrator.run_stress_simulator(self.base_request)
        self.assertIn("summary", result)


if __name__ == "__main__":
    unittest.main()
