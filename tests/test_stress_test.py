import unittest
from unittest.mock import patch

from nexoraAI.stress_test import NexoraStressTest


class TestNexoraStressTest(unittest.TestCase):
    def setUp(self):
        self.patrimony = {
            "liquidity": 10000,
            "min_reserve": 9500,
            "maintenance_fund": 6000,
        }
        self.assets = {"boilers": "ok", "roofs": "ok"}
        self.simulator = NexoraStressTest(self.patrimony, self.assets, iterations=4)

    @patch("nexoraAI.stress_test.np.random.normal")
    def test_run_economic_crash_returns_failure_rate_percentage(self, mock_normal):
        mock_normal.return_value = [-0.20, -0.10, 0.05, -0.02]
        result = self.simulator.run_economic_crash()
        self.assertEqual(result, 50.0)

    @patch("nexoraAI.stress_test.np.random.triangular")
    def test_run_operational_disaster_returns_exhaustion_rate_percentage(self, mock_triangular):
        mock_triangular.return_value = [1000, 7000, 6001, 5000]
        result = self.simulator.run_operational_disaster()
        self.assertEqual(result, 50.0)


if __name__ == "__main__":
    unittest.main()
