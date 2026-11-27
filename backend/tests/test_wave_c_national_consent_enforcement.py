from __future__ import annotations

from types import SimpleNamespace

import pytest
from app.identity.models.audit import IdentityAuditEntry
from app.national.api.routes import security as security_routes
from app.national.security.consent_enforcement import (
    ConsentCheckResult,
    ConsentEnforcementService,
)
from fastapi import HTTPException


class _Result:
    def scalar_one_or_none(self):
        return None


class _AuditSession:
    def __init__(self) -> None:
        self.entries: list[IdentityAuditEntry] = []
        self._counter = 0

    async def execute(self, statement):
        del statement
        return _Result()

    def add(self, entry: IdentityAuditEntry) -> None:
        self._counter += 1
        if isinstance(entry, IdentityAuditEntry):
            entry.id = f"CONS{self._counter:022d}"[:26]
            entry.uuid = f"uuid-cons-{self._counter}"
            self.entries.append(entry)

    async def flush(self) -> None:
        return None


async def test_check_consent_fails_closed_and_audits_without_raw_identifier() -> None:
    session = _AuditSession()
    service = ConsentEnforcementService(session)  # type: ignore[arg-type]

    result = await service.check_consent(
        patient_id="RAW-PATIENT-IDENTIFIER-123",
        scope="laboratory_result",
        requestor_id="account-1",
        purpose="TREATMENT",
    )

    assert result.granted is False
    assert result.reason == ConsentEnforcementService.AUTHORITY_UNAVAILABLE
    assert result.scope == "laboratory_result"
    assert len(session.entries) == 1
    entry = session.entries[0]
    assert entry.event_version == "2"
    assert entry.decision == "DENY"
    assert entry.actor_id == "account-1"
    assert entry.reason_code == ConsentEnforcementService.AUTHORITY_UNAVAILABLE
    assert "RAW-PATIENT-IDENTIFIER-123" not in repr(entry.__dict__)
    assert "laboratory_result" not in repr(entry.__dict__)


async def test_verify_before_access_fails_closed_with_resource_reference() -> None:
    session = _AuditSession()
    service = ConsentEnforcementService(session)  # type: ignore[arg-type]

    result = await service.verify_consent_before_access(
        patient_id="RAW-PATIENT-IDENTIFIER-123",
        resource_type="observation",
        resource_id="RAW-RESOURCE-IDENTIFIER-456",
        requestor_id="account-1",
        purpose="TREATMENT",
    )

    assert result.granted is False
    assert result.reason == ConsentEnforcementService.AUTHORITY_UNAVAILABLE
    entry = session.entries[0]
    assert entry.target_type == "observation"
    assert "RAW-RESOURCE-IDENTIFIER-456" not in repr(entry.__dict__)


async def test_security_route_passes_canonical_consent_arguments(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    async def fake_check(self, **kwargs):
        del self
        captured.update(kwargs)
        return ConsentCheckResult(granted=False, reason="denied")

    monkeypatch.setattr(ConsentEnforcementService, "check_consent", fake_check)
    response = await security_routes.check_consent(
        data=security_routes.ConsentCheck(citizen_id="citizen-1", scope="lab"),
        current_user=SimpleNamespace(id="account-1"),
        db=_AuditSession(),  # type: ignore[arg-type]
    )

    assert response.granted is False
    assert captured["patient_id"] == "citizen-1"
    assert captured["requestor_id"] == "account-1"
    assert "citizen_id" not in captured


async def test_security_route_rejects_unauthenticated_actor() -> None:
    with pytest.raises(HTTPException) as exc:
        await security_routes.check_consent(
            data=security_routes.ConsentCheck(citizen_id="citizen-1", scope="lab"),
            current_user=SimpleNamespace(),
            db=_AuditSession(),  # type: ignore[arg-type]
        )
    assert exc.value.status_code == 401
