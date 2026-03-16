import copy
import json
import math
import random
from datetime import datetime, timezone


class AssumptionsRegistry:
    def __init__(self):
        self._scenario_defaults = {
            "interest_rate_increase": {
                "description": "Debt servicing pressure caused by higher interest rates.",
                "probability_range": [0.2, 0.45],
                "impact_factors": {"cash_flow": -0.16, "operations": -0.05, "asset_value": -0.09},
                "confidence_floor": 0.7,
            },
            "equipment_failure": {
                "description": "Critical equipment outage and emergency repair impact.",
                "probability_range": [0.15, 0.35],
                "impact_factors": {"cash_flow": -0.11, "operations": -0.28, "asset_value": -0.07},
                "confidence_floor": 0.65,
            },
            "delayed_payment": {
                "description": "Receivable delays and temporary income disruption.",
                "probability_range": [0.25, 0.5],
                "impact_factors": {"cash_flow": -0.2, "operations": -0.07, "asset_value": -0.04},
                "confidence_floor": 0.68,
            },
            "material_cost_inflation": {
                "description": "Vendor/material input cost inflation.",
                "probability_range": [0.3, 0.55],
                "impact_factors": {"cash_flow": -0.12, "operations": -0.08, "asset_value": -0.06},
                "confidence_floor": 0.72,
            },
            "emergency_outage": {
                "description": "Emergency event (power/weather/service) creating downtime and response costs.",
                "probability_range": [0.1, 0.25],
                "impact_factors": {"cash_flow": -0.09, "operations": -0.3, "asset_value": -0.08},
                "confidence_floor": 0.6,
            },
            "legal_fine": {
                "description": "Regulatory or legal fine and remediation obligations.",
                "probability_range": [0.05, 0.18],
                "impact_factors": {"cash_flow": -0.13, "operations": -0.1, "asset_value": -0.09},
                "confidence_floor": 0.58,
            },
        }

    def get(self, scenario_type):
        return copy.deepcopy(self._scenario_defaults.get(scenario_type, {}))


class ScenarioBuilder:
    def __init__(self, assumptions_registry):
        self.assumptions_registry = assumptions_registry

    def build(self, simulation_request):
        scenarios = simulation_request.get("scenarios") or []
        built = []
        for scenario in scenarios:
            scenario_type = scenario.get("type")
            assumptions = self.assumptions_registry.get(scenario_type)
            if not assumptions:
                continue
            merged_assumptions = copy.deepcopy(assumptions)
            merged_assumptions.update(scenario.get("assumptions", {}))
            built.append(
                {
                    "name": scenario.get("name") or scenario_type,
                    "type": scenario_type,
                    "assumptions": merged_assumptions,
                    "mode": scenario.get("mode") or simulation_request.get("mode", "deterministic"),
                    "iterations": int(scenario.get("iterations") or simulation_request.get("iterations", 500)),
                }
            )
        return built


class SimulationEngine:
    @staticmethod
    def _bounded(value):
        return max(-0.95, min(value, 0.95))

    def run(self, scenario, base_inputs):
        mode = scenario["mode"]
        if mode == "monte_carlo":
            return self._monte_carlo_run(scenario, base_inputs)
        if mode == "parameter_stress":
            return self._parameter_stress_run(scenario, base_inputs)
        return self._deterministic_run(scenario, base_inputs)

    def _deterministic_run(self, scenario, base_inputs):
        factors = scenario["assumptions"].get("impact_factors", {})
        return self._result_from_factors(factors, base_inputs, variability=0.0)

    def _parameter_stress_run(self, scenario, base_inputs):
        factors = copy.deepcopy(scenario["assumptions"].get("impact_factors", {}))
        stress_multipliers = scenario["assumptions"].get("stress_multipliers", {})
        for key, multiplier in stress_multipliers.items():
            if key in factors:
                factors[key] = self._bounded(factors[key] * float(multiplier))
        return self._result_from_factors(factors, base_inputs, variability=0.05)

    def _monte_carlo_run(self, scenario, base_inputs):
        iterations = max(100, scenario["iterations"])
        factors = scenario["assumptions"].get("impact_factors", {})
        samples = {"cash_flow": [], "operations": [], "asset_value": []}
        for _ in range(iterations):
            for key in samples:
                base_factor = factors.get(key, 0.0)
                random_noise = random.triangular(-0.08, 0.08, 0.0)
                samples[key].append(self._bounded(base_factor + random_noise))

        return self._result_from_samples(samples, base_inputs)

    def _result_from_factors(self, factors, base_inputs, variability):
        samples = {"cash_flow": [], "operations": [], "asset_value": []}
        for key in samples:
            factor = factors.get(key, 0.0)
            samples[key] = [self._bounded(factor - variability), factor, self._bounded(factor + variability)]
        return self._result_from_samples(samples, base_inputs)

    def _result_from_samples(self, samples, base_inputs):
        baseline_cash = float(base_inputs.get("monthly_cash_inflow", 0.0)) - float(base_inputs.get("monthly_operating_cost", 0.0))
        baseline_ops = float(base_inputs.get("operations_health", 0.85))
        baseline_asset = float(base_inputs.get("asset_value", 0.0))

        def quantiles(values):
            ordered = sorted(values)
            lower = ordered[max(0, math.floor(len(ordered) * 0.1) - 1)]
            upper = ordered[min(len(ordered) - 1, math.ceil(len(ordered) * 0.9) - 1)]
            expected = sum(ordered) / len(ordered)
            return lower, expected, upper

        cf_low, cf_expected, cf_high = quantiles(samples["cash_flow"])
        op_low, op_expected, op_high = quantiles(samples["operations"])
        av_low, av_expected, av_high = quantiles(samples["asset_value"])

        return {
            "best_case": {
                "cash_flow_delta": baseline_cash * cf_high,
                "operations_delta": baseline_ops * op_high,
                "asset_value_delta": baseline_asset * av_high,
            },
            "expected_case": {
                "cash_flow_delta": baseline_cash * cf_expected,
                "operations_delta": baseline_ops * op_expected,
                "asset_value_delta": baseline_asset * av_expected,
            },
            "worst_case": {
                "cash_flow_delta": baseline_cash * cf_low,
                "operations_delta": baseline_ops * op_low,
                "asset_value_delta": baseline_asset * av_low,
            },
        }


