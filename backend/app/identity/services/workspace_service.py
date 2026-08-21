from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app._compat import UTC
from app.identity.models.account import Account, AccountStatus, AccountType
from app.identity.models.administrative_structure import NIAMAdminFacility
from app.identity.models.membership import Membership, MembershipStatus
from app.identity.models.niam_organization import NIAMOrganization
from app.identity.models.verification_record import (
    VerificationRecord,
    VerificationRecordStatus,
    VerificationRecordType,
)
from app.identity.models.workspace import (
    Workspace,
    WorkspaceSessionContext,
    WorkspaceStatus,
    WorkspaceType,
)


class WorkspaceAccessDenied(PermissionError):
    """Raised for missing, inactive or unauthorized workspace context."""


class WorkspaceStateError(ValueError):
    """Raised for invalid workspace lifecycle transitions."""


LEGAL_WORKSPACE_TRANSITIONS: dict[str, frozenset[str]] = {
    WorkspaceStatus.provisioning.value: frozenset({WorkspaceStatus.active.value, WorkspaceStatus.deactivated.value}),
    WorkspaceStatus.active.value: frozenset({WorkspaceStatus.restricted.value, WorkspaceStatus.suspended.value, WorkspaceStatus.archived.value, WorkspaceStatus.deactivated.value}),
    WorkspaceStatus.restricted.value: frozenset({WorkspaceStatus.active.value, WorkspaceStatus.suspended.value, WorkspaceStatus.archived.value, WorkspaceStatus.deactivated.value}),
    WorkspaceStatus.suspended.value: frozenset({WorkspaceStatus.active.value, WorkspaceStatus.archived.value, WorkspaceStatus.deactivated.value}),
    WorkspaceStatus.archived.value: frozenset(),
    WorkspaceStatus.deactivated.value: frozenset(),
}


class WorkspaceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def citizen_key(account_id: str) -> str:
        return f"citizen:{account_id}"

    @staticmethod
    def professional_key(account_id: str, professional_type: str) -> str:
        return f"professional:{account_id}:{professional_type}"

    async def ensure_citizen_workspace(self, account: Account) -> Workspace | None:
        if account.account_type != AccountType.human.value or account.status != AccountStatus.active.value or not account.is_active:
            return None
        key = self.citizen_key(account.id)
        result = await self.session.execute(select(Workspace).where(Workspace.workspace_key == key))
        existing = result.scalar_one_or_none()
        if existing:
            return existing
        workspace = Workspace(
            uuid=str(uuid.uuid4()),
            workspace_key=key,
            workspace_type=WorkspaceType.citizen.value,
            name="Citizen Workspace",
            name_ar="مساحة المواطن",
            status=WorkspaceStatus.provisioning.value,
            owner_account_id=account.id,
            is_personal=True,
        )
        self.session.add(workspace)
        await self.session.flush()
        self.transition(workspace, WorkspaceStatus.active)
        await self.session.flush()
        from app.identity.models.audit import AuditAction
        from app.identity.services.audit_service import AuditService

        await AuditService(self.session).record(
            AuditAction.workspace_created,
            actor_id=account.id,
            actor_type="account",
            target_type="workspace",
            target_id=workspace.id,
            decision="allow",
            reason_code="workspace_created",
            source="niam_workspace",
            metadata={"workspace_type": workspace.workspace_type, "idempotent": True},
        )
        return workspace

    async def ensure_professional_workspace(self, account: Account, professional_type: str) -> Workspace | None:
        if not await self._professional_eligible(account.id, professional_type):
            return None
        key = self.professional_key(account.id, professional_type)
        result = await self.session.execute(select(Workspace).where(Workspace.workspace_key == key))
        existing = result.scalar_one_or_none()
        if existing:
            return existing
        workspace = Workspace(
            uuid=str(uuid.uuid4()),
            workspace_key=key,
            workspace_type=WorkspaceType.professional.value,
            name=f"{professional_type.title()} Workspace",
            name_ar="المساحة المهنية",
            status=WorkspaceStatus.provisioning.value,
            owner_account_id=account.id,
            professional_type=professional_type,
            is_personal=False,
        )
        self.session.add(workspace)
        await self.session.flush()
        self.transition(workspace, WorkspaceStatus.active)
        await self.session.flush()
        return workspace

    async def list_eligible(self, account: Account) -> list[Workspace]:
        if account.status != AccountStatus.active.value or not account.is_active:
            return []
        # Personal citizen workspaces are owned directly by the account. An
        # organization-owned workspace must never be reachable merely because
        # the account is an organization owner/representative: access is
        # derived from an active, unexpired Membership with matching scope.
        direct = (
            select(Workspace)
            .outerjoin(NIAMOrganization, Workspace.organization_id == NIAMOrganization.id)
            .outerjoin(NIAMAdminFacility, Workspace.facility_id == NIAMAdminFacility.id)
            .where(
                Workspace.owner_account_id == account.id,
                Workspace.organization_id.is_(None),
                Workspace.status.in_([WorkspaceStatus.active.value, WorkspaceStatus.restricted.value]),
            )
        )
        result = await self.session.execute(direct)
        workspaces = {workspace.id: workspace for workspace in result.scalars().all()}

        membership_result = await self.session.execute(
            select(Membership).where(
                Membership.account_id == account.id,
                Membership.status == MembershipStatus.active.value,
                Membership.is_active.is_(True),
                or_(Membership.expires_at.is_(None), Membership.expires_at > datetime.now(UTC)),
            ),
        )
        memberships = list(membership_result.scalars().all())
        if not memberships:
            return list(workspaces.values())

        scoped_membership_conditions = []
        for membership in memberships:
            # Workspace has no unit relation. A unit-scoped membership without
            # an explicit workspace must not broaden into an organization or
            # department-wide workspace grant.
            if membership.unit_id is not None and membership.workspace_id is None:
                continue
            conditions = [Workspace.organization_id == membership.organization_id]
            for field in ("facility_id", "department_id"):
                value = getattr(membership, field, None)
                if value is not None:
                    conditions.append(getattr(Workspace, field) == value)
            if membership.workspace_id is not None:
                conditions.append(Workspace.id == membership.workspace_id)
            scoped_membership_conditions.append(and_(*conditions))

        if not scoped_membership_conditions:
            return list(workspaces.values())

        organization_result = await self.session.execute(
            select(Workspace)
            .join(NIAMOrganization, Workspace.organization_id == NIAMOrganization.id)
            .outerjoin(NIAMAdminFacility, Workspace.facility_id == NIAMAdminFacility.id)
            .where(
                or_(*scoped_membership_conditions),
                Workspace.status.in_([WorkspaceStatus.active.value, WorkspaceStatus.restricted.value]),
                NIAMOrganization.status == "active",
                NIAMOrganization.is_active.is_(True),
                or_(
                    Workspace.facility_id.is_(None),
                    and_(
                        NIAMAdminFacility.organization_id == Workspace.organization_id,
                        NIAMAdminFacility.status == "active",
                        NIAMAdminFacility.is_active.is_(True),
                    ),
                ),
            ),
        )
        for workspace in organization_result.scalars().all():
            workspaces[workspace.id] = workspace
        return list(workspaces.values())

    async def switch(self, account: Account, session_id: str, workspace_id: str) -> WorkspaceSessionContext:
        if account.status != AccountStatus.active.value or not account.is_active:
            raise WorkspaceAccessDenied("Account is not eligible for workspace access")
        eligible = await self.list_eligible(account)
        workspace = next((item for item in eligible if item.id == workspace_id), None)
        if workspace is None or workspace.status != WorkspaceStatus.active.value:
            raise WorkspaceAccessDenied("Workspace is not available to this account")

        result = await self.session.execute(
            select(WorkspaceSessionContext).where(WorkspaceSessionContext.session_id == session_id),
        )
        context = result.scalar_one_or_none()
        if context is None:
            context = WorkspaceSessionContext(
                session_id=session_id,
                account_id=account.id,
                identity_id=account.identity_id,
                workspace_id=workspace.id,
                version=1,
                is_active=True,
            )
            self.session.add(context)
        else:
            if context.account_id != account.id or not context.is_active:
                raise WorkspaceAccessDenied("Workspace context does not belong to this account")
            context.workspace_id = workspace.id
            context.version += 1
        await self.session.flush()
        return context

    async def _professional_eligible(self, account_id: str, professional_type: str) -> bool:
        result = await self.session.execute(
            select(VerificationRecord.id).where(
                VerificationRecord.account_id == account_id,
                VerificationRecord.record_type == VerificationRecordType.professional.value,
                VerificationRecord.professional_type == professional_type,
                VerificationRecord.status == VerificationRecordStatus.verified.value,
                or_(VerificationRecord.expires_at.is_(None), VerificationRecord.expires_at > datetime.now(UTC)),
                VerificationRecord.is_active.is_(True),
            ).limit(1),
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    def transition(workspace: Workspace, target: WorkspaceStatus) -> Workspace:
        current = str(workspace.status)
        if target.value not in LEGAL_WORKSPACE_TRANSITIONS.get(current, frozenset()):
            raise WorkspaceStateError(f"Illegal workspace transition: {current} -> {target.value}")
        workspace.status = target.value
        workspace.version = (workspace.version or 1) + 1
        return workspace
