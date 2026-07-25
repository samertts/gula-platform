from __future__ import annotations

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from app.identity.base import IdentityBaseEntity


class EnterprisePortal(IdentityBaseEntity):
    __tablename__ = "niam_admin_portals"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    portal_id = Column(String(100), unique=True, nullable=False, index=True)
    organization_id = Column(
        String(26),
        ForeignKey("niam_organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(300), nullable=False)
    portal_type = Column(String(20), nullable=False, index=True)
    features = Column(JSON, nullable=True)
    status = Column(String(20), default="active", nullable=False)
    created_by = Column(
        String(26), ForeignKey("niam_accounts.id", ondelete="SET NULL"), nullable=True
    )
    activated_at = Column(DateTime(timezone=True), nullable=True)
    last_access_at = Column(DateTime(timezone=True), nullable=True)
    settings = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)


class PortalBranch(IdentityBaseEntity):
    __tablename__ = "niam_admin_branches"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    branch_id = Column(String(100), unique=True, nullable=False, index=True)
    portal_id = Column(
        String(26),
        ForeignKey("niam_admin_portals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id = Column(
        String(26),
        ForeignKey("niam_organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name_en = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=False)
    address = Column(Text, nullable=True)
    phone = Column(String(30), nullable=True)
    email = Column(String(200), nullable=True)
    manager_person_id = Column(
        String(26), ForeignKey("niam_persons.id", ondelete="SET NULL"), nullable=True
    )
    status = Column(String(20), default="active", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


class PortalFacility(IdentityBaseEntity):
    __tablename__ = "niam_admin_facilities"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    facility_id = Column(String(100), unique=True, nullable=False, index=True)
    branch_id = Column(
        String(26),
        ForeignKey("niam_admin_branches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id = Column(
        String(26),
        ForeignKey("niam_organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name_en = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=False)
    facility_type = Column(String(50), nullable=False)
    license_number = Column(String(100), nullable=True)
    accreditation = Column(String(200), nullable=True)
    status = Column(String(20), default="active", nullable=False)
    contact = Column(JSON, nullable=True)
    address = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)


class PortalDepartment(IdentityBaseEntity):
    __tablename__ = "niam_admin_departments"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    dept_id = Column(String(100), unique=True, nullable=False, index=True)
    facility_id = Column(
        String(26),
        ForeignKey("niam_admin_facilities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name_en = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=False)
    dept_type = Column(String(50), nullable=True)
    head_person_id = Column(
        String(26), ForeignKey("niam_persons.id", ondelete="SET NULL"), nullable=True
    )
    status = Column(String(20), default="active", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


class PortalSubscription(IdentityBaseEntity):
    __tablename__ = "niam_admin_subscriptions"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    sub_id = Column(String(100), unique=True, nullable=False, index=True)
    organization_id = Column(
        String(26),
        ForeignKey("niam_organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_type = Column(String(50), nullable=False)
    features = Column(JSON, nullable=True)
    user_limit = Column(Integer, nullable=True)
    storage_limit = Column(Integer, nullable=True)
    api_call_limit = Column(Integer, nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=False)
    renewal_date = Column(DateTime(timezone=True), nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="trial", nullable=False)
    billing_cycle = Column(String(20), nullable=True)
    billing_amount = Column(Integer, nullable=True)
    currency = Column(String(3), default="IQD", nullable=True)
    payment_method = Column(String(50), nullable=True)
    auto_renew = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


class PortalAuditLog(IdentityBaseEntity):
    __tablename__ = "niam_admin_audit_logs"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    log_id = Column(String(100), unique=True, nullable=False, index=True)
    organization_id = Column(
        String(26),
        ForeignKey("niam_organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    portal_id = Column(
        String(26),
        ForeignKey("niam_admin_portals.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action = Column(String(100), nullable=False)
    performed_by = Column(
        String(26), ForeignKey("niam_accounts.id", ondelete="SET NULL"), nullable=True
    )
    target_type = Column(String(50), nullable=False)
    target_id = Column(String(100), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    outcome = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)


class FHIRConnection(IdentityBaseEntity):
    __tablename__ = "niam_admin_fhir_connections"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    conn_id = Column(String(100), unique=True, nullable=False, index=True)
    organization_id = Column(
        String(26),
        ForeignKey("niam_organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(200), nullable=False)
    fhir_version = Column(String(10), nullable=False)
    base_url = Column(String(500), nullable=False)
    auth_type = Column(String(20), nullable=False)
    credentials_encrypted = Column(Text, nullable=True)
    status = Column(String(20), default="inactive", nullable=False)
    last_test_at = Column(DateTime(timezone=True), nullable=True)
    last_test_result = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