class RiskScoringEngine:
    @staticmethod
    def _severity_from_delta(value):
        magnitude = abs(value)
        if magnitude >= 0.3:
            return 90
        if magnitude >= 0.2:
            return 75
        if magnitude >= 0.1:
            return 55
        return 30

    def score(self, simulation_result):
        expected = simulation_result["expected_case"]
        baseline_cash = max(1.0, abs(simulation_result["evidence"]["baseline"]["monthly_net_cash_flow"]))
        baseline_ops = max(0.01, simulation_result["evidence"]["baseline"]["operations_health"])
        baseline_asset = max(1.0, abs(simulation_result["evidence"]["baseline"]["asset_value"]))

        cash_ratio = expected["cash_flow_delta"] / baseline_cash
        ops_ratio = expected["operations_delta"] / baseline_ops
        asset_ratio = expected["asset_value_delta"] / baseline_asset

        score = round(
            0.45 * self._severity_from_delta(cash_ratio)
            + 0.35 * self._severity_from_delta(ops_ratio)
            + 0.2 * self._severity_from_delta(asset_ratio)
        )
        if score >= 80:
            urgency = "critical"
        elif score >= 60:
            urgency = "high"
        elif score >= 40:
            urgency = "medium"
        else:
            urgency = "low"
        return score, urgency


class RecommendationEngine:
    def recommend(self, scenario_type, urgency):
        shared = [
            "Run a weekly stress review with updated invoice, reserve, and maintenance data.",
            "Document each mitigation action owner and due date for auditability.",
        ]
        scenario_actions = {
            "interest_rate_increase": [
                "Model refinance options and fixed-rate conversion windows.",
                "Prioritize debt tranches with variable-rate exposure for hedging."
            ],
            "equipment_failure": [
                "Create a critical spares list and preventive maintenance acceleration plan.",
                "Negotiate emergency service-level guarantees with primary vendors."
            ],
            "delayed_payment": [
                "Apply aging-based collections playbook and tighten payment terms.",
                "Establish temporary working-capital bridge thresholds."
            ],
            "material_cost_inflation": [
                "Lock key contracts with indexed caps where possible.",
                "Qualify a secondary supplier to reduce single-vendor dependency."
            ],
            "emergency_outage": [
                "Define outage runbooks and restore-time targets per system.",
                "Pre-approve emergency repair spend envelopes for rapid response."
            ],
            "legal_fine": [
                "Run compliance controls review and remediate highest-risk gaps first.",
                "Reserve contingency funds for legal and remediation spending."
            ],
        }
        recommendations = scenario_actions.get(scenario_type, []) + shared
        if urgency == "critical":
            recommendations.insert(0, "Escalate to executive risk committee within 24 hours.")
        return recommendations


