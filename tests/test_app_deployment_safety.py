import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

import app as app_module


class AppDeploymentSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app_module.app)

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

    def test_telegram_webhook_valid_token_without_telegram_app_returns_503(self):
        with patch.multiple(app_module, BOT_TOKEN="valid-token", tg_app=None):
            response = self.client.post('/tg/valid-token', json={})
            self.assertEqual(response.status_code, 503)

    def test_telegram_webhook_valid_token_processes_update(self):
        fake_tg_app = SimpleNamespace(bot=AsyncMock(), process_update=AsyncMock())
        with patch.multiple(app_module, BOT_TOKEN="valid-token", tg_app=fake_tg_app):
            with patch("app.Update.de_json", return_value=object()):
                response = self.client.post('/tg/valid-token', json={"update_id": 1})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"ok": True})

    def test_whatsapp_webhook_returns_twiml_xml(self):
        response = self.client.post('/whatsapp', data={"Body": "hola", "From": "wa:+10000000000"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/xml", response.headers.get("content-type", ""))
        self.assertIn("<Response><Message>", response.text)


if __name__ == '__main__':
    unittest.main()
