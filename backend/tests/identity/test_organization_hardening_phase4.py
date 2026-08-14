"""Organization, facility and relationship hardening tests for IAM Phase 4."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from app.identity.models.administrative_structure import (
    OrganizationStatus,
    OwnershipStatus,
    RepresentativeStatus,
)
from app.identity.services.organization_service import (
    LEGAL_ORGANIZATION_TRANSITIONS,
    LEGAL_REPRESENTATIVE_TRANSITIONS,
    InvalidOrganizationTransition,
    OrganizationRelationshipService,
    OrganizationStateService,
    OrganizationVerificationProvider,
    OrganizationVerificationStatus,
)


def organization(status: str):
    return SimpleNamespace(status=status, is_active=False)


def representative(status: str):
    return SimpleNamespace(status=status)


def ownership(status: str):
    return SimpleNamespace(status=status)


def test_every_legal_organization_transition_has_expected_activation_semantics():
    for current, targets in LEGAL_ORGANIZATION_TRANSITIONS.items():
        for target in targets:
            item = organization(current)
            OrganizationStateService.transition(item, OrganizationStatus(target))
            assert item.status == target
            assert item.is_active is (target == OrganizationStatus.active.value)


def test_every_illegal_organization_transition_is_deny_by_default():
    statuses = list(OrganizationStatus)
    for current in statuses:
        legal = LEGAL_ORGANIZATION_TRANSITIONS[current.value]
        for target in statuses:
            if target.value in legal:
                continue
            item = organization(current.value)
            with pytest.raises(InvalidOrganizationTransition):
                OrganizationStateService.transition(item, target)
            assert item.status == current.value
            assert item.is_active is False


def test_activation_requires_pending_approval_and_never_auto_activates():
    for status in (
        OrganizationStatus.draft,
        OrganizationStatus.pending_verification,
        OrganizationStatus.active,
        OrganizationStatus.suspended,
    ):
        with pytest.raises(InvalidOrganizationTransition):
            OrganizationStateService.activate_after_approval(organization(status.value))

    item = organization(OrganizationStatus.pending_approval.value)
    OrganizationStateService.activate_after_approval(item)
    assert item.status == OrganizationStatus.active.value
    assert item.is_active is True


def test_every_illegal_representative_transition_is_rejected():
    statuses = list(RepresentativeStatus)
    for current in statuses:
        legal = LEGAL_REPRESENTATIVE_TRANSITIONS[current.value]
        for target in statuses:
            if target.value in legal:
                continue
            item = representative(current.value)
            with pytest.raises(InvalidOrganizationTransition):
                OrganizationRelationshipService.transition_representative(item, target)
            assert item.status == current.value


def test_ownership_activation_requires_pending_state():
    item = ownership(OwnershipStatus.pending.value)
    OrganizationRelationshipService.activate_ownership(item)
    assert item.status == OwnershipStatus.active.value

    for status in (OwnershipStatus.active, OwnershipStatus.ended, OwnershipStatus.revoked):
        with pytest.raises(InvalidOrganizationTransition):
            OrganizationRelationshipService.activate_ownership(ownership(status.value))


@pytest.mark.asyncio
async def test_organization_provider_boundary_never_claims_verification():
    result = await OrganizationVerificationProvider().verify("org-1", "opaque-reference")

    assert result.status == OrganizationVerificationStatus.not_connected
    assert result.provider == "organization:not-connected"
    assert result.provider_reference is None
