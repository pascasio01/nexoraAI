# SORA OMNI / Nexora — Personal Intelligence Layer Blueprint

This document defines the target architecture and product direction for evolving Nexora from a chatbot into a persistent **Personal Intelligence Layer**.

## 1) Current Landscape Analysis: Why Existing Assistants Fall Short

### ChatGPT / Gemini / Other LLM chat assistants
- **Session-first, life-second:** strong in conversation but weak at persistent, user-controlled life memory.
- **Limited cross-device identity continuity:** context often resets by channel, account boundary, or app surface.
- **Weak real-world execution:** can suggest actions, but tool/action depth is often narrow, fragmented, or gated.
- **Low personal-state awareness:** minimal modeling of long-running goals, routines, constraints, and relationships.

### Google Search
- **Information retrieval, not personal intelligence:** excellent index and ranking, but no deep user life model.
- **Decision support is indirect:** user must synthesize and decide manually across many results.
- **No coherent life memory graph:** query history is not equivalent to structured life knowledge.

### Siri / Alexa
- **Command-oriented architecture:** strong for simple tasks; weak for multi-step reasoning and planning.
- **Shallow contextual memory:** limited continuity across long horizons and nuanced personal context.
- **Low agent composability:** difficult to orchestrate many specialized capabilities with shared context.

### Core Gaps Across the Market
1. Lack of persistent life memory.
2. Lack of unified cross-device identity.
3. Weak personal context understanding.
4. Fragmented UX across channels/devices.
5. Limited real-world action capability.
6. Minimal decision autonomy with safety tiers.
7. Poor long-term personal knowledge modeling.
8. Weak personal security intelligence.
9. Weak multi-agent orchestration under one brain.

---

## 2) Product Vision

**SORA OMNI / Nexora** is a continuous, secure, cross-device intelligence presence that helps users:
- think better,
- remember better,
- decide better,
- and act faster.

It blends strengths of:
- conversational AI,
- search/research engines,
- personal assistants,
- knowledge management systems,
- and decision support systems.

> North Star: The user feels they are interacting with *one evolving intelligence* that knows their priorities, remembers context, and executes safely.

---

## 3) Reference Architecture

## 3.1 Interface Layer
Unified user experience across:
- Web app
- Mobile app
- Messaging channels (Telegram, WhatsApp, etc.)
- Voice surfaces
- Future IoT/ambient interfaces

**Requirement:** single user identity and state continuity across every interface.

## 3.2 API Gateway
Responsibilities:
- Authentication and authorization
- Session lifecycle
- Request validation and normalization
- Routing to backend domains
- Unified ingress for every channel

## 3.3 Orchestrator (Core Brain)
Central runtime that:
- receives user input,
- detects intent,
- retrieves relevant memory,
- plans execution,
- invokes domain agents/tools,
- merges outputs,
- preserves conversational state.

## 3.4 Multi-Agent System
Modular, independently deployable agents:
- **Memory Agent** — memory extraction, ranking, retrieval, consolidation.
- **Research Agent** — search, source comparison, evidence synthesis.
- **Calendar Agent** — scheduling, conflict detection, priority-aware planning.
- **Finance Agent** — budgets, reminders, risk flags, trend summaries.
- **Wellness Agent** — habits, routines, wellbeing insights.
- **Communication Agent** — message drafting, summaries, follow-ups.
- **Security Agent** — scam/risk detection, sensitive-action checks.
- **Device Agent** — cross-device awareness and action coordination.
- **Notification Agent** — timing, channel selection, escalation logic.

Design rules:
- clear contracts (typed input/output),
- stateless execution where possible,
- versioned interfaces,
- observable traces.

## 3.5 Decision Engine
Evaluates:
- context,
- permissions,
- risk,
- priority,
- user preference.

Autonomy tiers:
- **Level 0:** recommend only
- **Level 1:** prepare action, ask for confirmation
- **Level 2:** execute with pre-granted permission
- **Level 3:** execute automatically within strict policy guardrails

Every decision writes:
- structured logs,
- action rationale,
- confidence and risk notes.

## 3.6 Life Memory Engine
Structured memory model (not plain transcript storage):
- habits,
- preferences,
- relationships,
- important events,
- tasks,
- projects,
- goals,
- wellness patterns.

Memory horizons:
- **Short-term** (current dialog context)
- **Mid-term** (recent tasks/routines)
- **Long-term** (stable life knowledge graph)

User controls:
- edit/delete memory,
- privacy scopes,
- memory importance weighting,
- retention policies.

## 3.7 Tool Execution Layer
Tool adapters for:
- web search,
- notes,
- tasks,
- reminders,
- calendar events,
- webhooks,
- third-party APIs.

All tools enforce:
- permission checks,
- policy validation,
- audit logging.

## 3.8 Real-Time Interaction Layer
Capabilities:
- WebSockets transport,
- token/stream response delivery,
- assistant state events.

State machine (minimum):
- `idle`
- `listening`
- `thinking`
- `responding`

This enables future avatars, voice loops, and ambient interaction.

## 3.9 Personal Security Layer
Security intelligence includes:
- scam/phishing signal detection,
- sensitive-data exposure prevention,
- suspicious activity monitoring,
- risk warnings for high-impact actions.

Security controls:
- JWT access tokens + refresh tokens,
- device-bound sessions,
- security logs,
- explicit confirmation for sensitive operations.

---

## 4) User Experience System

Primary UX surfaces:
- conversational timeline,
- floating avatar assistant,
- voice + text input,
- conversation history,
- memory panel,
- task manager,
- device manager,
- security dashboard.

Experience principles:
- **Modern:** clean, responsive, uncluttered.
- **Calm:** low-noise interaction with sensible defaults.
- **Intelligent:** proactive but non-intrusive guidance.
- **Persistent:** seamless continuity across sessions/devices.

---

## 5) Recommended Technology Stack

- **Frontend:** Next.js + TypeScript + Tailwind
- **Mobile:** React Native
- **Backend:** FastAPI or NestJS
- **Primary DB:** PostgreSQL
- **Vector layer:** pgvector
- **Realtime:** WebSockets
- **Infra:** Docker + cloud deployment

Additional platform requirements:
- OpenTelemetry-based tracing,
- queue/workflow system for asynchronous actions,
- secrets management,
- policy engine for tool/action governance.

---

## 6) Evolution Roadmap

1. **Phase 1 — Core Platform**
   - Backend foundation, auth, base chat runtime.
2. **Phase 2 — Memory + Realtime**
   - Persistent memory primitives, WebSocket streaming.
3. **Phase 3 — Orchestrator + Agent Mesh**
   - Intent routing, modular domain agents.
4. **Phase 4 — Decision + Tools**
   - Policy-aware autonomy and robust action execution.
5. **Phase 5 — Voice + Avatar Presence**
   - Full duplex voice UX, stateful avatar interactions.
6. **Phase 6 — Cross-Device Intelligence Layer**
   - Unified identity and continuity across personal digital surfaces.

---

## 7) Competitive Advantage

This architecture can surpass current assistants by delivering:
- **Persistent intelligence:** continuity over months/years.
- **Personal life memory:** structured, user-controlled knowledge.
- **Cross-device identity:** one assistant presence everywhere.
- **Modular agent ecosystem:** faster capability expansion.
- **Controlled autonomy:** useful automation with clear safety tiers.
- **Strong security intelligence:** trust as a core feature, not an add-on.

In short: Nexora evolves from an answer engine into a **long-term cognitive partner** that helps users remember, organize, decide, and act.
