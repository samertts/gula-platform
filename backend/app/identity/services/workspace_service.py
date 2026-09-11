from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app._compat import UTC
from app.identity.models.account import Account, AccountStatus, AccountType
from app.identity.models.administrative_structure import (
    OrganizationOwnership,
    OrganizationRepresentative,
    OwnershipStatus,
    RepresentativeStatus,
)
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
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def citizen_key(account_id: str) -> str:
        return f"citizen:{account_id}"

    @staticmethod
    def professional_key(account_id: str, professional_type: str) -> str:
        return f"professional:{account_id}:{professional_type}"

    def ensure_citizen_workspace(self, account: Account) -> Workspace | None:
        if account.account_type != AccountType.human.value or account.status != AccountStatus.active.value or not account.is_active:
            return None
        key = self.citizen_key(account.id)
        result = self.session.execute(select(Workspace).where(Workspace.workspace_key == key))
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
        self.session.flush()
        self.transition(workspace, WorkspaceStatus.active)
        self.session.flush()
        from app.identity.models.audit import AuditAction
        from app.identity.services.audit_service import AuditService

        AuditService(self.session).record(
            AuditAction.workspace_created,
            actor_id=account.id,
            actor_type="account",
            target_type="workspace",
            target_id=workspace.id,
            metadata={"workspace_type": workspace.workspace_type, "idempotent": True},
        )
        return workspace

    def ensure_professional_workspace(self, account: Account, professional_type: str) -> Workspace | None:
        if not self._professional_eligible(account.id, professional_type):
            return None
        key = self.professional_key(account.id, professional_type)
        result = self.session.execute(select(Workspace).where(Workspace.workspace_key == key))
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
        self.session.flush()
        self.transition(workspace, WorkspaceStatus.active)
        self.session.flush()
        return workspace

    def list_eligible(self, account: Account) -> list[Workspace]:
        if account.status != AccountStatus.active.value or not account.is_active:
            return []
        direct = select(Workspace).where(
            Workspace.owner_account_id == account.id,
            Workspace.status.in_([WorkspaceStatus.active.value, WorkspaceStatus.restricted.value]),
        )
        result = self.session.execute(direct)
        workspaces = {workspace.id: workspace for workspace in result.scalars().all()}

        # AUTH-F5. Eligibility is a conjunction, not a single fact: an active
        # standing in an organization, an organization that is itself live, and
        # a workspace that is available. Membership in `niam_memberships` is
        # deliberately *not* consulted — it is necessary context, not a grant,
        # and wiring it here would hand access to every member of every
        # organization. Whether membership should confer eligibility is a
        # platform policy decision, recorded as AUTH-F5 and still open.
        organization_ids = select(OrganizationRepresentative.organization_id).where(
            OrganizationRepresentative.account_id == account.id,
            OrganizationRepresentative.status == RepresentativeStatus.active.value,
        )
        ownership_ids = select(OrganizationOwnership.organization_id).where(
            OrganizationOwnership.account_id == account.id,
            OrganizationOwnership.status == OwnershipStatus.active.value,
        )
        # The organization's own standing was not checked before AUTH-005: a
        # representative of a deactivated organization kept its workspaces.
        live_organization_ids = select(NIAMOrganization.id).where(
            NIAMOrganization.id.in_(organization_ids.union(ownership_ids)),
            NIAMOrganization.is_active.is_(True),
            NIAMOrganization.status == "active",
        )
        organization_result = self.session.execute(
            select(Workspace).where(
                Workspace.organization_id.in_(live_organization_ids),
                Workspace.status.in_([WorkspaceStatus.active.value, WorkspaceStatus.restricted.value]),
            ),
        )
        for workspace in organization_result.scalars().all():
            workspaces[workspace.id] = workspace
        return list(workspaces.values())

    def switch(self, account: Account, session_id: str, workspace_id: str) -> WorkspaceSessionContext:
        if account.status != AccountStatus.active.value or not account.is_active:
            raise WorkspaceAccessDenied("Account is not eligible for workspace access")
        eligible = self.list_eligible(account)
        workspace = next((item for item in eligible if item.id == workspace_id), None)
        if workspace is None or workspace.status != WorkspaceStatus.active.value:
            raise WorkspaceAccessDenied("Workspace is not available to this account")

        result = self.session.execute(
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
        self.session.flush()
        return context

    def _professional_eligible(self, account_id: str, professional_type: str) -> bool:
        result = self.session.execute(
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
