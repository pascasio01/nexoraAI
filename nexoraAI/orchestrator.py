# Core Orchestrator
from __future__ import annotations

import re
from typing import Any


MISSION_PROTOCOL_PROMPT = """ROLE: SENIOR DEV-SEC-OPS AGENT & CYBER-INTELLIGENCE INVESTIGATOR
IDENTITY: NEXORA CORE (ADMINISTRATOR: EMMANUEL REYNOSO)
RIGOR: Use [CONFIRMED], [PROBABLE], [NO DATA]. If unknown state: "I cannot confirm this data with available information."
SECURITY: Audit OWASP Top 10 exposure, leaked secrets and insecure endpoints. Prioritize post-quantum-ready handling decisions.
RESTRICTION: Execute critical changes or sensitive analysis only when identity "Emmanuel Reynoso" is verified.
OUTPUT: ### [SUMMARY] ### [ANALYSIS] ### [IMPLEMENTATION] ### [SECURITY CHECK]
""".strip()


class Orchestrator:
    def __init__(self, administrator: str = "Emmanuel Reynoso"):
        self.administrator = administrator
        self.active = False

    def start(self):
        self.active = True

    def stop(self):
        self.active = False

    def is_identity_verified(self, session_context: dict[str, Any] | None) -> bool:
        if not session_context:
            return False
        return (
            session_context.get("identity") == self.administrator
            and session_context.get("verified") is True
        )

    def _confidence_tag(self, data_available: bool, confirmed: bool) -> str:
        if not data_available:
            return "[NO DATA]"
        if confirmed:
            return "[CONFIRMED]"
        return "[PROBABLE]"

    def audit_security(self, text: str) -> dict[str, Any]:
        findings: list[str] = []
        if re.search(r"\bsk-[A-Za-z0-9]{20,}\b", text):
            findings.append("Potential API key leak detected.")
        if re.search(r"http://", text):
            findings.append("Insecure endpoint detected (HTTP).")

        if any("leak" in finding.lower() for finding in findings):
            status = "Red"
        elif findings:
            status = "Yellow"
        else:
            status = "Green"

        return {"status": status, "findings": findings}

    def format_output(
        self,
        summary: str,
        analysis: str,
        implementation: str,
        security_status: str,
    ) -> str:
        return (
            f"### [SUMMARY]\n{summary}\n\n"
            f"### [ANALYSIS]\n{analysis}\n\n"
            f"### [IMPLEMENTATION]\n{implementation}\n\n"
            f"### [SECURITY CHECK]\nAudit result: Status {security_status}"
        )

    def process_request(
        self,
        request_text: str,
        session_context: dict[str, Any] | None = None,
        *,
        sensitive: bool = False,
        confirmed: bool = False,
    ) -> str:
        verified = self.is_identity_verified(session_context)
        if sensitive and not verified:
            return self.format_output(
                "Sensitive operation blocked.",
                f'[NO DATA] I cannot confirm this data with available information. Identity "{self.administrator}" is not verified in session context.',
                "No execution performed.",
                "Yellow",
            )

        tag = self._confidence_tag(data_available=bool(request_text.strip()), confirmed=confirmed)
        if tag == "[NO DATA]":
            analysis = '[NO DATA] I cannot confirm this data with available information.'
        else:
            analysis = f"{tag} Request evaluated under Emmanuel Reynoso Sovereignty protocol."

        security = self.audit_security(request_text)
        implementation = "Request accepted under mission protocol."
        if security["findings"]:
            implementation = f"{implementation} Findings: {' '.join(security['findings'])}"

        return self.format_output(
            "Nexora Core protocol applied.",
            analysis,
            implementation,
            security["status"],
        )
