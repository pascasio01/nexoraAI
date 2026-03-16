import random

try:
    import numpy as np
except ModuleNotFoundError:  # pragma: no cover - fallback only used when numpy is unavailable
    class _RandomFallback:
        @staticmethod
        def normal(loc, scale, size):
            return [random.gauss(loc, scale) for _ in range(size)]

        @staticmethod
        def triangular(left, mode, right, size):
            return [random.triangular(left, right, mode) for _ in range(size)]

    class _NPFallback:
        random = _RandomFallback()

        @staticmethod
        def sum(values):
            return sum(values)

    np = _NPFallback()


class NexoraStressTest:
    def __init__(self, patrimony_data, building_assets, iterations=10000):
        self.patrimony = patrimony_data
        self.assets = building_assets
        self.iterations = iterations

    def run_economic_crash(self):
        """Simulate a market crash and rent payment delays."""
        revenue_shocks = np.random.normal(loc=-0.10, scale=0.05, size=self.iterations)
        projected_liquidity = [
            self.patrimony["liquidity"] * (1 + shock) for shock in revenue_shocks
        ]
        failures = np.sum(
            liquidity < self.patrimony["min_reserve"] for liquidity in projected_liquidity
        )
        return (failures / self.iterations) * 100

    def run_operational_disaster(self):
        """Simulate technical failures in buildings under extreme weather."""
        repair_costs = np.random.triangular(
            left=1000, mode=5000, right=20000, size=self.iterations
        )
        exhaustion_rate = np.sum(
            cost > self.patrimony["maintenance_fund"] for cost in repair_costs
        )
        return (exhaustion_rate / self.iterations) * 100
