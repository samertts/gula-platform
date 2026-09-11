from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app._compat import UTC
from app.identity.models.audit import AuditAction, IdentityAuditEntry


class AuditService:

    def __init__(self, session: Session) -> None:
        self.session = session

    def _get_last_entry_hash(self) -> str | None:
        stmt = (
            select(IdentityAuditEntry.entry_hash)
            .where(IdentityAuditEntry.entry_hash.isnot(None))
            .order_by(desc(IdentityAuditEntry.occurred_at))
            .limit(1)
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def _compute_hash(
        self,
        entry_id: str,
        uuid_str: str,
        action: str,
        actor_id: str | None,
        target_type: str | None,
        target_id: str | None,
        occurred_at: str,
        outcome: str,
        previous_hash: str | None,
        organization_id: str | None = None,
    ) -> str:
        content = {
            "id": entry_id,
            "uuid": uuid_str,
            "action": action,
            "actor_id": actor_id,
            "target_type": target_type,
            "target_id": target_id,
            "occurred_at": occurred_at,
            "outcome": outcome,
            "organization_id": organization_id,
            "previous_hash": previous_hash,
        }
        raw = json.dumps(content, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def record(
        self,
        action: AuditAction,
        actor_id: str | None = None,
        actor_type: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        changes: dict | None = None,
        metadata: dict | None = None,
        context: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        session_id: str | None = None,
        organization_id: str | None = None,
        outcome: str = "success",
        error_message: str | None = None,
    ) -> IdentityAuditEntry:
        entry_id = str(uuid.uuid4()).replace("-", "").upper()[:26]
        uuid_str = str(uuid.uuid4())
        occurred_at = datetime.now(UTC)
        previous_hash = self._get_last_entry_hash()
        entry_hash = self._compute_hash(
            entry_id=entry_id,
            uuid_str=uuid_str,
            action=action.value,
            actor_id=actor_id,
            target_type=target_type,
            target_id=target_id,
            occurred_at=occurred_at.isoformat(),
            outcome=outcome,
            previous_hash=previous_hash,
            organization_id=organization_id,
        )

        entry = IdentityAuditEntry(
            id=entry_id,
            uuid=uuid_str,
            entry_hash=entry_hash,
            previous_hash=previous_hash,
            action=action.value,
            actor_id=actor_id,
            actor_type=actor_type,
            target_type=target_type,
            target_id=target_id,
            changes=changes,
            extra_data=metadata,
            context=context,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            occurred_at=occurred_at,
            organization_id=organization_id,
            outcome=outcome,
            error_message=error_message,
        )
        self.session.add(entry)
        self.session.flush()
        return entry

    def record_event(
        self,
        action: str,
        actor_id: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        metadata: dict | None = None,
        organization_id: str | None = None,
        outcome: str = "success",
    ) -> IdentityAuditEntry:
        entry_id = str(uuid.uuid4()).replace("-", "").upper()[:26]
        uuid_str = str(uuid.uuid4())
        occurred_at = datetime.now(UTC)
        previous_hash = self._get_last_entry_hash()
        entry_hash = self._compute_hash(
            entry_id=entry_id,
            uuid_str=uuid_str,
            action=action,
            actor_id=actor_id,
            target_type=target_type,
            target_id=target_id,
            occurred_at=occurred_at.isoformat(),
            outcome=outcome,
            previous_hash=previous_hash,
            organization_id=organization_id,
        )

        entry = IdentityAuditEntry(
            id=entry_id,
            uuid=uuid_str,
            entry_hash=entry_hash,
            previous_hash=previous_hash,
            action=action,
            actor_id=actor_id,
            target_type=target_type,
            target_id=target_id,
            extra_data=metadata,
            occurred_at=occurred_at,
            organization_id=organization_id,
            outcome=outcome,
        )
        self.session.add(entry)
        self.session.flush()
        return entry

    def verify_chain_integrity(self) -> list[dict]:
        stmt = (
            select(IdentityAuditEntry)
            .where(IdentityAuditEntry.entry_hash.isnot(None))
            .order_by(IdentityAuditEntry.occurred_at)
        )
        result = self.session.execute(stmt)
        entries = list(result.scalars().all())
        violations = []
        for i, entry in enumerate(entries):
            expected_previous = entries[i - 1].entry_hash if i > 0 else None
            if entry.previous_hash != expected_previous:
                violations.append({
                    "id": entry.id,
                    "uuid": entry.uuid,
                    "expected_previous": expected_previous,
                    "actual_previous": entry.previous_hash,
                    "reason": "previous_hash_mismatch",
                })
            computed = self._compute_hash(
                entry_id=entry.id,
                uuid_str=entry.uuid,
                action=entry.action,
                actor_id=entry.actor_id,
                target_type=entry.target_type,
                target_id=entry.target_id,
                occurred_at=entry.occurred_at.isoformat(),
                outcome=entry.outcome,
                previous_hash=entry.previous_hash,
                organization_id=entry.organization_id,
            )
            if computed != entry.entry_hash:
                violations.append({
                    "id": entry.id,
                    "uuid": entry.uuid,
                    "computed": computed,
                    "stored": entry.entry_hash,
                    "reason": "hash_mismatch",
                })
        return violations
