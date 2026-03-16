# NEXORA OMNI · Arquitectura (MVP)

Capas activas en MVP:

1. **Orchestrator** (`services/orchestrator`): interpreta mensajes y coordina salida única.
2. **Decision Engine** (`services/decision_engine`): calcula autonomía (0-3), riesgo y razón.
3. **Life Memory** (`services/memory_engine` + tabla `memory_items`): short/mid/long-term persistente.
4. **API Gateway** (`services/api_gateway`): REST + WebSocket + auth + auditoría.

## Agentes especializados (estructura lista)
- Memory, Calendar, Finance, Wellness, Research, Security, Device, Communication, Notification.

## Persistencia
MVP corre sobre SQLite persistente (`data/nexora_omni.db`) con tablas para:
User, Device, Session, Conversation, Message, MemoryItem, Task, Notification, SecurityLog, UserPreference y DecisionLog.

## Evolución prevista
- Migración transparente a PostgreSQL + pgvector (infra base incluida)
- Servicios por dominio en contenedores independientes
- Mobile app y UI package compartido
