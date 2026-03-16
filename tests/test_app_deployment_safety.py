import unittest

from fastapi.testclient import TestClient

from app import app


class DeploymentSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_endpoint_reports_service_availability(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertIn('status', payload)
        self.assertIn('services', payload)
        self.assertIn('config', payload)
        self.assertIn('telegram', payload['services'])
        self.assertIn('has_base_url', payload['config'])

    def test_telegram_webhook_requires_valid_token(self):
        response = self.client.post('/tg/invalid-token', json={})
        self.assertEqual(response.status_code, 403)


if __name__ == '__main__':
    unittest.main()
