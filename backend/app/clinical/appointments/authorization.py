from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app._compat import UTC
from app.identity.api.workspaces import NiamActor
from app.identity.models.account import Account, AccountStatus
from app.identity.models.authorization import (
    Permission,
    RoleAssignment,
    RoleAssignmentStatus,
    RolePermission,
)
from app.identity.models.identity import IdentityRecord
from app.identity.models.membership import Membership, MembershipStatus
from app.identity.models.person import Person
from app.identity.models.workspace import Workspace, WorkspaceSessionContext, WorkspaceStatus


class AppointmentAuthorizationError(Exception):
    """Internal denial reason; routes expose only a bounded error code."""

    def __init__(self, reason: str, *, organization_id: str | None = None, facility_id: str | None = None, workspace_id: str | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.organization_id = organization_id
        self.facility_id = facility_id
        self.workspace_id = workspace_id


@dataclass(frozen=True)
class AppointmentScope:
    organization_id: str
    facility_id: str
    workspace_id: str
    membership_id: str
    actor_person_id: str | None


def _utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class AppointmentAuthorizationService:
    """Shared server-side authorization boundary for canonical appointments."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def resolve_scope(self, actor: NiamActor, requested_workspace_id: str) -> AppointmentScope:
        now = datetime.now(UTC)
        if actor.account.status != AccountStatus.active.value or not actor.account.is_active or actor.account.is_locked:
            raise AppointmentAuthorizationError("account_inactive", workspace_id=requested_workspace_id)
        session_expires_at = _utc(actor.session.expires_at)
        if (
            actor.session.account_id != actor.account.id
            or not actor.session.is_active
            or session_expires_at is None
            or session_expires_at <= now
        ):
            raise AppointmentAuthorizationError("session_invalid", workspace_id=requested_workspace_id)

        context = (
            self.db.query(WorkspaceSessionContext)
            .filter(
                WorkspaceSessionContext.session_id == actor.session.id,
                WorkspaceSessionContext.account_id == actor.account.id,
                WorkspaceSessionContext.identity_id == actor.account.identity_id,
                WorkspaceSessionContext.is_active.is_(True),
                WorkspaceSessionContext.workspace_id == requested_workspace_id,
            )
            .first()
        )
        if context is None:
            raise AppointmentAuthorizationError("workspace_context_mismatch", workspace_id=requested_workspace_id)

        workspace = (
            self.db.query(Workspace)
            .filter(
                Workspace.id == requested_workspace_id,
                Workspace.status == WorkspaceStatus.active.value,
            )
            .first()
        )
        if workspace is None or not workspace.organization_id or not workspace.facility_id:
            raise AppointmentAuthorizationError(
                "workspace_scope_unresolved",
                workspace_id=requested_workspace_id,
            )

        membership = self._membership(actor.account.id, workspace, now)
        if membership is None:
            raise AppointmentAuthorizationError(
                "membership_unresolved",
                organization_id=workspace.organization_id,
                facility_id=workspace.facility_id,
                workspace_id=workspace.id,
            )

        identity = (
            self.db.query(IdentityRecord)
            .filter(
                IdentityRecord.id == actor.account.identity_id,
                IdentityRecord.is_active.is_(True),
            )
            .first()
        )
        actor_person_id = None
        if identity is not None:
            person = (
                self.db.query(Person)
                .filter(Person.id == identity.person_id, Person.is_active.is_(True))
                .first()
            )
            actor_person_id = person.id if person is not None else None
        if actor_person_id is None:
            raise AppointmentAuthorizationError(
                "identity_person_unresolved",
                organization_id=workspace.organization_id,
                facility_id=workspace.facility_id,
                workspace_id=workspace.id,
            )
        return AppointmentScope(
            organization_id=workspace.organization_id,
            facility_id=workspace.facility_id,
            workspace_id=workspace.id,
            membership_id=membership.id,
            actor_person_id=actor_person_id,
        )

    def require_permission(self, actor: NiamActor, scope: AppointmentScope, permission_key: str) -> None:
        permission = (
            self.db.query(Permission)
            .filter(
                Permission.permission_key == permission_key,
                Permission.status == "active",
            )
            .first()
        )
        if permission is None:
            raise AppointmentAuthorizationError(
                "permission_unknown",
                organization_id=scope.organization_id,
                facility_id=scope.facility_id,
                workspace_id=scope.workspace_id,
            )

        now = datetime.now(UTC)
        assignment = (
            self.db.query(RoleAssignment)
            .join(RolePermission, RolePermission.role_id == RoleAssignment.role_id)
            .filter(
                RoleAssignment.account_id == actor.account.id,
                RoleAssignment.organization_id == scope.organization_id,
                RoleAssignment.status == RoleAssignmentStatus.active.value,
                or_(RoleAssignment.expires_at.is_(None), RoleAssignment.expires_at > now),
                or_(RoleAssignment.facility_id.is_(None), RoleAssignment.facility_id == scope.facility_id),
                or_(RoleAssignment.workspace_id.is_(None), RoleAssignment.workspace_id == scope.workspace_id),
                RolePermission.permission_id == permission.id,
                RolePermission.status == "active",
            )
            .first()
        )
        if assignment is None:
            raise AppointmentAuthorizationError(
                "permission_missing",
                organization_id=scope.organization_id,
                facility_id=scope.facility_id,
                workspace_id=scope.workspace_id,
            )

    def require_self_patient(self, scope: AppointmentScope, patient_person_id: str) -> None:
        if not scope.actor_person_id or scope.actor_person_id != patient_person_id:
            raise AppointmentAuthorizationError(
                "patient_scope_denied",
                organization_id=scope.organization_id,
                facility_id=scope.facility_id,
                workspace_id=scope.workspace_id,
            )

    def require_provider_in_scope(self, provider_account_id: str, scope: AppointmentScope) -> None:
        now = datetime.now(UTC)
        provider_membership = (
            self.db.query(Membership)
            .filter(
                Membership.account_id == provider_account_id,
                Membership.organization_id == scope.organization_id,
                Membership.status == MembershipStatus.active.value,
                Membership.is_active.is_(True),
                or_(Membership.expires_at.is_(None), Membership.expires_at > now),
                or_(Membership.facility_id.is_(None), Membership.facility_id == scope.facility_id),
                or_(Membership.workspace_id.is_(None), Membership.workspace_id == scope.workspace_id),
            )
            .first()
        )
        provider = (
            self.db.query(Account)
            .filter(
                Account.id == provider_account_id,
                Account.status == AccountStatus.active.value,
                Account.is_active.is_(True),
                Account.is_locked.is_(False),
            )
            .first()
        )
        if provider is None or provider_membership is None:
            raise AppointmentAuthorizationError(
                "provider_scope_unresolved",
                organization_id=scope.organization_id,
                facility_id=scope.facility_id,
                workspace_id=scope.workspace_id,
            )

    def _membership(self, account_id: str, workspace: Workspace, now: datetime) -> Membership | None:
        memberships = (
            self.db.query(Membership)
            .filter(
                Membership.account_id == account_id,
                Membership.organization_id == workspace.organization_id,
                Membership.status == MembershipStatus.active.value,
                Membership.is_active.is_(True),
                or_(Membership.expires_at.is_(None), Membership.expires_at > now),
                or_(Membership.facility_id.is_(None), Membership.facility_id == workspace.facility_id),
                or_(Membership.workspace_id.is_(None), Membership.workspace_id == workspace.id),
            )
            .all()
        )
        # A workspace-specific membership wins over a broader organization
        # membership. Ambiguous rows fail closed instead of using Last Write Wins.
        exact = [item for item in memberships if item.workspace_id == workspace.id]
        if len(exact) == 1:
            return exact[0]
        if len(exact) > 1:
            raise AppointmentAuthorizationError(
                "membership_ambiguous",
                organization_id=workspace.organization_id,
                facility_id=workspace.facility_id,
                workspace_id=workspace.id,
            )
        facility = [item for item in memberships if item.facility_id == workspace.facility_id and item.workspace_id is None]
        if len(facility) == 1:
            return facility[0]
        if len(facility) > 1:
            raise AppointmentAuthorizationError(
                "membership_ambiguous",
                organization_id=workspace.organization_id,
                facility_id=workspace.facility_id,
                workspace_id=workspace.id,
            )
        broad = [item for item in memberships if item.facility_id is None and item.workspace_id is None]
        if len(broad) == 1:
            return broad[0]
        return None
