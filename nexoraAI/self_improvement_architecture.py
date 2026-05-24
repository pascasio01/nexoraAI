"""Supervised self-improvement architecture blueprint for Nexora / Sora."""

from __future__ import annotations


def get_self_improvement_architecture() -> dict:
    """Return the platform architecture for safe self-improvement and repair."""
    return {
        "architecture": "Nexora/Sora Supervised Self-Improvement Loop",
        "safety_rules": [
            "Never silently change production code.",
            "Always log every action and decision.",
            "Run tests and checks before suggesting merges.",
            "Use branch-based changes for every code modification.",
            "Support rollback for every applied change.",
            "Require human approval for risky changes.",
        ],
        "autonomy_levels": [
            {
                "level": "analyze_only",
                "description": "Read-only diagnosis and recommendations.",
                "requires_human_approval": False,
            },
            {
                "level": "propose_changes",
                "description": "Prepare patch proposals without applying them.",
                "requires_human_approval": True,
            },
            {
                "level": "create_branch_pr",
                "description": "Create branch and PR with tests and change log.",
                "requires_human_approval": True,
            },
            {
                "level": "apply_safe_fixes_controlled_env",
                "description": "Apply low-risk fixes only in controlled environments.",
                "requires_human_approval": True,
            },
        ],
        "modules": {
            "dev_agent": {
                "responsibilities": [
                    "Analyze codebase structure and quality hotspots.",
                    "Propose safe refactors and technical debt reductions.",
                    "Write patch drafts for approved changes.",
                    "Improve and synchronize documentation with code.",
                    "Prepare pull requests with summary, risk notes, and test evidence.",
                ],
                "inputs": ["repository graph", "coding standards", "task scope"],
                "outputs": ["patch proposal", "doc updates", "pull request draft"],
            },
            "repair_agent": {
                "responsibilities": [
                    "Read runtime logs and error traces.",
                    "Detect runtime failures and broken imports.",
                    "Detect invalid or missing environment variables.",
                    "Propose fixes and generate incident-specific remediation patches.",
                ],
                "inputs": ["application logs", "runtime metrics", "environment snapshots"],
                "outputs": ["repair diagnosis", "safe fix proposal", "rollback plan"],
            },
            "update_agent": {
                "responsibilities": [
                    "Review dependency inventory and detect stale packages.",
                    "Suggest version upgrades with changelog highlights.",
                    "Assess compatibility and migration risks.",
                    "Prepare phased upgrade plans with fallback options.",
                ],
                "inputs": ["dependency lockfiles", "security advisories", "release notes"],
                "outputs": ["upgrade report", "compatibility risk matrix", "upgrade PR draft"],
            },
            "task_orchestrator": {
                "responsibilities": [
                    "Queue and prioritize internal maintenance tasks.",
                    "Run tasks sequentially or in parallel with safety guards.",
                    "Enforce rate limits, execution budgets, and timeouts.",
                    "Report status, outcomes, and blocked actions clearly.",
                ],
                "inputs": ["task backlog", "policies", "agent capabilities"],
                "outputs": ["execution plan", "audit log", "task status report"],
            },
            "self_improvement_engine": {
                "responsibilities": [
                    "Coordinate Dev, Repair, and Update agents.",
                    "Select autonomy level for each action.",
                    "Apply policy gates for approvals and risk checks.",
                    "Publish final recommendations or PR-ready change sets.",
                ],
                "inputs": ["agent reports", "safety policy", "autonomy level"],
                "outputs": ["consolidated improvement plan", "approved execution package"],
            },
        },
        "suggested_file_structure": [
            "nexoraAI/self_improvement/",
            "nexoraAI/self_improvement/policy.py",
            "nexoraAI/self_improvement/orchestrator.py",
            "nexoraAI/self_improvement/agents/dev_agent.py",
            "nexoraAI/self_improvement/agents/repair_agent.py",
            "nexoraAI/self_improvement/agents/update_agent.py",
            "nexoraAI/self_improvement/executors/branch_executor.py",
            "nexoraAI/self_improvement/executors/validation_runner.py",
            "nexoraAI/self_improvement/executors/rollback_manager.py",
            "nexoraAI/self_improvement/reporting/audit_log.py",
            "nexoraAI/self_improvement/reporting/result_reporter.py",
            "tests/test_self_improvement_architecture.py",
        ],
        "implementation_roadmap": [
            {
                "phase": "phase_1_foundation",
                "focus": "Define policy engine, autonomy levels, and event audit schema.",
            },
            {
                "phase": "phase_2_agent_scaffolding",
                "focus": "Implement Dev/Repair/Update agent interfaces and dry-run mode.",
            },
            {
                "phase": "phase_3_orchestration",
                "focus": "Add task prioritization, concurrency controls, and retries.",
            },
            {
                "phase": "phase_4_pr_and_validation",
                "focus": "Automate branch/PR preparation and mandatory validation gates.",
            },
            {
                "phase": "phase_5_controlled_autofix",
                "focus": "Enable controlled-environment safe fixes with rollback verification.",
            },
        ],
    }
