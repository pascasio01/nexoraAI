import asyncio
import unittest
from unittest.mock import patch

import core.orchestrator as orchestrator


class CoreOrchestratorFallbackTests(unittest.TestCase):
    def test_run_agents_returns_fallback_when_dependencies_missing(self):
        with patch.object(orchestrator, "_AGENT_FUNCS", None), patch.object(
            orchestrator, "_AGENT_IMPORT_ERROR", ModuleNotFoundError("agents")
        ):
            result = asyncio.run(orchestrator.run_agents("u1", "hola"))
        self.assertIn("no disponible", result.lower())

    def test_run_agents_fallback_is_stable_across_calls(self):
        with patch.object(orchestrator, "_AGENT_FUNCS", None), patch.object(
            orchestrator, "_AGENT_IMPORT_ERROR", ModuleNotFoundError("agents")
        ):
            first = asyncio.run(orchestrator.run_agents("u1", "hola"))
            second = asyncio.run(orchestrator.run_agents("u1", "hola"))
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
