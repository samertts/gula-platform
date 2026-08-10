"""A4 — National professional authorization (separable privilege layer).

The registry entry (identity) is separable from the authorization (privilege).
Authorizations are issued ONLY from verified, non-expired entries; they carry
scope (national/directorate/facility), expiry and an independent lifecycle
(active/suspended/revoked); and registry-level suspension/revocation
invalidates derived authorizations.
"""

from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from app._compat import UTC
from app.identity.models.audit import AuditAction
from app.identity.professional_registry import (
    AuthorizationError,
    AuthorizationScopeType,
    AuthorizationStatus,
    ProfessionalAuthorizationService,
    ScopeError,
    scope_matches,
    validate_scope,
)

NOW = datetime(2026, 8, 10, tzinfo=UTC)
LATER = NOW + timedelta(days=30)
PAST = NOW - timedelta(days=1)


def entry(**overrides):
    base = {
        "id": "REG0001",
        "registry_id": "REG-0001",
        "person_id": "P1",
        "profession": "doctor",
        "verified": True,
        "status": "verified",
        "expires_at": date(2030, 1, 1),
    }
    base.update(overrides)
    return MagicMock(**base)


def auth(**overrides):
    base = {
        "id": "AUTH0001",
        "authorization_id": "AUTH-0001",
        "registry_id": "REG0001",
        "person_id": "P1",
        "profession": "doctor",
        "scope_type": "facility",
        "scope_id": "ORG-1",
        "status": "active",
        "status_reason": None,
        "granted_at": NOW,
        "granted_by": "verifier-1",
        "expires_at": LATER,
        "is_active": True,
    }
    base.update(overrides)
    return MagicMock(**base)


class TestScope:
    def test_national_scope_needs_no_id(self):
        validate_scope("national", None)

    def test_facility_scope_requires_id(self):
        with pytest.raises(ScopeError):
            validate_scope("facility", None)

    def test_invalid_scope_type_rejected(self):
        with pytest.raises(ScopeError):
            validate_scope("province", "ORG-1")

    def test_national_matches_any_jurisdiction(self):
        assert scope_matches("national", None, "facility", "ORG-1")
        assert scope_matches("national", None, "national", None)

    def test_requested_national_matches_facility_auth(self):
        assert scope_matches("facility", "ORG-1", "national", None)

    def test_facility_scope_requires_exact_id(self):
        assert scope_matches("facility", "ORG-1", "facility", "ORG-1")
        assert not scope_matches("facility", "ORG-1", "facility", "ORG-2")


class TestIssue:
    async def test_issue_from_verified_entry(self):
        session = MagicMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        audit = AsyncMock()
        audit.record = AsyncMock()
        svc = ProfessionalAuthorizationService(session, audit=audit)
        result = await svc.issue(
            entry(),
            scope_type="facility",
            scope_id="ORG-1",
            granted_by="verifier-1",
            expires_at=LATER,
        )
        assert result.authorization_id.startswith("AUTH-")
        assert result.status == "active"
        assert result.scope_type == "facility"
        session.add.assert_called_once()
        audit.record.assert_awaited_once()
        assert audit.record.await_args.args[0] is AuditAction.authorization_issued

    async def test_issue_rejects_unverified_entry(self):
        svc = ProfessionalAuthorizationService(MagicMock())
        with pytest.raises(AuthorizationError) as excinfo:
            await svc.issue(
                entry(verified=False, status="pending"),
                granted_by="verifier-1",
            )
        assert "not_verified" in str(excinfo.value)

    async def test_issue_rejects_expired_entry(self):
        svc = ProfessionalAuthorizationService(MagicMock())
        with pytest.raises(AuthorizationError) as excinfo:
            await svc.issue(
                entry(expires_at=date(2020, 1, 1)),
                granted_by="verifier-1",
            )
        assert "entry_expired" in str(excinfo.value)

    async def test_issue_rejects_suspended_entry(self):
        svc = ProfessionalAuthorizationService(MagicMock())
        with pytest.raises(AuthorizationError):
            await svc.issue(entry(status="suspended"), granted_by="verifier-1")

    async def test_issue_rejects_missing_scope_id(self):
        svc = ProfessionalAuthorizationService(MagicMock())
        with pytest.raises(ScopeError):
            await svc.issue(entry(), scope_type="directorate", granted_by="verifier-1")


