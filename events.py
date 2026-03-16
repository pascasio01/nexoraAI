from datetime import datetime, timezone

from realtime_types import AssistantState, ConnectionContext

EVENT_VERSION = "1.0"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_event(event: str, context: ConnectionContext, data: dict | None = None) -> dict:
    return {
        "event": event,
        "data": data or {},
        "meta": {
            "version": EVENT_VERSION,
            "timestamp": _now_iso(),
            "user_id": context.user_id,
            "session_id": context.session_id,
            "room_id": context.room_id,
            "site_id": context.site_id,
            "visitor_id": context.visitor_id,
            "device_id": context.device_id,
        },
    }


def assistant_state_event(state: AssistantState, context: ConnectionContext) -> dict:
    return make_event("assistant.state", context, {"state": state.value})


def user_message_event(text: str, context: ConnectionContext) -> dict:
    return make_event("message.user", context, {"text": text})


def assistant_message_event(text: str, context: ConnectionContext, partial: bool = False) -> dict:
    return make_event("message.assistant", context, {"text": text, "partial": partial})


def typing_start_event(context: ConnectionContext) -> dict:
    return make_event("typing.start", context)


def typing_stop_event(context: ConnectionContext) -> dict:
    return make_event("typing.stop", context)


def error_event(message: str, context: ConnectionContext) -> dict:
    return make_event("error", context, {"message": message})
