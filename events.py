from __future__ import annotations

from typing import Any

from realtime_types import RealtimeContext, RealtimeEvent, RealtimeEventType


def build_event(event: RealtimeEventType, context: RealtimeContext, data: dict[str, Any] | None = None) -> RealtimeEvent:
    return RealtimeEvent(
        event=event,
        user_id=context.user_id,
        session_id=context.session_id,
        room_id=context.room_id,
        site_id=context.site_id,
        visitor_id=context.visitor_id,
        data=data or {},
    )
