from services.orchestrator.engine import Orchestrator


def run_agents(user_id: str, user_text: str) -> str:
    del user_id
    orchestrator = Orchestrator()
    response, _meta = orchestrator.respond(user_text)
    return response
