from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from app.identity.models.audit import IdentityAuditEntry
from app.national.api.routes import security as security_routes
from app.national.security.break_glass import BreakGlassReason, BreakGlassService


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
            entry.id = f"BRK{self._counter:023d}"[:26]
            entry.uuid = f"uuid-brk-{self._counter}"
            self.entries.append(entry)

    async def flush(self) -> None:
        return None


def _request_access(*, duration_minutes: int = 60, service: BreakGlassService | None = None):
    return (service or BreakGlassService()).request_access(
        user_id="account-1",
        user_name="Actor",
        user_role="doctor",
        reason=BreakGlassReason.EMERGENCY,
        reason_detail="Patient safety",
        resource_type="citizen",
        resource_id="citizen-1",
        patient_id="citizen-1",
        duration_minutes=duration_minutes,
    )


def test_break_glass_access_is_bounded_by_duration() -> None:
    service = BreakGlassService()
    before = datetime.now(UTC)
    access = _request_access(duration_minutes=15, service=service)
    after = datetime.now(UTC)

    assert access.expires_at is not None
    assert before + timedelta(minutes=15) <= access.expires_at <= after + timedelta(minutes=15)
    assert service.is_access_valid(access.access_id) is True


def test_expired_break_glass_access_is_invalid() -> None:
    service = BreakGlassService()
    access = service.request_access(
        user_id="account-1",
        user_name="Actor",
        user_role="doctor",
        reason=BreakGlassReason.EMERGENCY,
        reason_detail="Patient safety",
        resource_type="citizen",
        resource_id="citizen-1",
        patient_id="citizen-1",
        duration_minutes=1,
    )
    access.expires_at = datetime.now(UTC) - timedelta(seconds=1)

    assert service.is_access_valid(access.access_id) is False
    assert access.is_active is False


@pytest.mark.parametrize("duration_minutes", [0, -1, BreakGlassService.MAX_DURATION_MINUTES + 1])
def test_break_glass_duration_is_validated(duration_minutes: int) -> None:
    with pytest.raises(ValueError):
        _request_access(duration_minutes=duration_minutes)


async def test_break_glass_route_denies_and_audits_without_raw_reference() -> None:
    session = _AuditSession()

    response = await security_routes.request_break_glass(
        data=security_routes.BreakGlassRequest(
            citizen_id="RAW-CITIZEN-123",
            reason="RAW REASON WITH IDENTIFIER",
            duration_minutes=60,
        ),
        current_user=SimpleNamespace(id="account-1"),
        db=session,  # type: ignore[arg-type]
    )

    assert response.granted is False
    assert response.access_id is None
    assert response.reason == security_routes.BREAK_GLASS_AUTHORITY_UNAVAILABLE
    assert len(session.entries) == 1
    entry = session.entries[0]
    assert entry.event_version == "2"
    assert entry.decision == "DENY"
    assert entry.reason_code == security_routes.BREAK_GLASS_AUTHORITY_UNAVAILABLE
    assert "RAW-CITIZEN-123" not in repr(entry.__dict__)
    assert "RAW REASON WITH IDENTIFIER" not in repr(entry.__dict__)


async def test_break_glass_route_requires_authenticated_actor() -> None:
    with pytest.raises(Exception) as exc:
        await security_routes.request_break_glass(
            data=security_routes.BreakGlassRequest(citizen_id="citizen-1", reason="test"),
            current_user=SimpleNamespace(),
            db=_AuditSession(),  # type: ignore[arg-type]
        )
    assert getattr(exc.value, "status_code", None) == 401
