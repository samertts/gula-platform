from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app._compat import UTC
from app.identity.workspaces.models import (
    WORKSPACE_MEMBER_ROLES,
    WORKSPACE_TYPES,
    Workspace,
    WorkspaceDelegation,
    WorkspaceDepartment,
    WorkspaceInvitation,
    WorkspaceMembership,
    WorkspacePermissionTemplate,
    WorkspaceRole,
    WorkspaceTeam,
)


class WorkspaceError(Exception):
    pass


class WorkspaceIsolationError(WorkspaceError):
    """Raised when a permission or operation crosses workspace boundaries."""


class WorkspaceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Workspace lifecycle ────────────────────────────────────────────────────

    async def create_workspace(
        self,
        owner_identity_id: str,
        owner_person_id: str,
        name_en: str,
        name_ar: str,
        workspace_type: str,
        organization_id: str | None = None,
        description: str | None = None,
        settings: dict[str, Any] | None = None,
    ) -> Workspace:
        if workspace_type not in WORKSPACE_TYPES:
            raise WorkspaceError(
                f"invalid workspace_type '{workspace_type}'; allowed: {WORKSPACE_TYPES}"
            )
        workspace = Workspace(
            id=...,
            uuid=str(uuid.uuid4()),
            workspace_id=f"WS-{uuid.uuid4().hex[:16].upper()}",
            owner_identity_id=owner_identity_id,
            owner_person_id=owner_person_id,
            organization_id=organization_id,
            name_en=name_en,
            name_ar=name_ar,
            workspace_type=workspace_type,
            description=description,
            status="active",
            settings=settings,
            is_active=True,
        )
        self.session.add(workspace)
        await self.session.flush()

        owner_role = await self._get_or_create_system_role(
            workspace.id, "owner", "Full ownership of the workspace"
        )
        await self._add_member(
            workspace_id=workspace.id,
            identity_id=owner_identity_id,
            person_id=owner_person_id,
            role_id=owner_role.id,
            role_name="owner",
            status="active",
            active_workspace=True,
        )
        return workspace

    async def get_workspace(self, workspace_id: str) -> Workspace | None:
        stmt = select(Workspace).where(
            Workspace.workspace_id == workspace_id,
            Workspace.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_workspaces_for_identity(self, identity_id: str) -> list[Workspace]:
        stmt = (
            select(Workspace)
            .join(WorkspaceMembership, WorkspaceMembership.workspace_id == Workspace.id)
            .where(
                WorkspaceMembership.identity_id == identity_id,
                WorkspaceMembership.status == "active",
                Workspace.is_active.is_(True),
            )
            .order_by(Workspace.name_en)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())

    async def update_workspace(
        self,
        workspace_id: str,
        actor_identity_id: str,
        name_en: str | None = None,
        name_ar: str | None = None,
        description: str | None = None,
        settings: dict[str, Any] | None = None,
    ) -> Workspace:
        workspace = await self.get_workspace(workspace_id)
        if not workspace:
            raise WorkspaceError("workspace_not_found")
        if not await self.has_role(workspace.id, actor_identity_id, {"owner", "admin"}):
            raise WorkspaceIsolationError("actor_not_workspace_admin")
        if name_en is not None:
            workspace.name_en = name_en
        if name_ar is not None:
            workspace.name_ar = name_ar
        if description is not None:
            workspace.description = description
        if settings is not None:
            workspace.settings = settings
        await self.session.flush()
        return workspace

    async def suspend_workspace(
        self, workspace_id: str, actor_identity_id: str, reason: str = ""
    ) -> Workspace:
        workspace = await self.get_workspace(workspace_id)
        if not workspace:
            raise WorkspaceError("workspace_not_found")
        if not await self.has_role(workspace.id, actor_identity_id, {"owner"}):
            raise WorkspaceIsolationError("actor_not_workspace_owner")
        workspace.status = "suspended"
        await self.session.flush()
        return workspace

    async def close_workspace(
        self, workspace_id: str, actor_identity_id: str, reason: str = ""
    ) -> Workspace:
        workspace = await self.get_workspace(workspace_id)
        if not workspace:
            raise WorkspaceError("workspace_not_found")
        if not await self.has_role(workspace.id, actor_identity_id, {"owner"}):
            raise WorkspaceIsolationError("actor_not_workspace_owner")
        workspace.status = "closed"
        await self.session.flush()
        return workspace

    # ── Roles ──────────────────────────────────────────────────────────────────

    async def create_role(
        self,
        workspace_id: str,
        actor_identity_id: str,
        name: str,
        permissions: list[str],
        description: str | None = None,
    ) -> WorkspaceRole:
        if not await self.has_role(workspace_id, actor_identity_id, {"owner", "admin"}):
            raise WorkspaceIsolationError("actor_not_workspace_admin")
        role = WorkspaceRole(
            id=...,
            uuid=str(uuid.uuid4()),
            role_id=f"WR-{uuid.uuid4().hex[:16].upper()}",
            workspace_id=workspace_id,
            name=name,
            description=description,
            permissions=permissions,
            is_system=False,
            is_active=True,
        )
        self.session.add(role)
        await self.session.flush()
        return role

    async def _get_or_create_system_role(
        self, workspace_id: str, name: str, description: str
    ) -> WorkspaceRole:
        stmt = select(WorkspaceRole).where(
            WorkspaceRole.workspace_id == workspace_id,
            WorkspaceRole.name == name,
            WorkspaceRole.is_system.is_(True),
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            return existing
        role = WorkspaceRole(
            id=...,
            uuid=str(uuid.uuid4()),
            role_id=f"WR-{uuid.uuid4().hex[:16].upper()}",
            workspace_id=workspace_id,
            name=name,
            description=description,
            permissions=["*"],
            is_system=True,
            is_active=True,
        )
        self.session.add(role)
        await self.session.flush()
        return role

    async def list_roles(self, workspace_id: str) -> list[WorkspaceRole]:
        stmt = select(WorkspaceRole).where(
            WorkspaceRole.workspace_id == workspace_id,
            WorkspaceRole.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ── Members ────────────────────────────────────────────────────────────────

    async def _add_member(
        self,
        workspace_id: str,
        identity_id: str,
        person_id: str,
        role_id: str | None,
        role_name: str,
        status: str,
        active_workspace: bool = False,
    ) -> WorkspaceMembership:
        member = WorkspaceMembership(
            id=...,
            uuid=str(uuid.uuid4()),
            membership_id=f"WM-{uuid.uuid4().hex[:16].upper()}",
            workspace_id=workspace_id,
            identity_id=identity_id,
            person_id=person_id,
            role_id=role_id,
            role_name=role_name,
            status=status,
            active_workspace=active_workspace,
            is_active=True,
        )
        self.session.add(member)
        await self.session.flush()
        return member

    async def add_member(
        self,
        workspace_id: str,
        actor_identity_id: str,
        identity_id: str,
        person_id: str,
        role_name: str,
    ) -> WorkspaceMembership:
        if not await self.has_role(workspace_id, actor_identity_id, {"owner", "admin"}):
            raise WorkspaceIsolationError("actor_not_workspace_admin")
        if role_name not in WORKSPACE_MEMBER_ROLES:
            raise WorkspaceError(f"invalid role_name '{role_name}'")
        role = await self._find_role(workspace_id, role_name)
        return await self._add_member(
            workspace_id=workspace_id,
            identity_id=identity_id,
            person_id=person_id,
            role_id=role.id if role else None,
            role_name=role_name,
            status="active",
        )

    async def _find_role(self, workspace_id: str, role_name: str) -> WorkspaceRole | None:
        stmt = select(WorkspaceRole).where(
            WorkspaceRole.workspace_id == workspace_id,
            WorkspaceRole.name == role_name,
            WorkspaceRole.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def remove_member(
        self,
        workspace_id: str,
        actor_identity_id: str,
        member_person_id: str,
    ) -> WorkspaceMembership:
        if not await self.has_role(workspace_id, actor_identity_id, {"owner", "admin"}):
            raise WorkspaceIsolationError("actor_not_workspace_admin")
        member = await self._find_member(workspace_id, member_person_id)
        if not member:
            raise WorkspaceError("member_not_found")
        if member.role_name == "owner":
            owner_count = await self._count_owners(workspace_id)
            if owner_count <= 1:
                raise WorkspaceError("cannot_remove_last_owner")
        member.status = "removed"
        member.active_workspace = False
        member.is_active = False
        await self.session.flush()
        return member

    async def suspend_member(
        self,
        workspace_id: str,
        actor_identity_id: str,
        member_person_id: str,
    ) -> WorkspaceMembership:
        if not await self.has_role(workspace_id, actor_identity_id, {"owner", "admin"}):
            raise WorkspaceIsolationError("actor_not_workspace_admin")
        member = await self._find_member(workspace_id, member_person_id)
        if not member:
            raise WorkspaceError("member_not_found")
        if member.role_name == "owner":
            raise WorkspaceError("cannot_suspend_owner")
        member.status = "suspended"
        member.active_workspace = False
        await self.session.flush()
        return member

    async def assign_role(
        self,
        workspace_id: str,
        actor_identity_id: str,
        member_person_id: str,
        role_name: str,
    ) -> WorkspaceMembership:
        if not await self.has_role(workspace_id, actor_identity_id, {"owner", "admin"}):
            raise WorkspaceIsolationError("actor_not_workspace_admin")
        if role_name not in WORKSPACE_MEMBER_ROLES:
            raise WorkspaceError(f"invalid role_name '{role_name}'")
        member = await self._find_member(workspace_id, member_person_id)
        if not member:
            raise WorkspaceError("member_not_found")
        role = await self._find_role(workspace_id, role_name)
        member.role_name = role_name
        member.role_id = role.id if role else None
        await self.session.flush()
        return member

    async def _find_member(
        self, workspace_id: str, person_id: str
    ) -> WorkspaceMembership | None:
        stmt = select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.person_id == person_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _count_owners(self, workspace_id: str) -> int:
        stmt = select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.role_name == "owner",
            WorkspaceMembership.status == "active",
        )
        result = await self.session.execute(stmt)
        return len(list(result.scalars().all()))

    async def list_members(self, workspace_id: str) -> list[WorkspaceMembership]:
        stmt = select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == workspace_id,
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ── Workspace selection & isolation ────────────────────────────────────────

    async def select_active_workspace(
        self, identity_id: str, workspace_id: str
    ) -> WorkspaceMembership:
        """Bind the identity to ONE workspace (called after login)."""
        workspace = await self.get_workspace(workspace_id)
        if not workspace:
            raise WorkspaceError("workspace_not_found")
        member = await self._find_member_by_identity(workspace_id, identity_id)
        if not member:
            raise WorkspaceIsolationError("identity_not_workspace_member")
        if member.status != "active":
            raise WorkspaceIsolationError("membership_not_active")
        # Deactivate all other selections for this identity, then select this one.
        await self._clear_active_workspaces(identity_id)
        member.active_workspace = True
        await self.session.flush()
        return member

    async def _find_member_by_identity(
        self, workspace_id: str, identity_id: str
    ) -> WorkspaceMembership | None:
        stmt = select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.identity_id == identity_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _clear_active_workspaces(self, identity_id: str) -> None:
        stmt = select(WorkspaceMembership).where(
            WorkspaceMembership.identity_id == identity_id,
            WorkspaceMembership.active_workspace.is_(True),
        )
        result = await self.session.execute(stmt)
        for member in result.scalars().all():
            member.active_workspace = False

    async def get_active_workspace(self, identity_id: str) -> Workspace | None:
        stmt = (
            select(Workspace)
            .join(WorkspaceMembership, WorkspaceMembership.workspace_id == Workspace.id)
            .where(
                WorkspaceMembership.identity_id == identity_id,
                WorkspaceMembership.active_workspace.is_(True),
                Workspace.is_active.is_(True),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def has_role(
        self, workspace_id: str, identity_id: str, allowed_roles: set[str]
    ) -> bool:
        member = await self._find_member_by_identity(workspace_id, identity_id)
        if not member or member.status != "active":
            return False
        return member.role_name in allowed_roles

    async def check_permission(
        self, workspace_id: str, identity_id: str, permission: str
    ) -> bool:
        """Workspace-scoped permission check.

        Permissions NEVER cross workspaces: the membership is resolved inside
        the given workspace, and the role's permission list is consulted only
        there. An identity that is not a member of the workspace always gets
        False — regardless of its permissions in other workspaces.
        """
        member = await self._find_member_by_identity(workspace_id, identity_id)
        if not member or member.status != "active":
            return False
        if member.role_name in {"owner", "admin"}:
            return True
        role = await self._get_role_by_id(member.role_id)
        if not role:
            return False
        return permission in (role.permissions or [])

    async def _get_role_by_id(self, role_id: str | None) -> WorkspaceRole | None:
        if not role_id:
            return None
        stmt = select(WorkspaceRole).where(WorkspaceRole.id == role_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ── Invitations ────────────────────────────────────────────────────────────

    async def invite_member(
        self,
        workspace_id: str,
        actor_identity_id: str,
        invitee_email: str,
        role_name: str,
        invitee_person_id: str | None = None,
    ) -> WorkspaceInvitation:
        if not await self.has_role(workspace_id, actor_identity_id, {"owner", "admin"}):
            raise WorkspaceIsolationError("actor_not_workspace_admin")
        if role_name not in WORKSPACE_MEMBER_ROLES:
            raise WorkspaceError(f"invalid role_name '{role_name}'")
        role = await self._find_role(workspace_id, role_name)
        invitation = WorkspaceInvitation(
            id=...,
            uuid=str(uuid.uuid4()),
            invitation_id=f"WI-{uuid.uuid4().hex[:16].upper()}",
            workspace_id=workspace_id,
            invitee_email=invitee_email,
            invitee_person_id=invitee_person_id,
            role_id=role.id if role else None,
            role_name=role_name,
            token=secrets.token_urlsafe(32),
            status="pending",
            expires_at=datetime.now(UTC) + timedelta(days=7),
            is_active=True,
        )
        self.session.add(invitation)
        await self.session.flush()
        return invitation

    async def revoke_invitation(
        self, workspace_id: str, actor_identity_id: str, invitation_id: str
    ) -> WorkspaceInvitation:
        if not await self.has_role(workspace_id, actor_identity_id, {"owner", "admin"}):
            raise WorkspaceIsolationError("actor_not_workspace_admin")
        invitation = await self._find_invitation(workspace_id, invitation_id)
        if not invitation:
            raise WorkspaceError("invitation_not_found")
        invitation.status = "revoked"
        invitation.is_active = False
        await self.session.flush()
        return invitation

    async def _find_invitation(
        self, workspace_id: str, invitation_id: str
    ) -> WorkspaceInvitation | None:
        stmt = select(WorkspaceInvitation).where(
            WorkspaceInvitation.workspace_id == workspace_id,
            WorkspaceInvitation.invitation_id == invitation_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ── Permission templates ───────────────────────────────────────────────────

    async def create_permission_template(
        self,
        workspace_id: str,
        actor_identity_id: str,
        name: str,
        permissions: list[str],
        description: str | None = None,
    ) -> WorkspacePermissionTemplate:
        if not await self.has_role(workspace_id, actor_identity_id, {"owner", "admin"}):
            raise WorkspaceIsolationError("actor_not_workspace_admin")
        template = WorkspacePermissionTemplate(
            id=...,
            uuid=str(uuid.uuid4()),
            template_id=f"WPT-{uuid.uuid4().hex[:16].upper()}",
            workspace_id=workspace_id,
            name=name,
            description=description,
            permissions=permissions,
            is_active=True,
        )
        self.session.add(template)
        await self.session.flush()
        return template

    async def list_permission_templates(
        self, workspace_id: str
    ) -> list[WorkspacePermissionTemplate]:
        stmt = select(WorkspacePermissionTemplate).where(
            WorkspacePermissionTemplate.workspace_id == workspace_id,
            WorkspacePermissionTemplate.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ── Departments & Teams ────────────────────────────────────────────────────

    async def create_department(
        self,
        workspace_id: str,
        actor_identity_id: str,
        name_en: str,
        name_ar: str,
        dept_type: str | None = None,
        head_person_id: str | None = None,
    ) -> WorkspaceDepartment:
        if not await self.has_role(workspace_id, actor_identity_id, {"owner", "admin"}):
            raise WorkspaceIsolationError("actor_not_workspace_admin")
        dept = WorkspaceDepartment(
            id=...,
            uuid=str(uuid.uuid4()),
            dept_id=f"WD-{uuid.uuid4().hex[:16].upper()}",
            workspace_id=workspace_id,
            name_en=name_en,
            name_ar=name_ar,
            dept_type=dept_type,
            head_person_id=head_person_id,
            is_active=True,
        )
        self.session.add(dept)
        await self.session.flush()
        return dept

    async def list_departments(self, workspace_id: str) -> list[WorkspaceDepartment]:
        stmt = select(WorkspaceDepartment).where(
            WorkspaceDepartment.workspace_id == workspace_id,
            WorkspaceDepartment.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_team(
        self,
        workspace_id: str,
        actor_identity_id: str,
        name_en: str,
        name_ar: str,
        department_id: str | None = None,
        leader_person_id: str | None = None,
    ) -> WorkspaceTeam:
        if not await self.has_role(workspace_id, actor_identity_id, {"owner", "admin"}):
            raise WorkspaceIsolationError("actor_not_workspace_admin")
        team = WorkspaceTeam(
            id=...,
            uuid=str(uuid.uuid4()),
            team_id=f"WT-{uuid.uuid4().hex[:16].upper()}",
            workspace_id=workspace_id,
            department_id=department_id,
            name_en=name_en,
            name_ar=name_ar,
            leader_person_id=leader_person_id,
            is_active=True,
        )
        self.session.add(team)
        await self.session.flush()
        return team

    async def list_teams(self, workspace_id: str) -> list[WorkspaceTeam]:
        stmt = select(WorkspaceTeam).where(
            WorkspaceTeam.workspace_id == workspace_id,
            WorkspaceTeam.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ── Delegation ─────────────────────────────────────────────────────────────

    async def delegate_authority(
        self,
        workspace_id: str,
        delegated_from_person_id: str,
        delegated_to_person_id: str,
        permissions: list[str],
        end_at: datetime | None = None,
    ) -> WorkspaceDelegation:
        delegation = WorkspaceDelegation(
            id=...,
            uuid=str(uuid.uuid4()),
            delegation_id=f"WDEL-{uuid.uuid4().hex[:16].upper()}",
            workspace_id=workspace_id,
            delegated_from_person_id=delegated_from_person_id,
            delegated_to_person_id=delegated_to_person_id,
            permissions=permissions,
            status="active",
            start_at=datetime.now(UTC),
            end_at=end_at,
            is_active=True,
        )
        self.session.add(delegation)
        await self.session.flush()
        return delegation

    async def revoke_delegation(
        self, workspace_id: str, delegation_id: str, revoked_by: str
    ) -> WorkspaceDelegation:
        delegation = await self._find_delegation(workspace_id, delegation_id)
        if not delegation:
            raise WorkspaceError("delegation_not_found")
        delegation.status = "revoked"
        delegation.is_active = False
        delegation.revoked_by = revoked_by
        delegation.revoked_at = datetime.now(UTC)
        await self.session.flush()
        return delegation

    async def _find_delegation(
        self, workspace_id: str, delegation_id: str
    ) -> WorkspaceDelegation | None:
        stmt = select(WorkspaceDelegation).where(
            WorkspaceDelegation.workspace_id == workspace_id,
            WorkspaceDelegation.delegation_id == delegation_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def check_delegated_permission(
        self, workspace_id: str, person_id: str, permission: str
    ) -> bool:
        stmt = select(WorkspaceDelegation).where(
            WorkspaceDelegation.workspace_id == workspace_id,
            WorkspaceDelegation.delegated_to_person_id == person_id,
            WorkspaceDelegation.status == "active",
            WorkspaceDelegation.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        now = datetime.now(UTC)
        for delegation in result.scalars().all():
            if delegation.end_at and delegation.end_at < now:
                continue
            if permission in (delegation.permissions or []):
                return True
        return False
