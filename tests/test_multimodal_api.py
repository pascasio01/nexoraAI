import base64
import unittest

from fastapi.testclient import TestClient

from nexoraAI.multimodal.api import app


class TestMultimodalApi(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_analyze_input_endpoint_success(self):
        payload = {
            "input_type": "image",
            "content_base64": base64.b64encode(b"image-data").decode("utf-8"),
            "analysis_goal": "Technical analysis of workplace safety signage",
            "observed_text": "Emergency Exit - Level 2",
            "observed_objects": ["exit sign", "door"],
            "public_context": "Safety audit documentation",
        }
        response = self.client.post("/analyze-input", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("structured_summary", body)
        self.assertIn("key_findings", body)
        self.assertIn("possible_interpretations", body)
        self.assertIn("confidence_score", body)
        self.assertIn("confidence_explanation", body)

    def test_analyze_input_endpoint_rejects_blocked_intent(self):
        payload = {
            "input_type": "image",
            "content_base64": base64.b64encode(b"image-data").decode("utf-8"),
            "analysis_goal": "Track this person across cameras",
        }
        response = self.client.post("/analyze-input", json=payload)
        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