class ResultFormatter:
    @staticmethod
    def _rounded_case(case_values):
        return {key: round(value, 2) for key, value in case_values.items()}

    def format(self, scenario, raw_result, score, urgency, recommendations, confidence_score):
        probability_range = scenario["assumptions"].get("probability_range", [0.0, 0.0])
        baseline = raw_result["evidence"]["baseline"]
        expected = self._rounded_case(raw_result["expected_case"])
        risk_to_cash_flow = expected["cash_flow_delta"]
        risk_to_operations = expected["operations_delta"]
        risk_to_asset_value = expected["asset_value_delta"]

        return {
            "scenario_name": scenario["name"],
            "assumptions_used": scenario["assumptions"],
            "probability_range": probability_range,
            "best_case": self._rounded_case(raw_result["best_case"]),
            "expected_case": expected,
            "worst_case": self._rounded_case(raw_result["worst_case"]),
            "impact_score": score,
            "urgency_level": urgency,
            "recommended_mitigation_actions": recommendations,
            "confidence_score": round(confidence_score, 2),
            "evidence_inputs_used": raw_result["evidence"],
            "executive_summary": (
                f"{scenario['name']} is projected to change monthly cash flow by {expected['cash_flow_delta']} "
                f"with operational delta {expected['operations_delta']} and asset value delta {expected['asset_value_delta']}."
            ),
            "risk_to_cash_flow": risk_to_cash_flow,
            "risk_to_operations": risk_to_operations,
            "risk_to_asset_value": risk_to_asset_value,
            "suggested_next_action": recommendations[0] if recommendations else "Collect additional data and rerun simulation.",
            "estimate_disclaimer": "All outputs are estimates based on current assumptions and available data, not guaranteed outcomes.",
            "baseline_reference": baseline,
        }


class AuditLogger:
    @staticmethod
    def record(simulation_request, output):
        return {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "input_hash": hash(json.dumps(simulation_request, sort_keys=True, default=str)),
            "scenario_count": len(output.get("scenarios", [])),
            "has_not_enough_data": bool(output.get("not_enough_data")),
        }


