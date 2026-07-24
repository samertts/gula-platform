from __future__ import annotations

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from app.identity.base import IdentityBaseEntity


class EnterpriseRegistration(IdentityBaseEntity):
    __tablename__ = "niam_lifecycle_enterprise_reg"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    reg_id = Column(String(100), unique=True, nullable=False, index=True)
    organization_id = Column(String(26), ForeignKey("niam_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), default="draft", nullable=False, index=True)
    submitted_by = Column(String(100), nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    license_document = Column(Text, nullable=True)
    license_validated_at = Column(DateTime(timezone=True), nullable=True)
    license_validated_by = Column(String(100), nullable=True)
    inspection_report = Column(JSON, nullable=True)
    inspected_at = Column(DateTime(timezone=True), nullable=True)
    inspected_by = Column(String(100), nullable=True)
    risk_assessment = Column(JSON, nullable=True)
    risk_score = Column(Integer, nullable=True)
    risk_assessed_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    certificate_id = Column(String(100), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    current_step = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=False, nullable=False)


class EnterpriseRegistrationStep(IdentityBaseEntity):
    __tablename__ = "niam_lifecycle_enterprise_steps"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    step_id = Column(String(100), unique=True, nullable=False, index=True)
    reg_id = Column(String(26), ForeignKey("niam_lifecycle_enterprise_reg.id", ondelete="CASCADE"), nullable=False, index=True)
    step_name = Column(String(100), nullable=False)
    status = Column(String(30), default="pending", nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    performed_by = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    output = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=False, nullable=False)


class WorkforceRequest(IdentityBaseEntity):
    __tablename__ = "niam_lifecycle_workforce_requests"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    request_id = Column(String(100), unique=True, nullable=False, index=True)
    request_type = Column(String(50), nullable=False, index=True)
    requesting_org_id = Column(String(26), ForeignKey("niam_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_by = Column(String(100), nullable=True)
    person_id = Column(String(26), ForeignKey("niam_persons.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(50), default="draft", nullable=False, index=True)
    national_id_hash = Column(String(255), nullable=True)
    license_number = Column(String(100), nullable=True)
    board_registration = Column(String(100), nullable=True)
    employment_rules_check = Column(JSON, nullable=True)
    conflict_report = Column(JSON, nullable=True)
    restrictions = Column(JSON, nullable=True)
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    activated_at = Column(DateTime(timezone=True), nullable=True)
    suspension_reason = Column(Text, nullable=True)
    termination_reason = Column(Text, nullable=True)
    historical_preserved = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)


class GovernmentAppointment(IdentityBaseEntity):
    __tablename__ = "niam_lifecycle_gov_appointments"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    appointment_id = Column(String(100), unique=True, nullable=False, index=True)
    person_id = Column(String(26), ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(String(26), ForeignKey("niam_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    hr_reference = Column(String(100), unique=True, nullable=False, index=True)
    appointment_type = Column(String(30), nullable=False)
    position = Column(String(200), nullable=True)
    grade = Column(String(50), nullable=True)
    salary_scale = Column(String(50), nullable=True)
    department = Column(String(200), nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    hr_approved_by = Column(String(100), nullable=True)
    hr_approved_at = Column(DateTime(timezone=True), nullable=True)
    identity_created = Column(Boolean, default=False, nullable=False)
    credential_issued = Column(Boolean, default=False, nullable=False)
    account_activated = Column(Boolean, default=False, nullable=False)
    permissions_assigned = Column(Boolean, default=False, nullable=False)
    status = Column(String(30), default="draft", nullable=False, index=True)
    promotion_history = Column(JSON, nullable=True)
    transfer_history = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=False, nullable=False)


class CitizenLifecycle(IdentityBaseEntity):
    __tablename__ = "niam_lifecycle_citizen"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    citizen_id = Column(String(100), unique=True, nullable=False, index=True)
    person_id = Column(String(26), ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True)
    identity_id = Column(String(26), ForeignKey("niam_identities.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(30), default="registered", nullable=False, index=True)
    registration_date = Column(DateTime(timezone=True), nullable=True)
    otp_sent_at = Column(DateTime(timezone=True), nullable=True)
    otp_verified_at = Column(DateTime(timezone=True), nullable=True)
    identity_verified_at = Column(DateTime(timezone=True), nullable=True)
    health_id = Column(String(100), unique=True, nullable=True, index=True)
    guardian_person_id = Column(String(26), ForeignKey("niam_persons.id", ondelete="SET NULL"), nullable=True, index=True)
    family_tree = Column(JSON, nullable=True)
    consent_records = Column(JSON, nullable=True)
    emergency_contacts = Column(JSON, nullable=True)
    address_history = Column(JSON, nullable=True)
    document_verification = Column(JSON, nullable=True)
    self_service_enabled = Column(Boolean, default=False, nullable=False)
    last_recovery_at = Column(DateTime(timezone=True), nullable=True)
    deactivated_at = Column(DateTime(timezone=True), nullable=True)
    deactivation_reason = Column(Text, nullable=True)
    deceased_at = Column(DateTime(timezone=True), nullable=True)
    death_certificate_id = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=False, nullable=False)


class GuardianAccount(IdentityBaseEntity):
    __tablename__ = "niam_lifecycle_guardians"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    guardian_id = Column(String(100), unique=True, nullable=False, index=True)
    guardian_person_id = Column(String(26), ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True)
    dependent_person_id = Column(String(26), ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True)
    relationship = Column(String(50), nullable=False)
    guardian_type = Column(String(30), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    delegated_access = Column(JSON, nullable=True)
    consent_inheritance = Column(Boolean, default=False, nullable=False)
    status = Column(String(20), default="active", nullable=False, index=True)
    verified_by = Column(String(100), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    documents = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=False, nullable=False)


class FamilyLink(IdentityBaseEntity):
    __tablename__ = "niam_lifecycle_family_links"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    link_id = Column(String(100), unique=True, nullable=False, index=True)
    person_id = Column(String(26), ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True)
    relative_person_id = Column(String(26), ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True)
    relationship = Column(String(30), nullable=False)
    emergency_contact = Column(Boolean, default=False, nullable=False)
    consent_sharing = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)


class ConsentRecord(IdentityBaseEntity):
    __tablename__ = "niam_lifecycle_consents"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    consent_id = Column(String(100), unique=True, nullable=False, index=True)
    person_id = Column(String(26), ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True)
    consent_type = Column(String(50), nullable=False)
    granted_to = Column(String(26), ForeignKey("niam_organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    granted_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    scope = Column(JSON, nullable=True)
    terms = Column(Text, nullable=True)
    status = Column(String(20), default="active", nullable=False, index=True)
    is_active = Column(Boolean, default=False, nullable=False)
