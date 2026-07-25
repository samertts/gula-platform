from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app._compat import UTC, StrEnum

from ..database import Base


class UserTypeEnum(StrEnum):
    citizen = "citizen"
    patient = "patient"
    guardian = "guardian"
    physician = "physician"
    specialist = "specialist"
    consultant = "consultant"
    surgeon = "surgeon"
    resident = "resident"
    intern = "intern"
    dentist = "dentist"
    pharmacist = "pharmacist"
    nurse = "nurse"
    lab_technician = "lab_technician"
    senior_lab_technician = "senior_lab_technician"
    pathologist = "pathologist"
    microbiologist = "microbiologist"
    radiologist = "radiologist"
    paramedic = "paramedic"
    receptionist = "receptionist"
    cashier = "cashier"
    accountant = "accountant"
    hospital_director = "hospital_director"
    lab_director = "lab_director"
    phc_director = "phc_director"
    governorate_director = "governorate_director"
    ministry_director = "ministry_director"
    system_administrator = "system_administrator"
    national_administrator = "national_administrator"
    auditor = "auditor"
    compliance_officer = "compliance_officer"
    researcher = "researcher"
    ai_operator = "ai_operator"
    service_account = "service_account"
    ai_agent = "ai_agent"
    iot_device = "iot_device"


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    permission_id = Column(String(100), unique=True, nullable=False, index=True)
    name_en = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    domain = Column(String(50), nullable=False, index=True)
    resource = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)
    risk_level = Column(String(20), nullable=False, default="low")
    is_sensitive = Column(Boolean, default=False)
    requires_mfa = Column(Boolean, default=False)
    requires_justification = Column(Boolean, default=False)
    is_audited = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(String(100), unique=True, nullable=False, index=True)
    name_en = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    level = Column(String(50), nullable=False, default="department")
    parent_role_id = Column(String(100), nullable=True, index=True)
    role_group_id = Column(String(100), nullable=True, index=True)
    is_temporary = Column(Boolean, default=False)
    is_delegatable = Column(Boolean, default=True)
    requires_mfa = Column(Boolean, default=False)
    max_duration_hours = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    version = Column(Integer, default=1)


class RolePermission(Base):
    __tablename__ = "role_permissions"

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(
        String(100), ForeignKey("roles.role_id", ondelete="CASCADE"), nullable=False, index=True,
    )
    permission_id = Column(
        String(100),
        ForeignKey("permissions.permission_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )


class RoleAssignment(Base):
    __tablename__ = "role_assignments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    role_id = Column(
        String(100), ForeignKey("roles.role_id", ondelete="CASCADE"), nullable=False, index=True,
    )
    organization_id = Column(
        Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True,
    )
    facility_id = Column(Integer, ForeignKey("facilities.id", ondelete="SET NULL"), nullable=True)
    department_id = Column(Integer, nullable=True)
    assigned_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_primary = Column(Boolean, default=False)
    is_delegated = Column(Boolean, default=False)
    delegation_id = Column(
        Integer, ForeignKey("delegations.id", ondelete="SET NULL"), nullable=True,
    )
    status = Column(String(20), default="active")

    user = relationship("User", back_populates="role_assignments", foreign_keys=[user_id])


class RoleGroup(Base):
    __tablename__ = "role_groups"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(String(100), unique=True, nullable=False, index=True)
    name_en = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    is_template = Column(Boolean, default=False)


class RoleGroupMember(Base):
    __tablename__ = "role_group_members"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(
        String(100),
        ForeignKey("role_groups.group_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role_id = Column(
        String(100), ForeignKey("roles.role_id", ondelete="CASCADE"), nullable=False, index=True,
    )


class Policy(Base):
    __tablename__ = "abac_policies"

    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(String(100), unique=True, nullable=False, index=True)
    name_en = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(20), nullable=False, default="1.0.0")
    status = Column(String(20), default="draft")
    effect = Column(String(10), nullable=False, default="deny")
    priority = Column(Integer, default=100)
    category = Column(String(50), nullable=True)
    target = Column(JSON, nullable=True)
    conditions = Column(JSON, nullable=True)
    obligations = Column(JSON, nullable=True)
    validity_start = Column(DateTime(timezone=True), nullable=True)
    validity_end = Column(DateTime(timezone=True), nullable=True)
    signature = Column(String(255), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    tags = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class FieldSecurity(Base):
    __tablename__ = "field_security"

    id = Column(Integer, primary_key=True, index=True)
    resource_type = Column(String(50), nullable=False, index=True)
    field_name = Column(String(100), nullable=False, index=True)
    default_level = Column(String(20), nullable=False, default="public")
    consent_required = Column(Boolean, default=False)
    encryption_required = Column(Boolean, default=False)
    masking_pattern = Column(String(100), nullable=True)
    audit_access = Column(Boolean, default=True)
    purpose_restricted = Column(JSON, nullable=True)
    levels_by_role = Column(JSON, nullable=True)
    levels_by_org_type = Column(JSON, nullable=True)


class Delegation(Base):
    __tablename__ = "delegations"

    id = Column(Integer, primary_key=True, index=True)
    delegator_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    delegate_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    role_id = Column(String(100), ForeignKey("roles.role_id", ondelete="CASCADE"), nullable=False)
    delegation_type = Column(String(30), nullable=False)
    scope = Column(JSON, nullable=True)
    reason = Column(Text, nullable=True)
    starts_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), default="active")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


class BreakGlassSession(Base):
    __tablename__ = "break_glass_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    emergency_category = Column(String(50), nullable=False)
    justification = Column(Text, nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="SET NULL"), nullable=True)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    deactivated_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="active")
    reviewed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    review_status = Column(String(20), nullable=True)
    review_notes = Column(Text, nullable=True)


class AuthorizationAudit(Base):
    __tablename__ = "authorization_audit"

    id = Column(Integer, primary_key=True, index=True)
    decision_id = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True,
    )
    user_role = Column(String(100), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(100), nullable=True, index=True)
    decision = Column(String(20), nullable=False)
    policies_applied = Column(JSON, nullable=True)
    policy_engine = Column(String(20), nullable=True)
    context = Column(JSON, nullable=True)
    risk_score = Column(Float, nullable=True)
    justification = Column(Text, nullable=True)
    is_emergency = Column(Boolean, default=False)
    delegation_id = Column(
        Integer, ForeignKey("delegations.id", ondelete="SET NULL"), nullable=True,
    )
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
