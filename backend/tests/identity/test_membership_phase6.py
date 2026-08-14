from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.identity.models.membership import (
    Membership,
    MembershipApplication,
    MembershipApplicationStatus,
    MembershipScopeType,
    MembershipStatus,
)
from app.identity.services.membership_service import (
    LEGAL_APPLICATION_TRANSITIONS,
    LEGAL_MEMBERSHIP_TRANSITIONS,
    MembershipAccessDenied,
    MembershipService,
    MembershipStateError,
)


def test_membership_transition_matrix_allows_only_declared_edges() -> None:
    for current, targets in LEGAL_MEMBERSHIP_TRANSITIONS.items():
        for target in targets:
            membership = Membership(status=current, version=1, is_active=True)
            MembershipService.transition_membership(membership, MembershipStatus(target))
            assert membership.status == target
            assert membership.version == 2

        if not targets:
            membership = Membership(status=current, version=1, is_active=True)
            with pytest.raises(MembershipStateError):
                MembershipService.transition_membership(membership, MembershipStatus.active)


def test_membership_transition_rejects_escalation_from_revoked() -> None:
    membership = Membership(status=MembershipStatus.revoked.value, version=4, is_active=False)
    with pytest.raises(MembershipStateError):
        MembershipService.transition_membership(membership, MembershipStatus.active)
    assert membership.version == 4
    assert membership.status == MembershipStatus.revoked.value


def test_application_transition_matrix_rejects_approval_without_review() -> None:
    application = MembershipApplication(status=MembershipApplicationStatus.submitted.value, version=1)
    with pytest.raises(MembershipStateError):
        MembershipService.transition_application(application, MembershipApplicationStatus.approved)
    assert application.status == MembershipApplicationStatus.submitted.value


def test_application_transition_matrix_contains_no_implicit_auto_activation() -> None:
    assert MembershipApplicationStatus.approved.value not in LEGAL_APPLICATION_TRANSITIONS[MembershipApplicationStatus.submitted.value]
    assert MembershipApplicationStatus.approved.value in LEGAL_APPLICATION_TRANSITIONS[MembershipApplicationStatus.under_review.value]


def test_relationship_key_is_deterministic_and_scope_specific() -> None:
    first = MembershipService.relationship_key("acct", "org", "employee", MembershipScopeType.facility.value, facility_id="fac")
    second = MembershipService.relationship_key("acct", "org", "employee", MembershipScopeType.facility.value, facility_id="fac")
    other_scope = MembershipService.relationship_key("acct", "org", "employee", MembershipScopeType.facility.value, facility_id="other")
    assert first == second
    assert first != other_scope


def test_invitation_token_hash_is_one_way_and_stable() -> None:
    token = "test-token-value"
    assert MembershipService.token_hash(token) == MembershipService.token_hash(token)
    assert MembershipService.token_hash(token) != token


@pytest.mark.asyncio
async def test_application_cannot_be_submitted_for_another_account() -> None:
    service = MembershipService(SimpleNamespace())
    with pytest.raises(MembershipAccessDenied):
        await service.create_application(
            account_id="target-account",
            identity_id="identity",
            organization_id="organization",
            relationship_type="employee",
            scope_type="organization",
            actor_id="different-actor",
        )


@pytest.mark.asyncio
async def test_application_provisioning_is_idempotent_for_same_context() -> None:
    account = SimpleNamespace(id="account", status="active", is_active=True, identity_id="identity")
    organization = SimpleNamespace(id="organization", status="active", is_active=True)
    existing = None
    session = SimpleNamespace()
    session.execute = AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: account))
    session.scalar = AsyncMock(side_effect=[organization, existing])
    session.add = lambda item: None
    session.flush = AsyncMock()
    service = MembershipService(session)
    service._audit = AsyncMock()

    first = await service.create_application(
        account_id="account",
        identity_id="identity",
        organization_id="organization",
        relationship_type="employee",
        scope_type="organization",
        actor_id="account",
    )

    session.scalar = AsyncMock(side_effect=[organization, first])
    second = await service.create_application(
        account_id="account",
        identity_id="identity",
        organization_id="organization",
        relationship_type="employee",
        scope_type="organization",
        actor_id="account",
    )
    assert second is first
    assert service._audit.await_count == 1


def test_membership_serialization_does_not_include_invitation_secret() -> None:
    membership = Membership(
        id="membership",
        uuid="uuid",
        account_id="account",
        organization_id="organization",
        relationship_type="employee",
        scope_type="organization",
        status=MembershipStatus.active.value,
        source="application",
        version=1,
        is_active=True,
    )
    assert "token" not in membership.to_dict()
    assert "password" not in membership.to_dict()
