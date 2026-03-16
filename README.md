# nexoraAI

## Realtime event envelope (WebSocket)

`/ws` uses JSON envelopes:

```json
{
  "event": "assistant.state",
  "data": {"state": "thinking"},
  "meta": {
    "version": "1.0",
    "timestamp": "2026-03-16T00:00:00+00:00",
    "user_id": "u1",
    "session_id": "s1",
    "room_id": "r1",
    "site_id": "site-a",
    "visitor_id": "v1",
    "device_id": "device-ios"
  }
}
```

Supported events: `message.user`, `message.assistant`, `assistant.state`, `typing.start`, `typing.stop`, `error`.

Assistant states: `idle`, `listening`, `thinking`, `responding`.
