from __future__ import annotations

from enum import StrEnum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from app.identity.base import IdentityBaseEntity


class CatalogStatus(StrEnum):
    active = "active"
    disabled = "disabled"
    deprecated = "deprecated"


class PermissionSensitivity(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class RoleScopeType(StrEnum):
    organization = "organization"
    facility = "facility"
    department = "department"
    unit = "unit"
    workspace = "workspace"


class RoleAssignmentStatus(StrEnum):
    pending = "pending"
    active = "active"
    suspended = "suspended"
    expired = "expired"
    revoked = "revoked"


class Role(IdentityBaseEntity):
    __tablename__ = "niam_roles"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    role_key = Column(String(120), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    scope_type = Column(String(30), nullable=False, index=True)
    status = Column(String(30), nullable=False, default=CatalogStatus.active.value, index=True)
    is_system = Column(Boolean, nullable=False, default=False)
    version = Column(Integer, nullable=False, default=1)


class Permission(IdentityBaseEntity):
    __tablename__ = "niam_permissions"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    permission_key = Column(String(160), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    resource = Column(String(120), nullable=False, index=True)
    action = Column(String(80), nullable=False, index=True)
    sensitivity = Column(String(30), nullable=False, default=PermissionSensitivity.medium.value)
    status = Column(String(30), nullable=False, default=CatalogStatus.active.value, index=True)
    version = Column(Integer, nullable=False, default=1)


class RolePermission(IdentityBaseEntity):
    __tablename__ = "niam_role_permissions"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_niam_role_permissions_relation"),
    )

    role_id = Column(String(26), ForeignKey("niam_roles.id", ondelete="CASCADE"), nullable=False, index=True)
    permission_id = Column(String(26), ForeignKey("niam_permissions.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(30), nullable=False, default=CatalogStatus.active.value)
    created_by = Column(String(26), ForeignKey("niam_accounts.id", ondelete="SET NULL"), nullable=True)


class RoleAssignment(IdentityBaseEntity):
    __tablename__ = "niam_role_assignments"
    __table_args__ = (
        UniqueConstraint("assignment_key", name="uq_niam_role_assignments_key"),
    )

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    assignment_key = Column(String(768), nullable=False, index=True)
    account_id = Column(String(26), ForeignKey("niam_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    membership_id = Column(String(26), ForeignKey("niam_memberships.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(String(26), ForeignKey("niam_roles.id", ondelete="RESTRICT"), nullable=False, index=True)
    organization_id = Column(String(26), ForeignKey("niam_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    facility_id = Column(String(26), ForeignKey("niam_admin_facilities.id", ondelete="SET NULL"), nullable=True, index=True)
    department_id = Column(String(26), ForeignKey("niam_admin_departments.id", ondelete="SET NULL"), nullable=True, index=True)
    unit_id = Column(String(26), ForeignKey("niam_admin_units.id", ondelete="SET NULL"), nullable=True, index=True)
    workspace_id = Column(String(26), ForeignKey("niam_workspaces.id", ondelete="SET NULL"), nullable=True, index=True)
    scope_type = Column(String(30), nullable=False, index=True)
    status = Column(String(30), nullable=False, default=RoleAssignmentStatus.pending.value, index=True)
    assigned_by = Column(String(26), ForeignKey("niam_accounts.id", ondelete="SET NULL"), nullable=True)
    activated_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revocation_reason = Column(Text, nullable=True)
    version = Column(Integer, nullable=False, default=1)
