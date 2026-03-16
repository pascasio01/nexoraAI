from __future__ import annotations

from typing import Any


def build_platform_blueprint() -> dict[str, Any]:
    """Return the product + architecture foundation for Nexora/Sora messaging.

    The blueprint intentionally separates MVP-deliverable components from
    future-ready interfaces so the team can iterate without breaking security,
    realtime quality, or cross-device continuity.
    """

    return {
        "vision": "Private communication and personal AI platform, not a standalone chatbot.",
        "messaging_capabilities": {
            "mvp": [
                "one_to_one_chat",
                "group_chat",
                "multi_device_messaging",
                "persistent_history",
                "text_messages",
                "image_sharing",
                "video_sharing",
                "audio_messages",
                "document_sharing",
                "pdf_sharing",
                "file_attachments",
                "typing_indicators",
                "delivery_states",
                "read_states",
            ],
            "next": ["message_reactions", "message_replies", "threaded_context"],
        },
        "identity_and_continuity": {
            "primary_ids": ["user_id", "session_id", "device_id", "room_id"],
            "compatibility_ids": ["site_id", "visitor_id"],
            "device_trust": "Each device maintains a trust state and key version metadata.",
            "session_policy": "Short-lived sessions with rotation and sensitive-action re-authentication.",
        },
        "security_architecture": {
            "transport": "TLS everywhere, websocket auth tokens, strict origin checks.",
            "message_protection": "Envelope model with encrypted_payload slot and metadata separation.",
            "mvp_crypto": "Server-managed encryption-at-rest + per-room key version metadata.",
            "envelope_note": "encrypted_payload is present from day one so clients can migrate to end-to-end encryption without schema breaks.",
            "e2ee_path": [
                "Introduce device key bundles and signed prekeys",
                "Move content encryption to clients with double-ratchet-compatible envelopes",
                "Retain server-side searchable minimal metadata only",
                "Roll out key-rotation and secure device handoff UX",
            ],
            "controls": [
                "private_rooms",
                "room_permissions",
                "sensitive_action_confirmations",
                "privacy_controls",
                "security_audit_logs",
            ],
            "file_handling": "Malware scan, content-type validation, signed download URLs, expiring access grants.",
        },
        "service_boundaries": {
            "identity_service": "User auth, device registry, trust levels, consent and privacy preferences.",
            "messaging_service": "Room membership, message lifecycle, delivery/read states, reactions/replies roadmap.",
            "realtime_gateway": "WebSocket fanout, presence, typing and assistant streaming states.",
            "file_service": "Upload issuance, storage pointers, checksums, retention and ACL policy.",
            "media_service": "Media transcode/thumbnail jobs and adaptive delivery metadata.",
            "transfer_service": "Cloud transfer now; future local Wi-Fi, Bluetooth, QR pairing and discovery interfaces.",
            "assistant_integration_layer": "Assistant invocation policy, context retrieval, summarization/translation/drafting hooks.",
            "notification_service": "Push delivery orchestration and cross-device unread sync.",
            "security_service": "Audit events, key metadata, policy enforcement, anomaly detection.",
            "device_service": "Device linking, revocation, secure handoff, per-device capability matrix.",
        },
        "realtime_contracts": {
            "events": [
                "message.send",
                "message.receive",
                "message.delivered",
                "message.read",
                "typing.start",
                "typing.stop",
                "user.online",
                "user.offline",
                "assistant.state",
            ],
            "assistant_state_values": [
                "queued",
                "thinking",
                "streaming",
                "tool_running",
                "completed",
                "error",
            ],
            "future_ready": ["voice_signaling", "video_signaling", "realtime_translation"],
        },
        "data_model_suggestions": {
            "users": ["user_id", "display_name", "privacy_settings", "created_at"],
            "devices": ["device_id", "user_id", "trust_level", "key_version", "last_seen_at"],
            "rooms": ["room_id", "room_type", "owner_user_id", "policy", "created_at"],
            "room_members": ["room_id", "user_id", "role", "joined_at"],
            "messages": [
                "message_id",
                "room_id",
                "sender_user_id",
                "encrypted_payload",
                "optional_searchable_metadata",
                "metadata_policy_ref:root.metadata_policy",
                "attachment_refs",
                "state",
                "created_at",
            ],
            "attachments": [
                "attachment_id",
                "message_id",
                "media_type",
                "storage_ref",
                "checksum",
                "size_bytes",
                "encryption_info",
            ],
            "assistant_sessions": ["assistant_session_id", "room_id", "invoked_by", "capabilities", "state"],
            "audit_logs": ["audit_id", "actor_id", "action", "target_id", "risk_level", "timestamp"],
        },
        "endpoint_ideas": {
            "http": [
                "POST /v1/rooms",
                "GET /v1/rooms/{room_id}/messages",
                "POST /v1/rooms/{room_id}/messages",
                "POST /v1/files/upload-url",
                "POST /v1/files/{file_id}/complete",
                "POST /v1/assistant/rooms/{room_id}/summarize",
                "POST /v1/assistant/rooms/{room_id}/translate",
                "POST /v1/devices/link",
                "POST /v1/devices/{device_id}/revoke",
            ],
            "websocket": "wss://.../v1/realtime?user_id=...&device_id=...&session_id=...",
        },
        "file_transfer_architecture": {
            "mvp": [
                "cloud_upload",
                "signed_download_links",
                "metadata_indexing",
                "attachment_permissions",
            ],
            "future_interfaces": {
                "local_wifi": "TransferStrategy.start_local_wifi_transfer(payload)",
                "bluetooth": "TransferStrategy.start_bluetooth_transfer(payload)",
                "qr_pairing": "DevicePairingService.create_qr_pairing_token(device_id)",
                "device_discovery": "DeviceDiscoveryService.list_nearby_capable_devices(user_id)",
            },
        },
        "assistant_inside_messaging": {
            "modes": [
                "on_demand_in_room",
                "summarization",
                "translation",
                "drafting",
                "task_extraction",
                "file_organization",
            ],
            "policy": "Assistant joins conversations only when invited and always emits visible assistant.state events.",
        },
        "competitive_differentiation": {
            "limits_in_current_apps": [
                "weak_personal_ai_continuity",
                "fragmented_cross_device_experience",
                "limited_file_intelligence",
                "opaque_privacy_tradeoffs",
            ],
            "nexora_advantage": [
                "assistant_per_user_memory_layer",
                "privacy_first_modular_security_model",
                "deep_file_and_knowledge_organization",
                "cross_device_and_local_transfer_readiness",
                "assistant_mediated_communication_workflows",
            ],
        },
        "mvp_scope": [
            "secure auth + device registry",
            "1:1 and group chat with persistent history",
            "websocket realtime events and presence",
            "file uploads for image/video/audio/docs/pdf",
            "assistant summarize/translate/draft/task extraction endpoints",
            "audit logging + privacy controls + security confirmations",
        ],
        "future_roadmap": {
            "phase_2": [
                "reaction/reply/threading",
                "message-level E2EE rollout",
                "cross-platform sync hardening",
                "smart categorization",
            ],
            "phase_3": [
                "voice_video_calls",
                "assistant_avatar",
                "realtime_translation",
                "secure_device_handoff",
                "local_file_relay",
            ],
        },
        "metadata_policy": "Optional searchable metadata must be content-free (never plaintext excerpts) and disabled for private/high-security rooms.",
        "risks_and_mitigations": [
            {
                "risk": "Realtime event inconsistency across devices",
                "mitigation": "Use idempotent event IDs, sequence numbers, and ack retry policy.",
            },
            {
                "risk": "Metadata leakage before full E2EE",
                "mitigation": "Minimize stored metadata and introduce progressive client-side encryption migration.",
            },
            {
                "risk": "Assistant overreach in private chats",
                "mitigation": "Require explicit assistant invocation and clear opt-in controls per room.",
            },
            {
                "risk": "Large-file abuse or malware",
                "mitigation": "Size quotas, scan pipeline, signed URL expiry, and abuse throttling.",
            },
        ],
    }
