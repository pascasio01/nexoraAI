from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Dict


class AutonomyLevel(IntEnum):
    LEVEL_0_SUGGEST_ONLY = 0
    LEVEL_1_PREPARE_AND_ASK = 1
    LEVEL_2_EXECUTE_WITH_PRIOR_PERMISSION = 2
    LEVEL_3_EXECUTE_AUTOMATICALLY = 3


@dataclass
class DecisionContext:
    permissions: Dict[str, bool]
    autonomy_level: AutonomyLevel
    risk: int
    priority: int
    has_prior_permission: bool = False


@dataclass
class DecisionOutcome:
    should_execute: bool
    mode: str
    reason: str
    priority: int


class DecisionEngine:
    def __init__(self, max_auto_risk: int = 3):
        self.max_auto_risk = max_auto_risk

    def evaluate(self, requested_action: str, context: DecisionContext) -> DecisionOutcome:
        allowed = context.permissions.get(requested_action, True)
        if not allowed:
            return DecisionOutcome(
                should_execute=False,
                mode="blocked",
                reason=f"Permission denied for action '{requested_action}'.",
                priority=context.priority,
            )

        if context.autonomy_level == AutonomyLevel.LEVEL_0_SUGGEST_ONLY:
            return DecisionOutcome(
                should_execute=False,
                mode="suggest_only",
                reason="Autonomy level 0: suggestions only.",
                priority=context.priority,
            )

        if context.autonomy_level == AutonomyLevel.LEVEL_1_PREPARE_AND_ASK:
            return DecisionOutcome(
                should_execute=False,
                mode="prepare_and_ask",
                reason="Autonomy level 1: prepared action, waiting for explicit confirmation.",
                priority=context.priority,
            )

        if context.autonomy_level == AutonomyLevel.LEVEL_2_EXECUTE_WITH_PRIOR_PERMISSION:
            if context.has_prior_permission:
                return DecisionOutcome(
                    should_execute=True,
                    mode="execute_with_permission",
                    reason="Autonomy level 2: execution approved by prior permission.",
                    priority=context.priority,
                )
            return DecisionOutcome(
                should_execute=False,
                mode="execute_with_permission",
                reason="Autonomy level 2: prior permission is required before execution.",
                priority=context.priority,
            )

        if context.risk > self.max_auto_risk:
            return DecisionOutcome(
                should_execute=False,
                mode="auto_execute_restricted",
                reason=(
                    f"Autonomy level 3 blocked by strict rules: risk {context.risk} "
                    f"exceeds max {self.max_auto_risk}."
                ),
                priority=context.priority,
            )

        return DecisionOutcome(
            should_execute=True,
            mode="auto_execute",
            reason="Autonomy level 3: action executed automatically within strict rules.",
            priority=context.priority,
        )
