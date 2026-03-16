import unittest
from fastapi.testclient import TestClient

from app import app


class FutureArchitectureTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_assistant_settings_exposes_future_prompt_and_architecture(self):
        response = self.client.get('/assistant-settings')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('future_prompt', data)
        self.assertIn('future_architecture', data)

        architecture = data['future_architecture']
        self.assertIn('assistant_limitations', architecture)
        self.assertIn('required_modules', architecture)
        self.assertIn('evolution_roadmap', architecture)
        self.assertIn('risks_and_mitigations', architecture)

    def test_personal_memory_and_decision_engine_basics(self):
        write = self.client.post(
            '/personal-memory',
            json={
                'user_id': 'u1',
                'habits': ['daily planning'],
                'preferences': ['concise summaries'],
                'relationships': ['team'],
                'important_events': ['product launch'],
                'long_term_goals': ['improve focus'],
                'personal_context': ['remote work'],
            },
        )
        self.assertEqual(write.status_code, 200)

        read = self.client.get('/personal-memory/u1')
        self.assertEqual(read.status_code, 200)
        self.assertEqual(read.json()['memory']['habits'], ['daily planning'])

        decision = self.client.post('/tools/execute', json={'autonomy_level': 2, 'action': 'draft_email'})
        self.assertEqual(decision.status_code, 200)
        self.assertEqual(decision.json()['decision']['status'], 'awaiting_permission')

    def test_decision_engine_levels_and_validation(self):
        expected = {
            0: 'prepared',
            1: 'prepared',
            2: 'awaiting_permission',
            3: 'auto_executed',
        }
        for level, status in expected.items():
            response = self.client.post('/tools/execute', json={'autonomy_level': level, 'action': 'x'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['decision']['status'], status)

        invalid = self.client.post('/tools/execute', json={'autonomy_level': 9, 'action': 'x'})
        self.assertEqual(invalid.status_code, 422)


if __name__ == '__main__':
    unittest.main()
