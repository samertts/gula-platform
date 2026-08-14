from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.identity.models.administrative_structure import (
    OrganizationOwnership,
    OrganizationRepresentative,
    OrganizationStatus,
    OwnershipStatus,
    RepresentativeStatus,
)


class OrganizationVerificationStatus(StrEnum):
    not_connected = "not_connected"
    pending = "pending"
    verified = "verified"
    failed = "failed"
    expired = "expired"
    revoked = "revoked"
    requires_review = "requires_review"


@dataclass(frozen=True)
class OrganizationVerificationResult:
    status: OrganizationVerificationStatus
    provider: str
    provider_reference: str | None = None
    reason: str | None = None


class OrganizationVerificationProvider:
    connected = False
    name = "organization:not-connected"

    async def verify(self, organization_id: str, reference: str | None = None) -> OrganizationVerificationResult:
        return OrganizationVerificationResult(
            status=OrganizationVerificationStatus.not_connected,
            provider=self.name,
            reason="No organization verification provider is connected",
        )


LEGAL_ORGANIZATION_TRANSITIONS: dict[str, frozenset[str]] = {
    OrganizationStatus.draft.value: frozenset({OrganizationStatus.pending_verification.value}),
    OrganizationStatus.pending_verification.value: frozenset({
        OrganizationStatus.pending_approval.value,
        OrganizationStatus.rejected.value,
    }),
    OrganizationStatus.pending_approval.value: frozenset({
        OrganizationStatus.active.value,
        OrganizationStatus.rejected.value,
    }),
    OrganizationStatus.active.value: frozenset({
        OrganizationStatus.suspended.value,
        OrganizationStatus.deactivated.value,
    }),
    OrganizationStatus.suspended.value: frozenset({OrganizationStatus.active.value, OrganizationStatus.deactivated.value}),
    OrganizationStatus.rejected.value: frozenset({OrganizationStatus.draft.value}),
    OrganizationStatus.deactivated.value: frozenset({OrganizationStatus.archived.value}),
    OrganizationStatus.archived.value: frozenset(),
}


class InvalidOrganizationTransition(ValueError):
    """Raised when organization state changes outside the administrative workflow."""


class OrganizationStateService:
    @staticmethod
    def transition(organization, target: OrganizationStatus):
        current = str(organization.status)
        target_value = target.value
        if target_value not in LEGAL_ORGANIZATION_TRANSITIONS.get(current, frozenset()):
            raise InvalidOrganizationTransition(f"Illegal organization transition: {current} -> {target_value}")
        organization.status = target_value
        organization.is_active = target == OrganizationStatus.active
        return organization

    @staticmethod
    def activate_after_approval(organization):
        if str(organization.status) != OrganizationStatus.pending_approval.value:
            raise InvalidOrganizationTransition("Only pending_approval organizations can be activated")
        return OrganizationStateService.transition(organization, OrganizationStatus.active)


LEGAL_REPRESENTATIVE_TRANSITIONS: dict[str, frozenset[str]] = {
    RepresentativeStatus.pending.value: frozenset({RepresentativeStatus.active.value, RepresentativeStatus.revoked.value}),
    RepresentativeStatus.active.value: frozenset({RepresentativeStatus.suspended.value, RepresentativeStatus.expired.value, RepresentativeStatus.revoked.value}),
    RepresentativeStatus.suspended.value: frozenset({RepresentativeStatus.active.value, RepresentativeStatus.revoked.value}),
    RepresentativeStatus.expired.value: frozenset({RepresentativeStatus.revoked.value}),
    RepresentativeStatus.revoked.value: frozenset(),
}


class OrganizationRelationshipService:
    @staticmethod
    def transition_representative(representative: OrganizationRepresentative, target: RepresentativeStatus):
        current = str(representative.status)
        if target.value not in LEGAL_REPRESENTATIVE_TRANSITIONS.get(current, frozenset()):
            raise InvalidOrganizationTransition(f"Illegal representative transition: {current} -> {target.value}")
        representative.status = target.value
        return representative

    @staticmethod
    def activate_ownership(ownership: OrganizationOwnership):
        if str(ownership.status) != OwnershipStatus.pending.value:
            raise InvalidOrganizationTransition("Only pending ownership can be activated")
        ownership.status = OwnershipStatus.active.value
        return ownership
