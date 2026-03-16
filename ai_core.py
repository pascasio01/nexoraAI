from services.orchestrator.engine import Orchestrator

orchestrator = Orchestrator()


def ask_nexora(user_id: str, text: str, channel: str = "web") -> str:
    del user_id, channel
    response, _meta = orchestrator.respond(text)
    return response
