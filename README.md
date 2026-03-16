# nexoraAI

## Personal agent network foundation

`nexoraAI/orchestrator.py` now includes a minimal foundation for a future personal agent network:

- One `PersonalAgent` instance per user via `Orchestrator.get_or_create_agent(...)`
- Agent-to-agent communication using structured JSON `AgentEvent` objects
- Explicit task delegation through `Orchestrator.request_task(...)` with `task.requested` events

This is intentionally lightweight and backward-compatible so future agent-network features can be added incrementally.
