from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC


@dataclass
class SecurityAuditEvent:
    event_id: str = ""
    event_type: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    user_id: str = ""
    user_role: str = ""
    action: str = ""
    resource_type: str = ""
    resource_id: str = ""
    patient_id: str | None = None
    outcome: str = ""
    reason: str = ""
    ip_address: str | None = None
    user_agent: str | None = None
    is_break_glass: bool = False
    break_glass_reason: str | None = None
    purpose_of_use: str | None = None
    details: dict[str, Any] | None = None
    immutable_hash: str | None = None


class SecurityAuditService:
    def __init__(self) -> None:
        self._events: list[SecurityAuditEvent] = []

    def log(self, event: SecurityAuditEvent) -> None:
        import hashlib
        import json
        import uuid

        event.event_id = str(uuid.uuid4())
        content = json.dumps(
            {
                "event_type": event.event_type,
                "timestamp": event.timestamp.isoformat(),
                "user_id": event.user_id,
                "action": event.action,
                "resource_type": event.resource_type,
                "resource_id": event.resource_id,
            },
            sort_keys=True,
        )
        prev_hash = self._events[-1].immutable_hash if self._events else "0" * 64
        event.immutable_hash = hashlib.sha256(f"{prev_hash}{content}".encode()).hexdigest()
        self._events.append(event)

    def get_events(
        self, resource_type: str | None = None, resource_id: str | None = None,
    ) -> list[SecurityAuditEvent]:
        results = self._events
        if resource_type:
            results = [e for e in results if e.resource_type == resource_type]
        if resource_id:
            results = [e for e in results if e.resource_id == resource_id]
        return results

    def verify_chain(self) -> bool:
        prev_hash = "0" * 64
        for event in self._events:
            if event.immutable_hash is None:
                return False
            if event.immutable_hash == prev_hash:
                continue
            prev_hash = event.immutable_hash
        return True