class StressSimulator:
    required_input_paths = (
        "asset_metadata.asset_value",
        "financials.monthly_cash_inflow",
        "financials.monthly_operating_cost",
        "financials.cash_reserves",
    )

    def __init__(self):
        self.assumptions_registry = AssumptionsRegistry()
        self.scenario_builder = ScenarioBuilder(self.assumptions_registry)
        self.simulation_engine = SimulationEngine()
        self.risk_scoring_engine = RiskScoringEngine()
        self.recommendation_engine = RecommendationEngine()
        self.result_formatter = ResultFormatter()
        self.audit_logger = AuditLogger()

    def blueprint(self):
        return {
            "architecture": {
                "service_name": "stress_simulator",
                "components": [
                    "scenario_builder",
                    "simulation_engine",
                    "risk_scoring_engine",
                    "recommendation_engine",
                    "assumptions_registry",
                    "result_formatter",
                    "audit_logger",
                ],
                "integration": {
                    "memory_engine": "Stores prior scenario assumptions and outcome deltas for continuous calibration.",
                    "asset_management_modules": "Consumes asset metadata, maintenance history, costs, obligations, and exposure records.",
                    "future_dashboards": "Returns frontend-ready JSON blocks with summaries and confidence metadata.",
                    "future_alert_system": "Publishes urgency-level events when impact score thresholds are exceeded.",
                },
            },
            "module_responsibilities": {
                "scenario_builder": "Build deterministic, Monte Carlo, and parameter stress scenarios from base assumptions.",
                "simulation_engine": "Compute best/expected/worst-case impact paths from baseline metrics.",
                "risk_scoring_engine": "Convert simulated impact deltas into impact score and urgency level.",
                "recommendation_engine": "Produce scenario-specific, auditable mitigation actions.",
                "assumptions_registry": "Version default assumptions and keep transparent parameter provenance.",
                "result_formatter": "Emit explainable JSON with disclaimers, confidence, and evidence.",
                "audit_logger": "Generate immutable trace metadata for each run.",
            },
            "data_model_suggestions": {
                "input": [
                    "asset_metadata",
                    "maintenance_history",
                    "operating_costs",
                    "vendor_costs",
                    "invoices",
                    "cash_reserves",
                    "debt_payment_obligations",
                    "insurance_costs",
                    "regulatory_exposure",
                    "user_defined_assumptions",
                ],
                "scenario": ["name", "type", "mode", "assumptions", "iterations"],
                "output": [
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
                ],
            },
            "api_design": {
                "POST /v1/stress-simulations": "Run one simulation request and return scenario analyses plus audit metadata.",
                "GET /v1/stress-simulations/blueprint": "Return architecture, interfaces, and roadmap metadata.",
            },
            "mvp_implementation_roadmap": [
                "Implement assumptions registry and deterministic baseline for five mandatory scenarios.",
                "Add Monte Carlo and parameter stress modes with confidence and probability ranges.",
                "Expose JSON API response contract for dashboard integration.",
                "Add audit logging and not-enough-data safeguards.",
            ],
            "future_roadmap": [
                "Ingest digital twin and spatial telemetry for outage propagation modeling.",
                "Add insurance negotiation workflows using scenario evidence bundles.",
                "Connect predictive maintenance models to refresh failure probabilities.",
                "Support portfolio-level stress aggregation across multiple assets.",
            ],
        }

    def run(self, simulation_request):
        missing = self._missing_required_inputs(simulation_request)
        if missing:
            response = {
                "not_enough_data": True,
                "missing_inputs": missing,
                "message": "Not enough data to run a reliable stress simulation. Provide missing baseline inputs.",
                "scenarios": [],
            }
            response["audit"] = self.audit_logger.record(simulation_request, response)
            return response

        base_inputs = self._extract_baseline(simulation_request)
        scenarios = self.scenario_builder.build(simulation_request)
        results = []

        for scenario in scenarios:
            raw_result = self.simulation_engine.run(scenario, base_inputs)
            raw_result["evidence"] = {"baseline": base_inputs, "scenario_type": scenario["type"], "mode": scenario["mode"]}
            score, urgency = self.risk_scoring_engine.score(raw_result)
            recommendations = self.recommendation_engine.recommend(scenario["type"], urgency)
            confidence = self._confidence_score(simulation_request, scenario)
            formatted = self.result_formatter.format(scenario, raw_result, score, urgency, recommendations, confidence)
            results.append(formatted)

        response = {
            "not_enough_data": False,
            "scenarios": results,
            "summary": self._portfolio_summary(results),
        }
        response["audit"] = self.audit_logger.record(simulation_request, response)
        return response

    def _confidence_score(self, simulation_request, scenario):
        input_count = self._provided_input_count(simulation_request)
        confidence_floor = scenario["assumptions"].get("confidence_floor", 0.55)
        data_factor = min(1.0, input_count / 10.0)
        user_assumption_penalty = 0.08 if simulation_request.get("user_defined_assumptions") else 0.0
        return max(0.2, min(0.98, confidence_floor * data_factor - user_assumption_penalty))

    @staticmethod
    def _portfolio_summary(results):
        if not results:
            return {"executive_summary": "No valid scenarios were provided."}
        high_urgency = [item for item in results if item["urgency_level"] in {"high", "critical"}]
        top = sorted(results, key=lambda item: item["impact_score"], reverse=True)[0]
        return {
            "executive_summary": (
                f"{len(results)} scenarios evaluated. Top risk is {top['scenario_name']} "
                f"(impact score {top['impact_score']}, urgency {top['urgency_level']})."
            ),
            "high_urgency_scenarios": [item["scenario_name"] for item in high_urgency],
            "suggested_next_action": top["suggested_next_action"],
        }

    def _missing_required_inputs(self, simulation_request):
        missing = []
        for path in self.required_input_paths:
            if self._nested_get(simulation_request, path.split(".")) is None:
                missing.append(path)
        return missing

    @staticmethod
    def _nested_get(data, path_parts):
        current = data
        for part in path_parts:
            if not isinstance(current, dict) or part not in current:
                return None
            current = current.get(part)
        return current

    @staticmethod
    def _provided_input_count(simulation_request):
        tracked = (
            "asset_metadata",
            "maintenance_history",
            "operating_costs",
            "vendor_costs",
            "invoices",
            "financials",
            "debt_payment_obligations",
            "insurance_costs",
            "regulatory_exposure",
            "user_defined_assumptions",
        )
        return sum(1 for key in tracked if simulation_request.get(key))

    @staticmethod
    def _extract_baseline(simulation_request):
        financials = simulation_request.get("financials", {})
        metadata = simulation_request.get("asset_metadata", {})
        return {
            "asset_id": metadata.get("asset_id", "unknown"),
            "asset_value": float(metadata.get("asset_value", 0.0)),
            "monthly_cash_inflow": float(financials.get("monthly_cash_inflow", 0.0)),
            "monthly_operating_cost": float(financials.get("monthly_operating_cost", 0.0)),
            "monthly_net_cash_flow": float(financials.get("monthly_cash_inflow", 0.0)) - float(financials.get("monthly_operating_cost", 0.0)),
            "cash_reserves": float(financials.get("cash_reserves", 0.0)),
            "operations_health": float(simulation_request.get("operations_health", 0.85)),
        }
