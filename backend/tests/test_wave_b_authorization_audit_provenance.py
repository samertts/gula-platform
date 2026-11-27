from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from app.identity.api import audit as audit_api
from app.identity.models.audit import AuditAction, IdentityAuditEntry
from app.identity.services.audit_service import compute_audit_entry_hash
from app.identity.services.canonical_audit import (
    AuditEventInput,
    CanonicalAuditService,
    IntegrityStatus,
)


class _Result:
    def __init__(self, values: list[object] | None = None, scalar: object | None = None) -> None:
        self.values = values or []
        self.scalar = scalar

    def scalars(self) -> _Result:
        return self

    def all(self) -> list[object]:
        return self.values

    def scalar_one_or_none(self) -> object | None:
        return self.scalar


class _ProvenanceSession:
    def __init__(self) -> None:
        self.entries: list[IdentityAuditEntry] = []
        self._counter = 0

    async def execute(self, statement):
        compiled = statement.compile()
        sql = str(compiled)
        values: set[object] = set()
        for value in compiled.params.values():
            if isinstance(value, (list, tuple, set, frozenset)):
                values.update(value)
            else:
                values.add(value)
        has_authz_actions = any(
            isinstance(value, str) and value.startswith("AUTHZ_") for value in values
        )
        if has_authz_actions:
            selected = [
                entry
                for entry in self.entries
                if entry.event_version == "1"
                and entry.entry_hash is not None
                and isinstance(entry.action, str)
                and entry.action.startswith("AUTHZ_")
            ]
        elif "2" in values:
            selected = [entry for entry in self.entries if entry.event_version == "2"]
        else:
            selected = []
        if "LIMIT" in sql and "entry_hash" in sql:
            return _Result(scalar=selected[-1].entry_hash if selected else None)
        return _Result(values=list(selected))

    def add(self, entry: IdentityAuditEntry) -> None:
        self._counter += 1
        if isinstance(entry, IdentityAuditEntry):
            entry.id = f"V2{self._counter:024d}"[:26]
            entry.uuid = f"uuid-v2-{self._counter}"
            self.entries.append(entry)

    async def flush(self) -> None:
        return None


def _legacy_decision(
    index: int,
    action: str,
    previous_hash: str | None,
    *,
    organization_id: str = "org-1",
) -> IdentityAuditEntry:
    occurred_at = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=index)
    entry = IdentityAuditEntry(
        id=f"V1{index:024d}"[:26],
        uuid=f"uuid-v1-{index}",
        action=action,
        event_version="1",
        actor_id="account-1",
        actor_type="account",
        target_type="federation_trust",
        target_id="trust-1",
        occurred_at=occurred_at,
        organization_id=organization_id,
        outcome="denied" if action == AuditAction.authz_deny.value else "success",
        previous_hash=previous_hash,
    )
    entry.entry_hash = compute_audit_entry_hash(
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
    return entry


def test_legacy_authorization_chain_is_verifiable_and_tamper_detected() -> None:
    first = _legacy_decision(0, AuditAction.authz_deny.value, None)
    second = _legacy_decision(
        1,
        AuditAction.authz_allow_sensitive.value,
        first.entry_hash,
    )
    result = CanonicalAuditService._verify_legacy_authorization_entries([first, second])
    assert result["status"] == IntegrityStatus.valid.value
    assert result["entries_checked"] == 2

    second.action = AuditAction.authz_privilege_escalation_attempt.value
    tampered = CanonicalAuditService._verify_legacy_authorization_entries([first, second])
    assert tampered["status"] == IntegrityStatus.invalid.value
    assert any(item["reason"] == "event_hash_mismatch" for item in tampered["violations"])


async def test_provenance_verification_includes_both_authorization_streams() -> None:
    session = _ProvenanceSession()
    first = _legacy_decision(0, AuditAction.authz_deny.value, None)
    second = _legacy_decision(
        1,
        AuditAction.authz_allow_sensitive.value,
        first.entry_hash,
    )
    session.entries.extend([first, second])
    await CanonicalAuditService(session).record(
        AuditEventInput(
            event_type="authorization.guard.decision",
            category="security",
            action="establish",
            actor_id="account-1",
            organization_id="org-1",
            target_type="federation_trust",
            decision="allow",
            source="niam_authorization_guard",
        ),
    )

    result = await CanonicalAuditService(session).verify_authorization_provenance(
        organization_id="org-1",
    )

    provenance = result["authorization_provenance"]
    assert provenance["status"] == IntegrityStatus.valid.value
    assert provenance["legacy_authorization_chain"]["entries_checked"] == 2
    assert provenance["canonical_v2_chain"]["entries_checked"] == 1
    assert result["entries_checked"] == 1
    assert "no cross-version chain continuity is claimed" in provenance["coverage"]


async def test_integrity_endpoint_exposes_authorization_provenance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _no_permission_check(*args, **kwargs):
        del args, kwargs
        return

    monkeypatch.setattr(audit_api, "_require_audit_permission", _no_permission_check)
    result = await audit_api.verify_audit_integrity(
        organization_id="org-1",
        occurred_from=None,
        occurred_to=None,
        actor=SimpleNamespace(),
        db=_ProvenanceSession(),  # type: ignore[arg-type]
    )

    assert "authorization_provenance" in result
    assert result["authorization_provenance"]["status"] == IntegrityStatus.incomplete.value
