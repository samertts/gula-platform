from __future__ import annotations

from enum import StrEnum

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, String, Text

from app.identity.base import IdentityBaseEntity


class OrganizationStatus(StrEnum):
    draft = "draft"
    pending_verification = "pending_verification"
    pending_approval = "pending_approval"
    active = "active"
    suspended = "suspended"
    rejected = "rejected"
    deactivated = "deactivated"
    archived = "archived"


class RepresentativeStatus(StrEnum):
    pending = "pending"
    active = "active"
    suspended = "suspended"
    revoked = "revoked"
    expired = "expired"


class OwnershipStatus(StrEnum):
    pending = "pending"
    active = "active"
    ended = "ended"
    revoked = "revoked"


ORGANIZATION_TYPE_CATEGORIES: dict[str, tuple[str, ...]] = {
    "government": ("government", "ministry", "authority", "directorate", "government_health_institution", "public_hospital", "primary_health_center"),
    "private_health": ("private_hospital", "laboratory", "pharmacy", "radiology_center", "clinic", "medical_center"),
    "professional": ("union", "syndicate", "professional_association", "professional_body"),
    "academic": ("university", "college", "institute", "research_center"),
    "commercial": ("company", "medical_supplier", "technology_provider", "integration_provider"),
    "non_profit": ("organization", "foundation", "ngo"),
}


class NIAMAdminBranch(IdentityBaseEntity):
    __tablename__ = "niam_admin_branches"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    branch_id = Column(String(100), unique=True, nullable=False, index=True)
    portal_id = Column(String(26), nullable=False, index=True)
    organization_id = Column(String(26), ForeignKey("niam_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name_en = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=False)
    address = Column(Text, nullable=True)
    phone = Column(String(30), nullable=True)
    email = Column(String(200), nullable=True)
    manager_person_id = Column(String(26), ForeignKey("niam_persons.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(20), nullable=False, default=OrganizationStatus.draft.value)
    is_active = Column(Boolean, nullable=False, default=True)


class NIAMAdminFacility(IdentityBaseEntity):
    __tablename__ = "niam_admin_facilities"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    facility_id = Column(String(100), unique=True, nullable=False, index=True)
    branch_id = Column(String(26), ForeignKey("niam_admin_branches.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(String(26), ForeignKey("niam_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name_en = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=False)
    facility_type = Column(String(50), nullable=False, index=True)
    license_number = Column(String(100), nullable=True)
    accreditation = Column(String(200), nullable=True)
    status = Column(String(20), nullable=False, default=OrganizationStatus.draft.value)
    contact = Column(JSON, nullable=True)
    address = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)


class NIAMAdminDepartment(IdentityBaseEntity):
    __tablename__ = "niam_admin_departments"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    dept_id = Column(String(100), unique=True, nullable=False, index=True)
    facility_id = Column(String(26), ForeignKey("niam_admin_facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    name_en = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=False)
    dept_type = Column(String(50), nullable=True)
    head_person_id = Column(String(26), ForeignKey("niam_persons.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(20), nullable=False, default=OrganizationStatus.draft.value)
    is_active = Column(Boolean, nullable=False, default=True)


class NIAMAdminUnit(IdentityBaseEntity):
    __tablename__ = "niam_admin_units"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    unit_id = Column(String(100), unique=True, nullable=False, index=True)
    department_id = Column(String(26), ForeignKey("niam_admin_departments.id", ondelete="CASCADE"), nullable=False, index=True)
    name_en = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=False)
    unit_type = Column(String(50), nullable=True)
    status = Column(String(20), nullable=False, default=OrganizationStatus.draft.value)
    is_active = Column(Boolean, nullable=False, default=True)


class OrganizationRepresentative(IdentityBaseEntity):
    __tablename__ = "niam_organization_representatives"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    organization_id = Column(String(26), ForeignKey("niam_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(String(26), ForeignKey("niam_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default=RepresentativeStatus.pending.value)
    valid_from = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    appointed_by = Column(String(26), ForeignKey("niam_accounts.id", ondelete="SET NULL"), nullable=True)
    appointment_reference = Column(String(255), nullable=True)
    is_primary = Column(Boolean, nullable=False, default=False)


class OrganizationOwnership(IdentityBaseEntity):
    __tablename__ = "niam_organization_ownerships"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    organization_id = Column(String(26), ForeignKey("niam_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(String(26), ForeignKey("niam_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default=OwnershipStatus.pending.value)
    valid_from = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    authority_reference = Column(String(255), nullable=True)
    confirmation_hash = Column(String(64), nullable=True)
    is_primary = Column(Boolean, nullable=False, default=False)