class TestLifecycle:
    async def test_renew_updates_expiry(self):
        session = MagicMock()
        session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: auth()))
        session.flush = AsyncMock()
        audit = AsyncMock()
        audit.record = AsyncMock()
        svc = ProfessionalAuthorizationService(session, audit=audit)
        result = await svc.renew(
            "AUTH-0001",
            granted_by="verifier-1",
            expires_at=LATER + timedelta(days=365),
        )
        assert result.expires_at == LATER + timedelta(days=365)
        audit.record.assert_awaited_once()
        assert audit.record.await_args.args[0] is AuditAction.authorization_renewed

    async def test_renew_rejects_unknown(self):
        session = MagicMock()
        session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: None))
        svc = ProfessionalAuthorizationService(session)
        with pytest.raises(AuthorizationError):
            await svc.renew("NOPE", granted_by="v", expires_at=LATER)

    async def test_suspend_sets_status_and_audits(self):
        session = MagicMock()
        session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: auth()))
        session.flush = AsyncMock()
        audit = AsyncMock()
        audit.record = AsyncMock()
        svc = ProfessionalAuthorizationService(session, audit=audit)
        result = await svc.suspend("AUTH-0001", reason="misconduct", actor="reviewer")
        assert result.status == "suspended"
        assert result.status_reason == "misconduct"
        assert audit.record.await_args.args[0] is AuditAction.authorization_suspended

    async def test_revoke_deactivates_and_audits(self):
        session = MagicMock()
        session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: auth()))
        session.flush = AsyncMock()
        audit = AsyncMock()
        audit.record = AsyncMock()
        svc = ProfessionalAuthorizationService(session, audit=audit)
        result = await svc.revoke("AUTH-0001", reason="fraud", actor="reviewer")
        assert result.status == "revoked"
        assert result.is_active is False
        assert audit.record.await_args.args[0] is AuditAction.authorization_revoked


class TestEnforcement:
    def make_svc(self, authorizations, privileged=True):
        registry = MagicMock()
        registry.is_privileged = AsyncMock(return_value=privileged)
        session = MagicMock()
        session.execute = AsyncMock(
            return_value=MagicMock(
                scalars=MagicMock(return_value=MagicMock(all=lambda: authorizations))
            )
        )
        return ProfessionalAuthorizationService(session, registry=registry)

    async def test_authorized_with_matching_scope(self):
        svc = self.make_svc([auth(scope_type="facility", scope_id="ORG-1")])
        assert (
            await svc.is_authorized("P1", "doctor", scope_type="facility", scope_id="ORG-1") is True
        )

    async def test_denied_on_scope_mismatch(self):
        svc = self.make_svc([auth(scope_type="facility", scope_id="ORG-1")])
        assert (
            await svc.is_authorized("P1", "doctor", scope_type="facility", scope_id="ORG-2")
            is False
        )

    async def test_denied_when_registry_no_longer_privileged(self):
        svc = self.make_svc([auth()], privileged=False)
        assert (
            await svc.is_authorized("P1", "doctor", scope_type="facility", scope_id="ORG-1")
            is False
        )

    async def test_denied_when_authorization_expired(self):
        svc = self.make_svc([auth(expires_at=PAST)])
        assert (
            await svc.is_authorized("P1", "doctor", scope_type="facility", scope_id="ORG-1")
            is False
        )

    async def test_denied_when_authorization_suspended(self):
        svc = self.make_svc([auth(status="suspended")])
        assert (
            await svc.is_authorized("P1", "doctor", scope_type="facility", scope_id="ORG-1")
            is False
        )

    async def test_national_authorization_matches_any_facility(self):
        svc = self.make_svc([auth(scope_type="national", scope_id=None)])
        assert (
            await svc.is_authorized("P1", "doctor", scope_type="facility", scope_id="ORG-99")
            is True
        )

    async def test_profession_must_match(self):
        svc = self.make_svc([auth(profession="doctor")])
        assert (
            await svc.is_authorized("P1", "nurse", scope_type="facility", scope_id="ORG-1") is False
        )

    async def test_matching_authorization_returns_row(self):
        target = auth(scope_type="facility", scope_id="ORG-1")
        svc = self.make_svc([auth(scope_type="facility", scope_id="ORG-9"), target])
        found = await svc.matching_authorization(
            "P1", "doctor", scope_type="facility", scope_id="ORG-1"
        )
        assert found is target


class TestRegistrySync:
    def make_svc(self, authorizations):
        session = MagicMock()
        session.execute = AsyncMock(
            return_value=MagicMock(
                scalars=MagicMock(return_value=MagicMock(all=lambda: authorizations))
            )
        )
        session.flush = AsyncMock()
        return ProfessionalAuthorizationService(session)

    async def test_registry_suspension_suspends_derived(self):
        first = auth()
        svc = self.make_svc([first])
        n = await svc.sync_status_from_registry(entry(status="suspended"))
        assert n == 1
        assert first.status == "suspended"
        assert first.status_reason == "registry_suspended"

    async def test_registry_revocation_revokes_derived(self):
        first = auth()
        svc = self.make_svc([first])
        await svc.sync_status_from_registry(entry(status="revoked"))
        assert first.status == "revoked"
        assert first.status_reason == "registry_revoked"

    async def test_registry_verified_does_not_reactivate(self):
        first = auth(status="suspended")
        svc = self.make_svc([first])
        await svc.sync_status_from_registry(entry(status="verified"))
        assert first.status == "suspended"

    async def test_no_rows_returns_zero(self):
        svc = self.make_svc([])
        assert await svc.sync_status_from_registry(entry(status="revoked")) == 0
