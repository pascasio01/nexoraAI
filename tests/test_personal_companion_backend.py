import hashlib
import hmac
import time
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

import app as app_module


class PersonalCompanionBackendTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app_module.app)

    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn('status', payload)
        self.assertIn('redis', payload)

    def test_profile_and_settings_roundtrip_without_redis(self):
        user = 'test_user_profile'

        set_profile = self.client.post(f'/profile?usuario={user}', json={'profile': 'Le gusta música lo-fi'})
        self.assertEqual(set_profile.status_code, 200)

        get_profile = self.client.get(f'/profile?usuario={user}')
        self.assertEqual(get_profile.status_code, 200)
        self.assertEqual(get_profile.json()['profile'], 'Le gusta música lo-fi')

        set_settings = self.client.post(
            f'/assistant-settings?usuario={user}',
            json={
                'tone': 'warm',
                'response_length': 'short',
                'voice_enabled': True,
                'avatar_enabled': True,
            },
        )
        self.assertEqual(set_settings.status_code, 200)

        get_settings = self.client.get(f'/assistant-settings?usuario={user}')
        self.assertEqual(get_settings.status_code, 200)
        self.assertTrue(get_settings.json()['settings']['voice_enabled'])
        self.assertTrue(get_settings.json()['settings']['avatar_enabled'])

    @patch('ai_core.AUTH_SIGNING_KEY', 'test-secret')
    def test_chat_uses_bearer_identity_when_valid(self):
        user_id = 'secure-user'
        ts = str(int(time.time()))
        sig = hmac.new(b'test-secret', f'{user_id}.{ts}'.encode(), hashlib.sha256).hexdigest()
        token = f'{user_id}.{ts}.{sig}'

        res = self.client.post(
            '/chat',
            headers={'Authorization': f'Bearer {token}'},
            json={'texto': 'hola', 'usuario': 'spoofed', 'channel': 'web'},
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['user_id'], user_id)

    @patch('ai_core.AUTH_SIGNING_KEY', 'test-secret')
    @patch('ai_core.AUTH_TOKEN_MAX_AGE_SECONDS', 1)
    def test_chat_rejects_expired_bearer_identity(self):
        user_id = 'secure-user'
        ts = str(int(time.time()) - 300)
        sig = hmac.new(b'test-secret', f'{user_id}.{ts}'.encode(), hashlib.sha256).hexdigest()
        token = f'{user_id}.{ts}.{sig}'

        res = self.client.post(
            '/chat',
            headers={'Authorization': f'Bearer {token}'},
            json={'texto': 'hola', 'usuario': 'fallback-user', 'channel': 'web'},
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['user_id'], 'fallback-user')


if __name__ == '__main__':
    unittest.main()
