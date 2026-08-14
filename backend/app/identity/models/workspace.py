from __future__ import annotations

from enum import StrEnum

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String

from app.identity.base import IdentityBaseEntity


class WorkspaceType(StrEnum):
    citizen = "citizen"
    professional = "professional"
    organization = "organization"
    facility = "facility"
    department = "department"
    administrative = "administrative"
    government = "government"
    audit = "audit"
    security = "security"
    support = "support"


class WorkspaceStatus(StrEnum):
    provisioning = "provisioning"
    active = "active"
    restricted = "restricted"
    suspended = "suspended"
    archived = "archived"
    deactivated = "deactivated"


WORKSPACE_TYPES: tuple[str, ...] = tuple(item.value for item in WorkspaceType)


class Workspace(IdentityBaseEntity):
    __tablename__ = "niam_workspaces"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    workspace_key = Column(String(255), unique=True, nullable=False, index=True)
    workspace_type = Column(String(30), nullable=False, index=True)
    name = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=True)
    status = Column(String(30), nullable=False, default=WorkspaceStatus.provisioning.value, index=True)

    owner_account_id = Column(String(26), ForeignKey("niam_accounts.id", ondelete="SET NULL"), nullable=True, index=True)
    organization_id = Column(String(26), ForeignKey("niam_organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    facility_id = Column(String(26), nullable=True, index=True)
    department_id = Column(String(26), nullable=True, index=True)
    professional_type = Column(String(60), nullable=True, index=True)
    provisioned_by = Column(String(26), ForeignKey("niam_accounts.id", ondelete="SET NULL"), nullable=True)
    is_personal = Column(Boolean, nullable=False, default=False, index=True)
    version = Column(Integer, nullable=False, default=1)


class WorkspaceSessionContext(IdentityBaseEntity):
    __tablename__ = "niam_workspace_contexts"

    session_id = Column(String(26), ForeignKey("niam_sessions.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    account_id = Column(String(26), ForeignKey("niam_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    identity_id = Column(String(26), ForeignKey("niam_identities.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(String(26), ForeignKey("niam_workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=True)
