# Guía de instalación local

## Requisitos
- Python 3.12+
- pip

## Pasos rápidos
```bash
pip install -r requirements.txt
export JWT_SECRET="tu-secreto-seguro"
python -m uvicorn app:app --reload --port 8000
```

Abrir: `http://localhost:8000`

## Docker Compose
```bash
docker compose -f infra/docker/docker-compose.yml up --build
```
