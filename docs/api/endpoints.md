# Endpoints MVP

## Auth
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`

## Usuario
- `GET /user/profile`
- `PUT /user/profile`

## Conversaciones/Mensajes
- `POST /conversations`
- `GET /conversations`
- `GET /conversations/{conversation_id}/messages`
- `POST /conversations/{conversation_id}/messages`

## Memoria
- `GET /memory`
- `POST /memory`
- `DELETE /memory/{memory_id}`

## Tareas
- `GET /tasks`
- `POST /tasks`
- `PATCH /tasks/{task_id}`

## Dispositivos
- `GET /devices`
- `POST /devices`

## Notificaciones
- `GET /notifications`
- `POST /notifications/read`

## Seguridad
- `GET /security/logs`

## WebSocket
- `WS /ws/live-chat?token=<access_token>[&conversation_id=<id>]`
  - eventos: `typing_state`, `avatar_state`, `message`, `error`
