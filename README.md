# nexoraAI

Prototipo de asistente personal con IA sobre **FastAPI**, con bot de Telegram,
memoria en Redis y búsqueda web (Tavily). Desplegado en Railway durante su
fase de pruebas.

> **Estado honesto:** prototipo de marzo 2026, desarrollo **pausado**.
> El código funciona como monolito (`app.py`, ~57 KB); la modularización
> quedó iniciada en `core/orchestrator.py` y el paquete `nexoraAI/`.
> Los archivos `ai_core.py`, `config.py`, `memory.py`, `routes.py` y
> `telegram_actor.py` son marcadores de esa refactorización pendiente.

## Stack

- Python + FastAPI + Uvicorn
- `python-telegram-bot` 21.10 (canal de Telegram)
- OpenAI (modelo de lenguaje)
- Redis + hiredis (memoria/caché)
- Tavily (búsqueda web)

## Ejecutar

```bash
pip install -r requirements.txt
cp .env.example .env   # completar credenciales
uvicorn app:app --host 0.0.0.0 --port 8000
```

`Procfile` y `runtime.txt` reflejan el despliegue original en Railway.

## Nota

Este repositorio se conserva como registro público del experimento.
No acepta contribuciones; se mantiene tal cual por transparencia del recorrido.
