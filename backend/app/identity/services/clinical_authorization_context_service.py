from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.identity.models.account import Account
from app.identity.models.assignment import Assignment
from app.identity.models.identity import IdentityRecord
from app.identity.models.legacy_account_link import (
    LegacyAccountLink,
    LegacyAccountLinkSource,
    LegacyAccountLinkStatus,
)
from app.identity.services.audit_service import AuditService
from app.models.clinical_scope import ClinicalLabFacilityBinding
from app.models.organization import Facility, Organization
from app.models.tenant import Tenant
from app.services.clinical_scope_bridge_service import ClinicalScopeBridgeService


class ClinicalAuthorizationContextError(ValueError):
    """Base error for an unproven clinical authorization context."""


class ClinicalLegacyIdentityUnresolved(ClinicalAuthorizationContextError):
    pass


class ClinicalIdentityAssignmentMismatch(ClinicalAuthorizationContextError):
    pass


class ClinicalActiveAssignmentUnavailable(ClinicalAuthorizationContextError):
    pass


class ClinicalFacilityScopeMismatch(ClinicalAuthorizationContextError):
    pass


class ClinicalAuthorizationContextAmbiguous(ClinicalAuthorizationContextError):
    pass


@dataclass(frozen=True)
class ClinicalAuthorizationContext:
    """Server-derived context. It intentionally contains technical IDs only."""

    legacy_lab_user_id: int
    legacy_lab_id: int
    account_id: str
    identity_id: str
    person_id: str
    assignment_id: str
    facility_resource_id: int
    organization_resource_id: int
    tenant_id: int
    scope_mapping_version: int


