import unittest

from nexoraAI.orchestrator import Orchestrator


class OrchestratorProtocolTests(unittest.TestCase):
    def setUp(self):
        self.orchestrator = Orchestrator()

    def test_blocks_sensitive_request_without_verified_identity(self):
        response = self.orchestrator.process_request("run sensitive audit", sensitive=True)
        self.assertIn("Sensitive operation blocked.", response)
        self.assertIn("[NO DATA]", response)
        self.assertIn("Status Yellow", response)

    def test_allows_sensitive_request_with_verified_identity(self):
        response = self.orchestrator.process_request(
            "review endpoint https://example.com",
            session_context={"identity": "Emmanuel Reynoso", "verified": True},
            sensitive=True,
            confirmed=True,
        )
        self.assertIn("### [SUMMARY]", response)
        self.assertIn("### [ANALYSIS]", response)
        self.assertIn("### [IMPLEMENTATION]", response)
        self.assertIn("### [SECURITY CHECK]", response)
        self.assertIn("[CONFIRMED]", response)
        self.assertIn("Status Green", response)

    def test_reports_no_data_phrase_when_request_is_empty(self):
        response = self.orchestrator.process_request("   ")
        self.assertIn("I cannot confirm this data with available information.", response)
        self.assertIn("Status Green", response)

    def test_security_audit_flags_secret_and_insecure_endpoint(self):
        response = self.orchestrator.process_request(
            "exposed token sk-12345678901234567890 and callback http://example.com"
        )
        self.assertIn("Potential API key leak detected.", response)
        self.assertIn("Insecure endpoint detected (HTTP).", response)
        self.assertIn("Status Red", response)


if __name__ == "__main__":
    unittest.main()
