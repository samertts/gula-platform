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


class MembershipRelationshipType(StrEnum):
    employee = "employee"
    professional = "professional"
    owner = "owner"
    authorized_representative = "authorized_representative"
    administrator = "administrator"
    manager = "manager"
    contractor = "contractor"
    consultant = "consultant"
    volunteer = "volunteer"
    student = "student"
    researcher = "researcher"
    auditor = "auditor"
    support = "support"
    member = "member"
    affiliate = "affiliate"


class MembershipScopeType(StrEnum):
    organization = "organization"
    facility = "facility"
    department = "department"
    unit = "unit"
    workspace = "workspace"


class MembershipStatus(StrEnum):
    pending = "pending"
    invited = "invited"
    active = "active"
    suspended = "suspended"
    expired = "expired"
    revoked = "revoked"
    rejected = "rejected"
    deactivated = "deactivated"


class MembershipSource(StrEnum):
    invitation = "invitation"
    application = "application"
    administrative_provisioning = "administrative_provisioning"
    verified_professional_link = "verified_professional_link"
    authorized_representative_assignment = "authorized_representative_assignment"


class InvitationStatus(StrEnum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    revoked = "revoked"
    expired = "expired"


class MembershipApplicationStatus(StrEnum):
    draft = "draft"
    submitted = "submitted"
    under_review = "under_review"
    approved = "approved"
    rejected = "rejected"
    cancelled = "cancelled"
    expired = "expired"


class Membership(IdentityBaseEntity):
    __tablename__ = "niam_memberships"
    __table_args__ = (
        UniqueConstraint("membership_key", name="uq_niam_memberships_key"),
    )

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    membership_key = Column(String(768), nullable=False, index=True)
    account_id = Column(String(26), ForeignKey("niam_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    identity_id = Column(String(26), ForeignKey("niam_identities.id", ondelete="SET NULL"), nullable=True, index=True)
    organization_id = Column(String(26), ForeignKey("niam_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    facility_id = Column(String(26), ForeignKey("niam_admin_facilities.id", ondelete="SET NULL"), nullable=True, index=True)
    department_id = Column(String(26), ForeignKey("niam_admin_departments.id", ondelete="SET NULL"), nullable=True, index=True)
    unit_id = Column(String(26), ForeignKey("niam_admin_units.id", ondelete="SET NULL"), nullable=True, index=True)
    workspace_id = Column(String(26), ForeignKey("niam_workspaces.id", ondelete="SET NULL"), nullable=True, index=True)
    relationship_type = Column(String(50), nullable=False, index=True)
    scope_type = Column(String(30), nullable=False, index=True)
    status = Column(String(30), nullable=False, default=MembershipStatus.pending.value, index=True)
    source = Column(String(50), nullable=False)
    created_by = Column(String(26), ForeignKey("niam_accounts.id", ondelete="SET NULL"), nullable=True)
    activated_by = Column(String(26), ForeignKey("niam_accounts.id", ondelete="SET NULL"), nullable=True)
    activated_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    suspended_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revocation_reason = Column(Text, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=True, index=True)


class MembershipInvitation(IdentityBaseEntity):
    __tablename__ = "niam_membership_invitations"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    invitation_key = Column(String(768), unique=True, nullable=False, index=True)
    token_hash = Column(String(128), unique=True, nullable=False, index=True)
    recipient_account_id = Column(String(26), ForeignKey("niam_accounts.id", ondelete="SET NULL"), nullable=True, index=True)
    organization_id = Column(String(26), ForeignKey("niam_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    facility_id = Column(String(26), ForeignKey("niam_admin_facilities.id", ondelete="SET NULL"), nullable=True)
    department_id = Column(String(26), ForeignKey("niam_admin_departments.id", ondelete="SET NULL"), nullable=True)
    unit_id = Column(String(26), ForeignKey("niam_admin_units.id", ondelete="SET NULL"), nullable=True)
    workspace_id = Column(String(26), ForeignKey("niam_workspaces.id", ondelete="SET NULL"), nullable=True)
    relationship_type = Column(String(50), nullable=False)
    scope_type = Column(String(30), nullable=False)
    status = Column(String(30), nullable=False, default=InvitationStatus.pending.value, index=True)
    membership_id = Column(String(26), ForeignKey("niam_memberships.id", ondelete="SET NULL"), nullable=True)
    created_by = Column(String(26), ForeignKey("niam_accounts.id", ondelete="SET NULL"), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    version = Column(Integer, nullable=False, default=1)


class MembershipApplication(IdentityBaseEntity):
    __tablename__ = "niam_membership_applications"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    application_key = Column(String(768), unique=True, nullable=False, index=True)
    account_id = Column(String(26), ForeignKey("niam_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    identity_id = Column(String(26), ForeignKey("niam_identities.id", ondelete="SET NULL"), nullable=True, index=True)
    organization_id = Column(String(26), ForeignKey("niam_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    facility_id = Column(String(26), ForeignKey("niam_admin_facilities.id", ondelete="SET NULL"), nullable=True)
    department_id = Column(String(26), ForeignKey("niam_admin_departments.id", ondelete="SET NULL"), nullable=True)
    unit_id = Column(String(26), ForeignKey("niam_admin_units.id", ondelete="SET NULL"), nullable=True)
    workspace_id = Column(String(26), ForeignKey("niam_workspaces.id", ondelete="SET NULL"), nullable=True)
    relationship_type = Column(String(50), nullable=False)
    scope_type = Column(String(30), nullable=False)
    status = Column(String(30), nullable=False, default=MembershipApplicationStatus.draft.value, index=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(String(26), ForeignKey("niam_accounts.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    version = Column(Integer, nullable=False, default=1)
