from __future__ import annotations


class PreActionSafetyLayer:
    MIN_CONFIDENCE = 0.05
    MAX_CONFIDENCE = 0.99
    MIN_INPUT_LENGTH = 12
    SHORT_INPUT_PENALTY = 0.15
    MISSING_CONTEXT_PENALTY = 0.1
    MISSING_ACTION_NAME_PENALTY = 0.1
    RISK_PENALTY_PER_ITEM = 0.1
    MAX_RISK_PENALTY = 0.45

    SENSITIVE_ACTIONS = {
        "delete_data",
        "send_report",
        "share_credentials",
        "wire_transfer",
        "publish_private_content",
        "location_alarm",
    }

    def analyze_action(self, user_input, available_context=None, action_metadata=None):
        context = available_context or {}
        metadata = action_metadata or {}

        detected_objective = self._detect_objective(user_input, metadata)
        urgency = self._estimate_urgency(user_input, metadata)
        risks = self._evaluate_risks(detected_objective, context, metadata)
        risk_severity = self._risk_severity(metadata, risks)
        confidence = self._estimate_confidence(user_input, context, metadata, risks)
        recommended_action = self._recommend_action(detected_objective, risks)
        alternatives = self._alternatives_for(detected_objective)
        scenarios = self._build_scenarios(detected_objective, risks, recommended_action)
        consequences = [scenario["consequence"] for scenario in scenarios.values()]
        secure_practices = self._secure_practices(context, metadata, risks)
        requires_confirmation = self._requires_confirmation(metadata, risk_severity)

        best_next_step = (
            "Request explicit user confirmation and then execute cautiously."
            if requires_confirmation
            else "Proceed with the recommended action while applying listed safeguards."
        )

        return {
            "detected_objective": detected_objective,
            "recommended_action": recommended_action,
            "alternative_options": alternatives,
            "confidence_score": confidence,
            "potential_risks": risks,
            "likely_consequences": consequences,
            "urgency": urgency,
            "best_next_step": best_next_step,
            "scenario_model": scenarios,
            "secure_practices": secure_practices,
            "risk_severity": risk_severity,
            "requires_confirmation": requires_confirmation,
            "sensitive_action": metadata.get("action_name") in self.SENSITIVE_ACTIONS,
        }

    def get_architecture_blueprint(self):
        return {
            "architecture_for_pre_action_analysis": [
                "Goal Interpreter",
                "Context Analyzer",
                "Risk Engine",
                "Decision Review Layer",
                "Scenario Evaluator",
                "Safety Recommendation Layer",
                "Confirmation Gate",
            ],
            "module_responsibilities": {
                "risk_engine": "Scores operational, privacy, and security risks before execution.",
                "decision_review_layer": "Generates recommendation, alternatives, and confidence.",
                "pre_action_safety_layer": "Combines risk, scenarios, safeguards, and confirmation needs.",
            },
            "risk_model": "Rule-based scoring with additive penalties for sensitive intent, unsafe network, untrusted device, and low context quality.",
            "confidence_scoring_approach": "Starts at 0.9, subtracts ambiguity and risk penalties, clips to [0.05, 0.99].",
            "scenario_evaluation_model": {
                "optimistic_scenario": "User follows safeguards and receives desired outcome.",
                "probable_scenario": "Action succeeds with minor friction or moderate risk.",
                "risky_scenario": "Action triggers data, trust, or operational harm.",
            },
            "safe_recommendation_flow": [
                "Detect objective",
                "Analyze context",
                "Evaluate risks",
                "Estimate outcomes",
                "Recommend best action",
                "Present alternatives and confidence",
                "Require confirmation for sensitive actions",
            ],
            "mvp_implementation_plan": [
                "Implement pre_action_safety_layer with structured output.",
                "Integrate review_before_action into orchestrator action paths.",
                "Block sensitive execution until explicit confirmation.",
                "Capture analytics for confidence/risk tuning.",
                "Expand policy rules with telemetry-driven improvements.",
            ],
        }

    def _detect_objective(self, user_input, metadata):
        text = (user_input or "").lower()
        action_name = (metadata.get("action_name") or "").lower()

        if "delete" in text or action_name == "delete_data":
            return "Delete existing data"
        if "report" in text or action_name == "send_report":
            return "Generate and send report"
        if "reminder" in text or action_name == "set_reminder":
            return "Set a reminder"
        if "calendar" in text or action_name == "set_calendar_event":
            return "Create calendar event"
        if "note" in text or action_name == "save_note":
            return "Save a note"
        return "General assistant operation"

    def _estimate_urgency(self, user_input, metadata):
        text = (user_input or "").lower()
        explicit_urgency = (metadata.get("urgency") or "").lower()
        if explicit_urgency in {"high", "critical"} or "urgent" in text or "asap" in text:
            return "high"
        if explicit_urgency == "medium":
            return "medium"
        return "low"

    def _evaluate_risks(self, detected_objective, context, metadata):
        risks = []
        action_name = metadata.get("action_name")
        if action_name in self.SENSITIVE_ACTIONS:
            risks.append("Sensitive operation could impact user privacy, trust, or data integrity.")
        if context.get("network_trust") == "unsafe":
            risks.append("Untrusted network increases interception and session hijack risk.")
        if context.get("device_trusted") is False:
            risks.append("Untrusted device may expose data to unauthorized access.")
        if not context.get("session_protected", True):
            risks.append("Session protections appear weak, increasing account takeover risk.")
        if detected_objective == "Delete existing data":
            risks.append("Deletion may be irreversible without backup or recovery checkpoint.")
        return risks

    def _estimate_confidence(self, user_input, context, metadata, risks):
        score = 0.9
        if len((user_input or "").strip()) < self.MIN_INPUT_LENGTH:
            score -= self.SHORT_INPUT_PENALTY
        if not context:
            score -= self.MISSING_CONTEXT_PENALTY
        if not metadata.get("action_name"):
            score -= self.MISSING_ACTION_NAME_PENALTY
        score -= min(self.MAX_RISK_PENALTY, len(risks) * self.RISK_PENALTY_PER_ITEM)
        return round(max(self.MIN_CONFIDENCE, min(self.MAX_CONFIDENCE, score)), 2)

    def _recommend_action(self, detected_objective, risks):
        if risks:
            return f"{detected_objective} with a safety checkpoint and explicit confirmation."
        return f"{detected_objective} with standard execution safeguards."

    def _alternatives_for(self, detected_objective):
        return [
            f"Ask clarifying questions before executing: {detected_objective}.",
            "Run a dry-run or preview mode before committing changes.",
            "Delay execution and request stronger context signals.",
        ]

    def _build_scenarios(self, detected_objective, risks, recommended_action):
        risky_consequence = (
            "Security, privacy, or data-loss issues become likely without safeguards."
            if risks
            else "Low but non-zero operational risk remains."
        )
        return {
            "optimistic_scenario": {
                "summary": "User intent is clear and safeguards are followed.",
                "consequence": f"{detected_objective} succeeds with strong safety posture.",
            },
            "probable_scenario": {
                "summary": "Execution proceeds with normal uncertainty.",
                "consequence": f"{recommended_action} completes with manageable risk.",
            },
            "risky_scenario": {
                "summary": "Safeguards are skipped or context is weak.",
                "consequence": risky_consequence,
            },
        }

    def _secure_practices(self, context, metadata, risks):
        practices = []
        if context.get("network_trust") == "unsafe":
            practices.append("Use a secure network whenever possible for sensitive operations.")
            practices.append(
                "Use a reputable VPN on unsafe networks for privacy and security protection, not for bypassing rules."
            )
        if not context.get("session_protected", True):
            practices.append("Enable session protection controls (MFA, secure tokens, short session TTL).")
        if context.get("device_trusted") is False:
            practices.append("Run sensitive actions only on trusted devices with verified security posture.")
        if metadata.get("action_name") in self.SENSITIVE_ACTIONS or risks:
            practices.append(
                "Separate development and creator production environments to reduce blast radius."
            )
        return practices

    def _risk_severity(self, metadata, risks):
        if metadata.get("action_name") in self.SENSITIVE_ACTIONS:
            return "high"
        if len(risks) >= 3:
            return "high"
        if len(risks) >= 1:
            return "medium"
        return "low"

    def _requires_confirmation(self, metadata, risk_severity):
        return metadata.get("action_name") in self.SENSITIVE_ACTIONS or risk_severity == "high"
