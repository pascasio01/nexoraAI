from nexoraAI.orchestrator import Orchestrator


def run_agents(orchestrator: Orchestrator, user_id: str, user_text: str) -> str:
    """
    Backward-compatible entry point to run a user's configured personal agent.
    """
    return orchestrator.run_personal_agent(user_id=user_id, user_text=user_text)
