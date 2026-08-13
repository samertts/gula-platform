from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.identity.services.audit_service import AuditService
from app.models.clinical_scope import (
    ClinicalEhrFacilityBinding,
    ClinicalEhrFacilityBindingStatus,
    ClinicalLabFacilityBinding,
    ClinicalLabFacilityBindingStatus,
)
from app.models.organization import Facility, Organization


class ClinicalScopeBridgeError(ValueError):
    """Base failure for a clinical scope bridge that cannot be proven."""


class ClinicalFacilityScopeUnavailable(ClinicalScopeBridgeError):
    """Raised when no reviewed, active binding can establish the facility scope."""


class ClinicalFacilityScopeAmbiguous(ClinicalScopeBridgeError):
    """Raised when a lab has more than one simultaneously active facility binding."""


class ClinicalScopeBridgeService:
    """Resolve reviewed laboratory-to-facility scope without any implicit ID conversion."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.audit = AuditService(session)

    async def create_pending_binding(
        self,
        *,
        legacy_lab_id: int,
        facility_resource_id: int,
        actor_id: str | None,
    ) -> ClinicalLabFacilityBinding:
        if legacy_lab_id <= 0 or facility_resource_id <= 0:
            raise ValueError("Legacy lab and facility resource identifiers must be positive")
        binding = ClinicalLabFacilityBinding(
            legacy_lab_id=legacy_lab_id,
            facility_resource_id=facility_resource_id,
            status=ClinicalLabFacilityBindingStatus.pending.value,
            mapping_version=1,
        )
        self.session.add(binding)
        await self.session.flush()
        await self.audit.record_event(
            action="clinical_lab_facility_binding_created",
            actor_id=actor_id,
            target_type="clinical_lab_facility_binding",
            target_id=binding.id,
            metadata={"mapping_version": binding.mapping_version},
        )
        return binding

    async def transition(
        self,
        binding: ClinicalLabFacilityBinding,
        target: ClinicalLabFacilityBindingStatus | str,
        *,
        actor_id: str | None,
        reason: str | None = None,
    ) -> ClinicalLabFacilityBinding:
        previous_status = binding.status
        binding.transition(target, reason=reason)
        await self.session.flush()
        await self.audit.record_event(
            action="clinical_lab_facility_binding_transition",
            actor_id=actor_id,
            target_type="clinical_lab_facility_binding",
            target_id=binding.id,
            metadata={
                "from_status": previous_status,
                "to_status": binding.status,
                "mapping_version": binding.mapping_version,
                "reason_present": bool((reason or "").strip()),
            },
        )
        return binding

    async def resolve_active_binding(self, legacy_lab_id: int) -> ClinicalLabFacilityBinding:
        """Return exactly one active binding with an active facility and organization.

        The query joins internal resources by their foreign keys, so a caller never
        treats legacy lab IDs and external facility labels as interchangeable.
        """

        if legacy_lab_id <= 0:
            raise ClinicalFacilityScopeUnavailable("Legacy lab identifier must be positive")
        stmt = (
            select(ClinicalLabFacilityBinding)
            .join(Facility, Facility.id == ClinicalLabFacilityBinding.facility_resource_id)
            .join(Organization, Organization.id == Facility.organization_id)
            .where(
                ClinicalLabFacilityBinding.legacy_lab_id == legacy_lab_id,
                ClinicalLabFacilityBinding.status == ClinicalLabFacilityBindingStatus.active.value,
                Facility.is_active.is_(True),
                Organization.is_active.is_(True),
            )
        )
        result = await self.session.execute(stmt)
        bindings = list(result.scalars().all())
        if not bindings:
            raise ClinicalFacilityScopeUnavailable("No active reviewed facility scope exists for this lab")
        if len(bindings) != 1:
            raise ClinicalFacilityScopeAmbiguous("More than one active facility scope exists for this lab")
        return bindings[0]


class ClinicalEhrFacilityScopeBridgeService:
    """Resolve a reviewed national-EHR-facility to NIAM-facility bridge."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.audit = AuditService(session)

    async def create_pending_binding(
        self,
        *,
        national_facility_id: str,
        facility_resource_id: int,
        actor_id: str | None,
    ) -> ClinicalEhrFacilityBinding:
        if not national_facility_id.strip() or len(national_facility_id) > 26:
            raise ValueError("National EHR facility identifier must be a non-empty 26-character identifier")
        if facility_resource_id <= 0:
            raise ValueError("Facility resource identifier must be positive")
        binding = ClinicalEhrFacilityBinding(
            national_facility_id=national_facility_id,
            facility_resource_id=facility_resource_id,
            status=ClinicalEhrFacilityBindingStatus.pending.value,
            mapping_version=1,
        )
        self.session.add(binding)
        await self.session.flush()
        await self.audit.record_event(
            action="clinical_ehr_facility_binding_created",
            actor_id=actor_id,
            target_type="clinical_ehr_facility_binding",
            target_id=binding.id,
            metadata={"mapping_version": binding.mapping_version},
        )
        return binding

    async def transition(
        self,
        binding: ClinicalEhrFacilityBinding,
        target: ClinicalEhrFacilityBindingStatus | str,
        *,
        actor_id: str | None,
        reason: str | None = None,
    ) -> ClinicalEhrFacilityBinding:
        previous_status = binding.status
        binding.transition(target, reason=reason)
        await self.session.flush()
        await self.audit.record_event(
            action="clinical_ehr_facility_binding_transition",
            actor_id=actor_id,
            target_type="clinical_ehr_facility_binding",
            target_id=binding.id,
            metadata={
                "from_status": previous_status,
                "to_status": binding.status,
                "mapping_version": binding.mapping_version,
                "reason_present": bool((reason or "").strip()),
            },
        )
        return binding

    async def resolve_active_binding(self, national_facility_id: str) -> ClinicalEhrFacilityBinding:
        """Return exactly one active bridge with an active NIAM facility and organization."""

        if not national_facility_id.strip():
            raise ClinicalFacilityScopeUnavailable("National EHR facility identifier is required")
        stmt = (
            select(ClinicalEhrFacilityBinding)
            .join(Facility, Facility.id == ClinicalEhrFacilityBinding.facility_resource_id)
            .join(Organization, Organization.id == Facility.organization_id)
            .where(
                ClinicalEhrFacilityBinding.national_facility_id == national_facility_id,
                ClinicalEhrFacilityBinding.status == ClinicalEhrFacilityBindingStatus.active.value,
                Facility.is_active.is_(True),
                Organization.is_active.is_(True),
            )
        )
        result = await self.session.execute(stmt)
        bindings = list(result.scalars().all())
        if not bindings:
            raise ClinicalFacilityScopeUnavailable("No active reviewed NIAM scope exists for this EHR facility")
        if len(bindings) != 1:
            raise ClinicalFacilityScopeAmbiguous("More than one active NIAM scope exists for this EHR facility")
        return bindings[0]
