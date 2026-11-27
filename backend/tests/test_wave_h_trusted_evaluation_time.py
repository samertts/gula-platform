from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.identity.models.account import Account, AccountStatus
from app.identity.models.consent import NiamConsent, NiamConsentStatus
from app.identity.models.membership import Membership, MembershipStatus
from app.identity.models.session import UserSession
from app.identity.services.authorization_decision import (
    AuthorizationActor,
    AuthorizationDecisionService,
    AuthorizationReason,
    AuthorizationRequest,
)
from app.identity.services.canonical_audit import CanonicalAuditService
from app.identity.services.consent_service_v2 import NiamConsentService


class _Result:
    def __init__(self, values: list[object] | None = None, scalar: object | None = None) -> None:
        self.values = values or []
        self.scalar_value = scalar

    def scalars(self) -> _Result:
        return self

    def all(self) -> list[object]:
        return self.values

    def scalar_one_or_none(self) -> object | None:
        return self.scalar_value


class _DecisionDb:
    def __init__(self, *, membership: Membership) -> None:
        self.membership = membership

    async def execute(self, statement):
        sql = str(statement)
        if "niam_memberships" in sql:
            return _Result([self.membership])
        if "niam_role_assignments" in sql:
            return _Result(["record.read"])
        if "niam_audit_entries" in sql:
            return _Result()
        return _Result()

    async def scalar(self, statement):
        del statement
        return "permission-id"

    def add(self, entry) -> None:
        del entry

    async def flush(self) -> None:
        return None


def _trusted_now() -> datetime:
    return datetime.now(UTC) - timedelta(hours=2)


def _actor(session_expires_at: datetime) -> AuthorizationActor:
    return AuthorizationActor(
        account=Account(
            id="account-1",
            identity_id="identity-1",
            status=AccountStatus.active.value,
            is_active=True,
            is_locked=False,
        ),
        session=UserSession(
            id="session-1",
            account_id="account-1",
            is_active=True,
            expires_at=session_expires_at,
            started_at=session_expires_at - timedelta(minutes=30),
            mfa_used=True,
        ),
    )


def _request() -> AuthorizationRequest:
    return AuthorizationRequest(
        subject_account_id="account-1",
        action="read",
        resource_type="record",
        resource_id="resource-1",
        organization_id="org-1",
        resource_context={"exists": True, "organization_id": "org-1"},
    )


async def test_wall_clock_still_rejects_an_expired_session() -> None:
    trusted_now = _trusted_now()
    membership = Membership(
        id="membership-1",
        account_id="account-1",
        organization_id="org-1",
        status=MembershipStatus.active.value,
        is_active=True,
        expires_at=trusted_now + timedelta(hours=1),
    )
    service = AuthorizationDecisionService(_DecisionDb(membership=membership))  # type: ignore[arg-type]

    decision = await service.authorize(_actor(trusted_now + timedelta(hours=1)), _request())

    assert decision.allowed is False
    assert decision.reason_code is AuthorizationReason.session_invalid


async def test_trusted_evaluation_time_allows_the_same_chain() -> None:
    trusted_now = _trusted_now()
    membership = Membership(
        id="membership-1",
        account_id="account-1",
        organization_id="org-1",
        status=MembershipStatus.active.value,
        is_active=True,
        expires_at=trusted_now + timedelta(hours=1),
    )
    service = AuthorizationDecisionService(_DecisionDb(membership=membership))  # type: ignore[arg-type]

    decision = await service.authorize(
        _actor(trusted_now + timedelta(hours=1)),
        _request(),
        now=trusted_now + timedelta(minutes=30),
    )

    assert decision.allowed is True


class _ConsentDb:
    def __init__(self, consent: NiamConsent) -> None:
        self.consent = consent

    async def get(self, model, identifier):
        del model, identifier
        return self.consent

    async def flush(self) -> None:
        return None


def _consent(expires_at: datetime) -> NiamConsent:
    return NiamConsent(
        id="CONSENT-1",
        uuid="uuid-consent-1",
        subject_account_id="citizen-1",
        grantee_account_id="account-1",
        purpose="TREATMENT",
        scope={"resource_domain": "patient_record", "actions": ["read"]},
        resource_domain="patient_record",
        status=NiamConsentStatus.active.value,
        is_active=True,
        granted_at=expires_at - timedelta(hours=1),
        expires_at=expires_at,
        version=1,
        source="user_portal",
    )


async def test_consent_check_uses_trusted_evaluation_time(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _no_audit(*args, **kwargs):
        del args, kwargs
        return

    async def _organization(self, actor_account_id: str) -> str:
        del self, actor_account_id
        return "org-1"

    monkeypatch.setattr(CanonicalAuditService, "record", _no_audit)
    monkeypatch.setattr(NiamConsentService, "_organization_for_account", _organization)
    trusted_now = _trusted_now()
    consent = _consent(trusted_now + timedelta(hours=1))
    service = NiamConsentService(_ConsentDb(consent))  # type: ignore[arg-type]

    result = await service.check(
        actor_account_id="account-1",
        consent_id=consent.id,
        now=trusted_now + timedelta(minutes=30),
    )

    assert result is consent
    assert consent.status == NiamConsentStatus.active.value
