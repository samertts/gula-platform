from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app._compat import UTC
from app.clinical_gateway.session_facade import SyncSessionAsyncFacade
from app.identity.api.workspaces import NiamActor
from app.identity.models.administrative_structure import NIAMAdminFacility
from app.identity.models.legacy_account_link import (
    LegacyAccountLink,
    LegacyAccountLinkSource,
    LegacyAccountLinkStatus,
)
from app.identity.models.membership import Membership, MembershipStatus
from app.identity.models.niam_organization import NIAMOrganization
from app.identity.models.workspace import Workspace, WorkspaceSessionContext, WorkspaceStatus
from app.identity.services.clinical_authorization_context_service import (
    ClinicalAuthorizationContextService,
)
from app.models.clinical_scope import ClinicalLabFacilityBinding, ClinicalLabFacilityBindingStatus
from app.models.lab_user import LabUser
from app.services.clinical_legacy_read_scope import ClinicalLegacyReadScope


class ClinicalGatewayBlocked(PermissionError):
    """A clinical context that cannot be proven must remain blocked."""

    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


@dataclass(frozen=True)
class ClinicalGatewayContext:
    actor: NiamActor
    workspace: Workspace
    membership: Membership
    legacy_link: LegacyAccountLink
    legacy_user: LabUser
    binding: ClinicalLabFacilityBinding
    scope: ClinicalLegacyReadScope


class ClinicalGatewayContextResolver:
    """Resolve all clinical scope from trusted server state before any read query."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.facade = SyncSessionAsyncFacade(db)

    def resolve(self, actor: NiamActor) -> ClinicalGatewayContext:
        workspace_context = (
            self.db.query(WorkspaceSessionContext)
            .filter(
                WorkspaceSessionContext.session_id == actor.session.id,
                WorkspaceSessionContext.account_id == actor.account.id,
                WorkspaceSessionContext.is_active.is_(True),
            )
            .one_or_none()
        )
        if workspace_context is None:
            raise ClinicalGatewayBlocked("missing_workspace")

        workspace = self.db.get(Workspace, workspace_context.workspace_id)
        if (
            workspace is None
            or workspace.status != WorkspaceStatus.active.value
            or not workspace.organization_id
            or not workspace.facility_id
        ):
            raise ClinicalGatewayBlocked("workspace_inactive")

        niam_organization = self.db.get(NIAMOrganization, workspace.organization_id)
        niam_facility = self.db.get(NIAMAdminFacility, workspace.facility_id)
        if (
            niam_organization is None
            or not niam_organization.is_active
            or niam_organization.status != "active"
            or niam_facility is None
            or not niam_facility.is_active
            or niam_facility.status != "active"
            or niam_facility.organization_id != workspace.organization_id
        ):
            raise ClinicalGatewayBlocked("invalid_context")

        now = datetime.now(UTC)
        memberships = (
            self.db.query(Membership)
            .filter(
                Membership.account_id == actor.account.id,
                Membership.organization_id == workspace.organization_id,
                Membership.status == MembershipStatus.active.value,
                Membership.is_active.is_(True),
                or_(Membership.workspace_id.is_(None), Membership.workspace_id == workspace.id),
                or_(
                    Membership.facility_id.is_(None),
                    Membership.facility_id == workspace.facility_id,
                ),
                or_(Membership.expires_at.is_(None), Membership.expires_at > now),
            )
            .all()
        )
        if not memberships:
            raise ClinicalGatewayBlocked("membership_missing")
        membership = max(
            memberships,
            key=lambda item: sum(
                getattr(item, field) is not None
                for field in ("facility_id", "department_id", "unit_id", "workspace_id")
            ),
        )

        links = (
            self.db.query(LegacyAccountLink)
            .filter(
                LegacyAccountLink.source_kind == LegacyAccountLinkSource.lab_user.value,
                LegacyAccountLink.canonical_account_id == actor.account.id,
                LegacyAccountLink.status == LegacyAccountLinkStatus.migrated.value,
            )
            .all()
        )
        if len(links) != 1:
            raise ClinicalGatewayBlocked("legacy_identity_unresolved")
        legacy_link = links[0]
        legacy_user = self.db.get(LabUser, legacy_link.legacy_account_id)
        if legacy_user is None or not legacy_user.is_active or legacy_user.lab_id <= 0:
            raise ClinicalGatewayBlocked("legacy_identity_unresolved")

        bindings = (
            self.db.query(ClinicalLabFacilityBinding)
            .filter(
                ClinicalLabFacilityBinding.legacy_lab_id == legacy_user.lab_id,
                ClinicalLabFacilityBinding.facility_resource_id.isnot(None),
                ClinicalLabFacilityBinding.status == ClinicalLabFacilityBindingStatus.active.value,
                ClinicalLabFacilityBinding.niam_organization_id == workspace.organization_id,
                ClinicalLabFacilityBinding.niam_facility_id == workspace.facility_id,
            )
            .all()
        )
        if not bindings:
            raise ClinicalGatewayBlocked("facility_mapping_unavailable")
        if len(bindings) != 1:
            raise ClinicalGatewayBlocked("facility_mapping_ambiguous")
        binding = bindings[0]

        try:
            # Reuse the reviewed account→identity→assignment→facility proof chain.
            asyncio.run(
                ClinicalAuthorizationContextService(self.facade).resolve_for_legacy_lab_user(
                    legacy_lab_user_id=legacy_user.id,
                    legacy_lab_id=legacy_user.lab_id,
                    expected_niam_organization_id=workspace.organization_id,
                    expected_niam_facility_id=workspace.facility_id,
                ),
            )
        except Exception as exc:
            if isinstance(exc, ClinicalGatewayBlocked):
                raise
            raise ClinicalGatewayBlocked("invalid_context") from exc

        scope = ClinicalLegacyReadScope(
            legacy_lab_id=legacy_user.lab_id,
            legacy_lab_user_id=legacy_user.id,
            operational_facility_id=binding.facility_resource_id,
            operational_organization_id=self._operational_organization_id(
                binding.facility_resource_id
            ),
            tenant_id=self._tenant_id(binding.facility_resource_id),
            niam_organization_id=workspace.organization_id,
            niam_facility_id=workspace.facility_id,
            niam_workspace_id=workspace.id,
            scope_mapping_version=binding.mapping_version,
        )
        return ClinicalGatewayContext(
            actor=actor,
            workspace=workspace,
            membership=membership,
            legacy_link=legacy_link,
            legacy_user=legacy_user,
            binding=binding,
            scope=scope,
        )

    def _operational_organization_id(self, facility_resource_id: int) -> int:
        from app.models.organization import Facility

        facility = self.db.get(Facility, facility_resource_id)
        if facility is None or not facility.is_active:
            raise ClinicalGatewayBlocked("facility_mismatch")
        return int(facility.organization_id)

    def _tenant_id(self, facility_resource_id: int) -> int:
        from app.models.organization import Organization

        organization_id = self._operational_organization_id(facility_resource_id)
        organization = self.db.get(Organization, organization_id)
        if organization is None or not organization.is_active or organization.tenant_id is None:
            raise ClinicalGatewayBlocked("cross_tenant_scope")
        return int(organization.tenant_id)
