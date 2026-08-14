from types import SimpleNamespace

import pytest
from app.identity.models.administrative_structure import (
    OrganizationStatus,
    OwnershipStatus,
    RepresentativeStatus,
)
from app.identity.services.organization_service import (
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


def test_organization_requires_verification_and_approval_before_activation():
    item = organization(OrganizationStatus.draft.value)
    OrganizationStateService.transition(item, OrganizationStatus.pending_verification)
    OrganizationStateService.transition(item, OrganizationStatus.pending_approval)
    OrganizationStateService.activate_after_approval(item)
    assert item.status == OrganizationStatus.active.value
    assert item.is_active is True


def test_organization_cannot_activate_from_draft():
    with pytest.raises(InvalidOrganizationTransition):
        OrganizationStateService.activate_after_approval(organization(OrganizationStatus.draft.value))


def test_organization_status_cannot_skip_approval_or_reactivate_archived():
    item = organization(OrganizationStatus.pending_verification.value)
    with pytest.raises(InvalidOrganizationTransition):
        OrganizationStateService.transition(item, OrganizationStatus.active)
    with pytest.raises(InvalidOrganizationTransition):
        OrganizationStateService.transition(organization(OrganizationStatus.archived.value), OrganizationStatus.active)


def test_representative_state_machine_is_independent_from_authorization():
    item = representative(RepresentativeStatus.pending.value)
    OrganizationRelationshipService.transition_representative(item, RepresentativeStatus.active)
    OrganizationRelationshipService.transition_representative(item, RepresentativeStatus.suspended)
    assert item.status == RepresentativeStatus.suspended.value


def test_revoked_representative_cannot_be_reactivated():
    with pytest.raises(InvalidOrganizationTransition):
        OrganizationRelationshipService.transition_representative(
            representative(RepresentativeStatus.revoked.value),
            RepresentativeStatus.active,
        )


def test_ownership_requires_explicit_pending_to_active_transition():
    item = ownership(OwnershipStatus.pending.value)
    OrganizationRelationshipService.activate_ownership(item)
    assert item.status == OwnershipStatus.active.value
    with pytest.raises(InvalidOrganizationTransition):
        OrganizationRelationshipService.activate_ownership(item)


@pytest.mark.asyncio
async def test_unconnected_organization_provider_never_approves():
    result = await OrganizationVerificationProvider().verify("org-1", "opaque-reference")
    assert result.status == OrganizationVerificationStatus.not_connected
    assert result.provider == "organization:not-connected"
