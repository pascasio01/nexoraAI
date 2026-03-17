import base64
import unittest

from nexoraAI.multimodal.analysis import GuardrailViolation, analyze_multimodal_input
from nexoraAI.multimodal.schemas import AnalyzeInputRequest


class TestMultimodalAnalysis(unittest.TestCase):
    def test_rejects_identity_tracking_request(self):
        payload = AnalyzeInputRequest(
            input_type="image",
            content_base64=base64.b64encode(b"image-bytes").decode("utf-8"),
            analysis_goal="Use facial recognition to identify this person",
            observed_objects=["badge", "laptop"],
        )

        with self.assertRaises(GuardrailViolation):
            analyze_multimodal_input(payload)

    def test_document_analysis_returns_required_sections(self):
        payload = AnalyzeInputRequest(
            input_type="document",
            content_base64=base64.b64encode(
                b"Incident Report 2026-03-17\nSystem NodeA restarted during maintenance."
            ).decode("utf-8"),
            analysis_goal="Extract technical event details for compliance review",
            public_context="Public maintenance report",
        )
        response = analyze_multimodal_input(payload)

        self.assertIn("summary", response.structured_summary)
        self.assertGreater(len(response.key_findings), 0)
        self.assertGreater(len(response.possible_interpretations), 0)
        self.assertIn(response.confidence_score, {"low", "medium", "high"})
        self.assertIn("entities", response.knowledge_graph)
        self.assertEqual(response.privacy["image_document_storage"], "not_persisted")


if __name__ == "__main__":
    unittest.main()
