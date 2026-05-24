# Nexora / SORA — Personal Intelligence Layer Blueprint

## 1) Market gap analysis (current assistants)

Modern assistants (ChatGPT, Gemini, Siri, Alexa, most copilots) are strong at one-shot Q&A, but still weak in personal continuity:

- **No durable life memory** beyond short chat windows
- **Weak cross-device identity continuity** (web/mobile/voice context fragmentation)
- **Limited long-term user modeling** (habits, goals, relationships, routines)
- **Shallow multi-agent coordination** (single model + ad hoc tool calls)
- **Low autonomy maturity** (few explicit risk-governed autonomy levels)
- **Insufficient personal security intelligence** (scam/phishing/risky action detection)
- **Fragmented real-time stateful experience** across channels
- **Limited action graph execution** with strict permission boundaries

## 2) Product thesis

Nexora should evolve from a chatbot into a **Personal Intelligence Layer**:

- Always-on user context (memory + identity + goals)
- Explainable autonomy with permission and risk control
- Modular domain agents + secure tool execution
- Cross-device persistent presence and real-time state orchestration

## 3) Core architecture modules

The foundation implementation in `nexoraAI/personal_intelligence.py` includes:

1. **Orchestrator**
   - Receives user input from any channel
   - Resolves intent and risk
   - Queries memory and agent network
   - Applies autonomy policy
   - Logs decisions and state events

2. **Life Memory Engine**
   - Tiered storage: short / mid / long
   - Structured memory records: preference, goals, tasks, people, etc.
   - Edit/delete/privacy controls
   - Summarization + importance ranking

3. **Decision Engine**
   - Explicit autonomy levels (0..3)
   - Contextual risk and permission governance
   - Explainable decision logs

4. **Multi-Agent System**
   - Modular agent registry with required domains:
     memory, research, calendar, finance, wellness, communication, security, device, notification

5. **Tool Execution Layer**
   - Tool registry + permission checks
   - Action execution with auditable logs

6. **Cross-Device Presence**
   - Persistent user identity mapped to many channels/devices
   - Shared session continuity across interfaces

7. **Real-Time Interaction**
   - Assistant state events:
     `idle`, `listening`, `thinking`, `responding`
   - Event stream model compatible with WebSocket streaming

8. **Personal Security Layer**
   - Scam/suspicious request detection
   - Sensitive-data redaction support
   - Risky action guardrails

## 4) Technology stack direction

Near-term stack improvements to support scale:

- **Backend**: FastAPI + async orchestration runtime
- **Realtime**: WebSocket/SSE event channel with state/event schema
- **Memory**:
  - short-term: Redis
  - mid/long-term: Postgres + vector index
- **Orchestration**: policy-driven orchestrator + agent registry
- **Observability**: OpenTelemetry traces + decision/audit logs
- **Security**: policy engine (permissions, risk scoring, PII controls)

## 5) Evolution roadmap

### MVP (0-3 months)
- Stable orchestrator contracts
- Memory tiers + CRUD/privacy
- Autonomy levels 0-2
- Core agents (memory/research/calendar/notification/security)

### Growth (3-9 months)
- Autonomy level 3 (strict bounded domains)
- Cross-device context sync
- Real-time voice/avatar states
- Security anomaly detection improvements

### Platform (9-18 months)
- Personal knowledge graph
- Long-horizon planning and proactive workflows
- Personal decision support and life archive system

## 6) Risks and mitigations

- **Over-autonomy risk** → enforce autonomy levels, hard permission boundaries, reversible actions
- **Privacy risk** → user-owned memory controls, redact pipelines, clear retention policies
- **Hallucinated actions** → tool schema validation + confirmation workflows
- **Fragmented UX** → unified identity/session context APIs
- **Scalability drift** → modular services, event-driven boundaries, explicit contracts
