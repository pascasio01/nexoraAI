# NEXORA OMNI · MVP Base

NEXORA OMNI es una base funcional de asistente AI persistente y modular con arquitectura orientada a evolución.

## Qué incluye este MVP
- Monorepo base (`apps/`, `services/`, `packages/`, `infra/`, `docs/`)
- API Gateway con FastAPI
- Registro/login JWT + refresh token + sesiones por dispositivo
- Perfil de usuario
- Chat persistente + historial de conversaciones/mensajes
- WebSocket de chat en tiempo real
- Orchestrator + Decision Engine + Memory Engine
- Memoria persistente (short/mid/long term)
- Endpoints para tareas, dispositivos, notificaciones y logs de seguridad
- Web UI conversacional mobile-first con avatar básico (`idle/listening/thinking/responding`)
- Docker Compose con PostgreSQL + pgvector listo para evolución

## Estructura
Ver `docs/product/monorepo.md`.

## Ejecutar local
```bash
pip install -r requirements.txt
export JWT_SECRET="tu-secreto-seguro"
python -m uvicorn app:app --reload --port 8000
```
Abrir `http://localhost:8000`.

## Documentación
- Arquitectura: `docs/architecture/overview.md`
- Setup local: `docs/architecture/local-setup.md`
- API: `docs/api/endpoints.md`
- Roadmap: `docs/product/roadmap.md`
- ADR inicial: `docs/decisions/adr-0001-initial-stack.md`

## Próximos pasos recomendados
1. Migrar persistencia de SQLite a PostgreSQL + pgvector en runtime.
2. Extraer API Gateway/Orchestrator/Memory/Decision como servicios independientes con mensajería.
3. Implementar app mobile React Native y componentes compartidos en `packages/ui`.
