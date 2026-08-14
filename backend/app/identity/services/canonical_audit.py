from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.identity.models.audit import IdentityAuditEntry


class IntegrityStatus(StrEnum):
    valid = "VALID"
    invalid = "INVALID"
    incomplete = "INCOMPLETE"


class AuditAccessError(PermissionError):
    pass


@dataclass(frozen=True)
class AuditEventInput:
    event_type: str
    category: str
    action: str
    actor_id: str | None = None
    actor_identity_id: str | None = None
    actor_type: str = "human"
    organization_id: str | None = None
    facility_id: str | None = None
    department_id: str | None = None
    workspace_id: str | None = None
    target_type: str | None = None
    target_id: str | None = None
    decision: str | None = None
    reason_code: str | None = None
    request_id: str | None = None
    correlation_id: str | None = None
    session_id: str | None = None
    source: str = "api"
    data_classification: str = "INTERNAL"
    changes: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    context: dict[str, Any] | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    outcome: str = "success"
    error_message: str | None = None


_SECRET_KEYS = frozenset(
    {
        "password",
        "token",
        "access_token",
        "refresh_token",
        "authorization",
        "cookie",
        "otp",
        "secret",
        "private_key",
        "credentials",
        "credentials_encrypted",
    },
)


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): "[REDACTED]" if str(key).lower() in _SECRET_KEYS else _redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact(item) for item in value[:100]]
    if isinstance(value, str):
        return value[:2000]
    return value


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class CanonicalAuditService:
    """Append-only Phase 9 audit stream over the existing NIAM audit table."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _canonical_payload(entry: IdentityAuditEntry) -> str:
        payload = {
            "action": entry.action,
            "actor_id": entry.actor_id,
            "actor_identity_id": entry.actor_identity_id,
            "actor_type": entry.actor_type,
            "category": entry.category,
            "changes": _redact(entry.changes),
            "context": _redact(entry.context),
            "correlation_id": entry.correlation_id,
            "data_classification": entry.data_classification,
            "decision": entry.decision,
            "department_id": entry.department_id,
            "event_type": entry.event_type,
            "event_version": entry.event_version,
            "facility_id": entry.facility_id,
            "id": entry.id,
            "metadata": _redact(entry.extra_data),
            "organization_id": entry.organization_id,
            "outcome": entry.outcome,
            "previous_hash": entry.previous_hash,
            "reason_code": entry.reason_code,
            "request_id": entry.request_id,
            "session_id": entry.session_id,
            "source": entry.source,
            "target_id": entry.target_id,
            "target_type": entry.target_type,
            "workspace_id": entry.workspace_id,
            "occurred_at": _utc(entry.occurred_at).isoformat(timespec="microseconds"),
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @classmethod
    def _hash(cls, entry: IdentityAuditEntry) -> str:
        return hashlib.sha256(cls._canonical_payload(entry).encode("utf-8")).hexdigest()

    async def _last_canonical_hash(self) -> str | None:
        result = await self.session.execute(
            select(IdentityAuditEntry.entry_hash)
            .where(IdentityAuditEntry.event_version == "2")
            .order_by(IdentityAuditEntry.occurred_at.desc(), IdentityAuditEntry.id.desc())
            .limit(1)
            .with_for_update(),
        )
        return result.scalar_one_or_none()

    async def record(self, event: AuditEventInput) -> IdentityAuditEntry:
        occurred_at = datetime.now(UTC)
        entry = IdentityAuditEntry(
            event_type=event.event_type,
            event_version="2",
            category=event.category,
            action=event.action,
            actor_id=event.actor_id,
            actor_identity_id=event.actor_identity_id,
            actor_type=event.actor_type,
            target_type=event.target_type,
            target_id=event.target_id,
            facility_id=event.facility_id,
            department_id=event.department_id,
            workspace_id=event.workspace_id,
            decision=event.decision,
            reason_code=event.reason_code,
            request_id=event.request_id,
            correlation_id=event.correlation_id,
            source=event.source,
            data_classification=event.data_classification,
            changes=_redact(event.changes),
            extra_data=_redact(event.metadata),
            context=_redact(event.context),
            ip_address=event.ip_address,
            user_agent=event.user_agent[:500] if event.user_agent else None,
            session_id=event.session_id,
            occurred_at=occurred_at,
            organization_id=event.organization_id,
            outcome=event.outcome,
            error_message=event.error_message,
        )
        entry.previous_hash = await self._last_canonical_hash()
        self.session.add(entry)
        await self.session.flush()
        entry.entry_hash = self._hash(entry)
        await self.session.flush()
        return entry

    async def search(
        self,
        *,
        organization_id: str,
        limit: int = 100,
        offset: int = 0,
        actor_id: str | None = None,
        event_type: str | None = None,
        resource_type: str | None = None,
        decision: str | None = None,
        facility_id: str | None = None,
        workspace_id: str | None = None,
        occurred_from: datetime | None = None,
        occurred_to: datetime | None = None,
    ) -> list[IdentityAuditEntry]:
        conditions = [
            IdentityAuditEntry.event_version == "2",
            IdentityAuditEntry.organization_id == organization_id,
        ]
        optional = {
            IdentityAuditEntry.actor_id: actor_id,
            IdentityAuditEntry.event_type: event_type,
            IdentityAuditEntry.target_type: resource_type,
            IdentityAuditEntry.decision: decision,
            IdentityAuditEntry.facility_id: facility_id,
            IdentityAuditEntry.workspace_id: workspace_id,
        }
        conditions.extend(column == value for column, value in optional.items() if value is not None)
        if occurred_from is not None:
            conditions.append(IdentityAuditEntry.occurred_at >= occurred_from)
        if occurred_to is not None:
            conditions.append(IdentityAuditEntry.occurred_at < occurred_to)
        result = await self.session.execute(
            select(IdentityAuditEntry)
            .where(and_(*conditions))
            .order_by(IdentityAuditEntry.occurred_at.desc(), IdentityAuditEntry.id.desc())
            .offset(max(offset, 0))
            .limit(min(max(limit, 1), 100)),
        )
        return list(result.scalars().all())

    async def verify(
        self,
        *,
        organization_id: str | None = None,
        occurred_from: datetime | None = None,
        occurred_to: datetime | None = None,
    ) -> dict[str, Any]:
        conditions = [IdentityAuditEntry.event_version == "2"]
        if organization_id is not None:
            conditions.append(IdentityAuditEntry.organization_id == organization_id)
        if occurred_from is not None:
            conditions.append(IdentityAuditEntry.occurred_at >= occurred_from)
        if occurred_to is not None:
            conditions.append(IdentityAuditEntry.occurred_at < occurred_to)
        result = await self.session.execute(
            select(IdentityAuditEntry)
            .where(and_(*conditions))
            .order_by(IdentityAuditEntry.occurred_at.asc(), IdentityAuditEntry.id.asc()),
        )
        entries = list(result.scalars().all())
        if not entries:
            return {"status": IntegrityStatus.incomplete.value, "entries_checked": 0, "violations": []}
        violations: list[dict[str, Any]] = []
        previous_hash = entries[0].previous_hash
        for index, entry in enumerate(entries):
            expected_previous = previous_hash if index == 0 else entries[index - 1].entry_hash
            if entry.previous_hash != expected_previous:
                violations.append({"id": entry.id, "reason": "previous_hash_mismatch", "expected": expected_previous, "actual": entry.previous_hash})
            expected_hash = self._hash(entry)
            if entry.entry_hash != expected_hash:
                violations.append({"id": entry.id, "reason": "event_hash_mismatch", "expected": expected_hash, "actual": entry.entry_hash})
        return {
            "status": IntegrityStatus.invalid.value if violations else IntegrityStatus.valid.value,
            "entries_checked": len(entries),
            "violations": violations[:100],
            "first_event_id": entries[0].id,
            "last_event_id": entries[-1].id,
        }
