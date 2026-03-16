# ADR-0001: Base tecnológica inicial

## Decisión
Mantener FastAPI en MVP actual para estabilizar rápidamente la plataforma y habilitar evolución por servicios.

## Razón
El repositorio existente ya estaba orientado a Python, con fallas de compilación activas. Se prioriza un MVP funcional y auditable de inmediato.

## Consecuencia
La estructura monorepo deja servicios desacoplados y contratos listos para migración gradual a stack objetivo (NestJS/Next.js/React Native) sin romper datos ni API.