class ClinicalAuthorizationContextService:
    """Prove account → person → assignment → facility for one legacy lab user.

    The service is read-only with respect to clinical resources. It does not add
    a facility to a token and does not authorize a clinical operation by itself.
    Callers must still check the exact clinical permission before loading a
    resource under the returned operational facility resource ID.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.audit = AuditService(session)
        self.scope_bridge = ClinicalScopeBridgeService(session)

    async def resolve_for_legacy_lab_user(
        self,
        *,
        legacy_lab_user_id: int,
        legacy_lab_id: int,
        expected_niam_organization_id: str | None = None,
        expected_niam_facility_id: str | None = None,
    ) -> ClinicalAuthorizationContext:
        if legacy_lab_user_id <= 0 or legacy_lab_id <= 0:
            raise ClinicalLegacyIdentityUnresolved("Legacy account and laboratory identifiers must be positive")

        try:
            link = await self._get_migrated_link(legacy_lab_user_id)
            account, identity = await self._get_active_account_identity(link.canonical_account_id)
            binding = await self.scope_bridge.resolve_active_binding(legacy_lab_id)
            if expected_niam_organization_id is not None and binding.niam_organization_id != expected_niam_organization_id:
                raise ClinicalFacilityScopeMismatch("The reviewed organization mapping does not match the active NIAM workspace")
            if expected_niam_facility_id is not None and binding.niam_facility_id != expected_niam_facility_id:
                raise ClinicalFacilityScopeMismatch("The reviewed facility mapping does not match the active NIAM workspace")
            if binding.niam_organization_id is None or binding.niam_facility_id is None:
                raise ClinicalFacilityScopeMismatch("The reviewed bridge has no canonical NIAM scope mapping")
            facility, organization, tenant = await self._get_active_operational_scope(binding)
            assignment = await self._get_matching_assignment(
                person_id=identity.person_id,
                facility_resource_id=facility.id,
                organization_resource_id=organization.id,
            )
            context = ClinicalAuthorizationContext(
                legacy_lab_user_id=legacy_lab_user_id,
                legacy_lab_id=legacy_lab_id,
                account_id=account.id,
                identity_id=identity.id,
                person_id=identity.person_id,
                assignment_id=assignment.id,
                facility_resource_id=facility.id,
                organization_resource_id=organization.id,
                tenant_id=tenant.id,
                scope_mapping_version=binding.mapping_version,
            )
        except ClinicalAuthorizationContextError as exc:
            await self._record_decision(
                action="clinical_authorization_context_denied",
                legacy_lab_user_id=legacy_lab_user_id,
                legacy_lab_id=legacy_lab_id,
                outcome="denied",
                failure_code=exc.__class__.__name__,
            )
            raise

        await self._record_decision(
            action="clinical_authorization_context_resolved",
            legacy_lab_user_id=legacy_lab_user_id,
            legacy_lab_id=legacy_lab_id,
            outcome="success",
            assignment_id=context.assignment_id,
            facility_resource_id=context.facility_resource_id,
            organization_resource_id=context.organization_resource_id,
            tenant_id=context.tenant_id,
            scope_mapping_version=context.scope_mapping_version,
        )
        return context

    async def _get_migrated_link(self, legacy_lab_user_id: int) -> LegacyAccountLink:
        stmt = select(LegacyAccountLink).where(
            LegacyAccountLink.source_kind == LegacyAccountLinkSource.lab_user.value,
            LegacyAccountLink.legacy_account_id == legacy_lab_user_id,
            LegacyAccountLink.status == LegacyAccountLinkStatus.migrated.value,
            LegacyAccountLink.canonical_account_id.isnot(None),
        )
        result = await self.session.execute(stmt)
        links = list(result.scalars().all())
        if not links:
            raise ClinicalLegacyIdentityUnresolved("No migrated canonical account link exists for this laboratory user")
        if len(links) != 1:
            raise ClinicalAuthorizationContextAmbiguous("More than one migrated canonical account link exists")
        return links[0]

    async def _get_active_account_identity(self, account_id: str | None) -> tuple[Account, IdentityRecord]:
        if not account_id:
            raise ClinicalLegacyIdentityUnresolved("The migrated legacy account link has no canonical account")
        stmt = (
            select(Account, IdentityRecord)
            .join(IdentityRecord, IdentityRecord.id == Account.identity_id)
            .where(
                Account.id == account_id,
                Account.status == "active",
                Account.is_active.is_(True),
                IdentityRecord.status == "active",
                IdentityRecord.is_active.is_(True),
            )
        )
        result = await self.session.execute(stmt)
        rows = list(result.all())
        if len(rows) != 1:
            raise ClinicalLegacyIdentityUnresolved("The canonical account and active identity could not be proven")
        return rows[0]

    async def _get_active_operational_scope(
        self,
        binding: ClinicalLabFacilityBinding,
    ) -> tuple[Facility, Organization, Tenant]:
        stmt = (
            select(Facility, Organization, Tenant)
            .join(Organization, Organization.id == Facility.organization_id)
            .join(Tenant, Tenant.id == Organization.tenant_id)
            .where(
                Facility.id == binding.facility_resource_id,
                Facility.is_active.is_(True),
                Organization.is_active.is_(True),
                Tenant.is_active.is_(True),
            )
        )
        result = await self.session.execute(stmt)
        rows = list(result.all())
        if len(rows) != 1:
            raise ClinicalFacilityScopeMismatch("The reviewed facility does not resolve to one active organization and tenant")
        return rows[0]

    async def _get_matching_assignment(
        self,
        *,
        person_id: str,
        facility_resource_id: int,
        organization_resource_id: int,
    ) -> Assignment:
        today = date.today()
        stmt = select(Assignment).where(
            Assignment.is_active.is_(True),
            Assignment.status == "active",
            Assignment.clinical_organization_resource_id.isnot(None),
            Assignment.clinical_facility_resource_id.isnot(None),
            Assignment.start_date <= today,
            (Assignment.end_date.is_(None) | (Assignment.end_date >= today)),
        )
        result = await self.session.execute(stmt)
        candidates = list(result.scalars().all())
        person_candidates = [assignment for assignment in candidates if assignment.person_id == person_id]
        if not person_candidates:
            if candidates:
                raise ClinicalIdentityAssignmentMismatch("No active clinical assignment belongs to the canonical identity person")
            raise ClinicalActiveAssignmentUnavailable("No active clinical assignment is available")

        scoped = [
            assignment
            for assignment in person_candidates
            if assignment.clinical_facility_resource_id == facility_resource_id
            and assignment.clinical_organization_resource_id == organization_resource_id
        ]
        if not scoped:
            raise ClinicalFacilityScopeMismatch("The active person assignment does not match the reviewed facility scope")
        if len(scoped) != 1:
            raise ClinicalAuthorizationContextAmbiguous("More than one active clinical assignment matches this scope")
        return scoped[0]

    async def _record_decision(
        self,
        *,
        action: str,
        legacy_lab_user_id: int,
        legacy_lab_id: int,
        outcome: str,
        **metadata: object,
    ) -> None:
        safe_metadata = {
            "legacy_lab_id": legacy_lab_id,
            **metadata,
        }
        await self.audit.record_event(
            action=action,
            target_type="legacy_lab_user",
            target_id=str(legacy_lab_user_id),
            metadata=safe_metadata,
            outcome=outcome,
        )
