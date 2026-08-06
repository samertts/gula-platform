from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, String, Text

from app._compat import UTC, StrEnum
from app.identity.base import IdentityBaseEntity

WORKSPACE_TYPES = [
    "citizen",
    "personal",
    "professional",
    "laboratory",
    "pharmacy",
    "radiology",
    "hospital",
    "blood_bank",
    "public_health",
    "insurance",
    "research",
    "government",
]

WORKSPACE_MEMBER_ROLES = ["owner", "admin", "manager", "member", "viewer"]


class WorkspaceStatus(StrEnum):
    active = "active"
    suspended = "suspended"
    closed = "closed"


class WorkspaceMembershipStatus(StrEnum):
    invited = "invited"
    active = "active"
    suspended = "suspended"
    removed = "removed"


class Workspace(IdentityBaseEntity):
    """A logical compartment that an identity owns and operates within.

    Every identity may own multiple workspaces (Citizen, Laboratory,
    Hospital, Pharmacy, …). The user selects ONE workspace after login and
    permissions never cross workspace boundaries.
    """

    __tablename__ = "niam_workspaces"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    workspace_id = Column(String(100), unique=True, nullable=False, index=True)

    owner_identity_id = Column(
        String(26), ForeignKey("niam_identities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    owner_person_id = Column(
        String(26), ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    organization_id = Column(
        String(26),
        ForeignKey("niam_organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    name_en = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=False)
    workspace_type = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)

    status = Column(String(20), default="active", nullable=False, index=True)
    settings = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)


class WorkspaceRole(IdentityBaseEntity):
    """A role scoped to a single workspace."""

    __tablename__ = "niam_workspace_roles"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    role_id = Column(String(100), unique=True, nullable=False, index=True)
    workspace_id = Column(
        String(26), ForeignKey("niam_workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )

    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    permissions = Column(JSON, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


class WorkspaceMembership(IdentityBaseEntity):
    """Links an identity to a workspace with a single scoped role.

    Isolation rule: a membership grants permissions ONLY inside its
    workspace. No permission is ever resolved across workspaces.
    """

    __tablename__ = "niam_workspace_members"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    membership_id = Column(String(100), unique=True, nullable=False, index=True)
    workspace_id = Column(
        String(26), ForeignKey("niam_workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    identity_id = Column(
        String(26), ForeignKey("niam_identities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    person_id = Column(
        String(26), ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_id = Column(
        String(26), ForeignKey("niam_workspace_roles.id", ondelete="SET NULL"), nullable=True
    )
    role_name = Column(String(100), nullable=False)

    status = Column(String(20), default="invited", nullable=False, index=True)

    invited_by = Column(
        String(26), ForeignKey("niam_persons.id", ondelete="SET NULL"), nullable=True
    )
    invited_at = Column(DateTime(timezone=True), nullable=True)
    joined_at = Column(DateTime(timezone=True), nullable=True)

    active_workspace = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


class WorkspacePermissionTemplate(IdentityBaseEntity):
    """Reusable permission template that owners can assign to members."""

    __tablename__ = "niam_workspace_permission_templates"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    template_id = Column(String(100), unique=True, nullable=False, index=True)
    workspace_id = Column(
        String(26), ForeignKey("niam_workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    permissions = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


class WorkspaceDepartment(IdentityBaseEntity):
    """A department within a workspace's organization."""

    __tablename__ = "niam_workspace_departments"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    dept_id = Column(String(100), unique=True, nullable=False, index=True)
    workspace_id = Column(
        String(26), ForeignKey("niam_workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )

    name_en = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=False)
    dept_type = Column(String(50), nullable=True)
    head_person_id = Column(
        String(26), ForeignKey("niam_persons.id", ondelete="SET NULL"), nullable=True
    )
    is_active = Column(Boolean, default=True, nullable=False)


class WorkspaceTeam(IdentityBaseEntity):
    """A team within a workspace, optionally linked to a department."""

    __tablename__ = "niam_workspace_teams"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    team_id = Column(String(100), unique=True, nullable=False, index=True)
    workspace_id = Column(
        String(26), ForeignKey("niam_workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    department_id = Column(
        String(26),
        ForeignKey("niam_workspace_departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    name_en = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=False)
    leader_person_id = Column(
        String(26), ForeignKey("niam_persons.id", ondelete="SET NULL"), nullable=True
    )
    is_active = Column(Boolean, default=True, nullable=False)


class WorkspaceInvitation(IdentityBaseEntity):
    """Invitation for a person to join a workspace under a given role."""

    __tablename__ = "niam_workspace_invitations"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    invitation_id = Column(String(100), unique=True, nullable=False, index=True)
    workspace_id = Column(
        String(26), ForeignKey("niam_workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    invited_by = Column(
        String(26), ForeignKey("niam_persons.id", ondelete="SET NULL"), nullable=True
    )
    invitee_email = Column(String(200), nullable=False, index=True)
    invitee_person_id = Column(
        String(26), ForeignKey("niam_persons.id", ondelete="SET NULL"), nullable=True, index=True
    )
    role_id = Column(
        String(26), ForeignKey("niam_workspace_roles.id", ondelete="SET NULL"), nullable=True
    )
    role_name = Column(String(100), nullable=False)

    token = Column(String(255), unique=True, nullable=False, index=True)
    status = Column(String(20), default="pending", nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)


class WorkspaceDelegation(IdentityBaseEntity):
    """Temporary authority delegation inside a single workspace."""

    __tablename__ = "niam_workspace_delegations"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    delegation_id = Column(String(100), unique=True, nullable=False, index=True)
    workspace_id = Column(
        String(26), ForeignKey("niam_workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    delegated_from_person_id = Column(
        String(26), ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    delegated_to_person_id = Column(
        String(26), ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    permissions = Column(JSON, nullable=False)

    status = Column(String(20), default="active", nullable=False, index=True)
    start_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    end_at = Column(DateTime(timezone=True), nullable=True)
    revoked_by = Column(
        String(26), ForeignKey("niam_persons.id", ondelete="SET NULL"), nullable=True
    )
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
