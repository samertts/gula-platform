from __future__ import annotations

import uuid as _uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, String, Text

from app._compat import UTC, StrEnum
from app.identity.base import IdentityBaseEntity


class AuditAction(StrEnum):
    person_created = "person_created"
    person_updated = "person_updated"
    person_deactivated = "person_deactivated"
    identity_created = "identity_created"
    identity_verified = "identity_verified"
    identity_revoked = "identity_revoked"
    verification_started = "verification_started"
    verification_completed = "verification_completed"
    verification_failed = "verification_failed"
    verification_expired = "verification_expired"
    verification_revoked = "verification_revoked"
    identity_attribute_verified = "identity_attribute_verified"
    identity_attribute_corrected = "identity_attribute_corrected"
    identity_correction_requested = "identity_correction_requested"
    account_created = "account_created"
    account_activated = "account_activated"
    account_locked = "account_locked"
    account_unlocked = "account_unlocked"
    account_suspended = "account_suspended"
    account_disabled = "account_disabled"
    account_password_changed = "account_password_changed"
    account_mfa_enabled = "account_mfa_enabled"
    account_mfa_disabled = "account_mfa_disabled"
    employment_created = "employment_created"
    employment_terminated = "employment_terminated"
    assignment_created = "assignment_created"
    assignment_revoked = "assignment_revoked"
    session_started = "session_started"
    session_created = "session_created"
    session_terminated = "session_terminated"
    session_revoked = "session_revoked"
    login_success = "login_success"
    login_failure = "login_failure"
    logout = "logout"
    password_reset_requested = "password_reset_requested"
    password_reset_completed = "password_reset_completed"
    email_verified = "email_verified"
    phone_verified = "phone_verified"
    otp_requested = "otp_requested"
    otp_verified = "otp_verified"
    otp_failed = "otp_failed"
    session_refreshed = "session_refreshed"
    session_reuse_detected = "session_reuse_detected"
    credential_created = "credential_created"
    credential_revoked = "credential_revoked"
    role_assigned = "role_assigned"
    role_revoked = "role_revoked"
    permission_granted = "permission_granted"
    permission_revoked = "permission_revoked"
    role_created = "role_created"
    role_updated = "role_updated"
    role_disabled = "role_disabled"
    role_deprecated = "role_deprecated"
    permission_created = "permission_created"
    permission_updated = "permission_updated"
    permission_disabled = "permission_disabled"
    permission_deprecated = "permission_deprecated"
    role_permission_granted = "role_permission_granted"
    role_permission_revoked = "role_permission_revoked"
    role_assignment_created = "role_assignment_created"
    role_assignment_activated = "role_assignment_activated"
    role_assignment_suspended = "role_assignment_suspended"
    role_assignment_reactivated = "role_assignment_reactivated"
    role_assignment_revoked = "role_assignment_revoked"
    role_assignment_denied = "role_assignment_denied"
    permission_enforced = "permission_enforced"
    permission_denied = "permission_denied"
    authz_allow_sensitive = "AUTHZ_ALLOW_SENSITIVE"
    authz_deny = "AUTHZ_DENY"
    authz_policy_failure = "AUTHZ_POLICY_FAILURE"
    authz_cross_tenant_attempt = "AUTHZ_CROSS_TENANT_ATTEMPT"
    authz_privilege_escalation_attempt = "AUTHZ_PRIVILEGE_ESCALATION_ATTEMPT"
    authz_role_manipulation_attempt = "AUTHZ_ROLE_MANIPULATION_ATTEMPT"
    authz_resource_enumeration_attempt = "AUTHZ_RESOURCE_ENUMERATION_ATTEMPT"
    break_glass_used = "BREAK_GLASS_USED"
    step_up_required = "STEP_UP_REQUIRED"
    step_up_failed = "STEP_UP_FAILED"
    policy_created = "policy_created"
    policy_updated = "policy_updated"
    policy_enforced = "policy_enforced"
    policy_denied = "policy_denied"
    device_trusted = "device_trusted"
    device_revoked = "device_revoked"
    breach_detected = "breach_detected"
    organization_created = "organization_created"
    organization_updated = "organization_updated"
    organization_verification_started = "organization_verification_started"
    organization_verification_completed = "organization_verification_completed"
    organization_verification_rejected = "organization_verification_rejected"
    organization_activated = "organization_activated"
    organization_suspended = "organization_suspended"
    organization_representative_appointed = "organization_representative_appointed"
    membership_created = "membership_created"
    membership_invited = "membership_invited"
    membership_accepted = "membership_accepted"
    membership_rejected = "membership_rejected"
    membership_suspended = "membership_suspended"
    membership_reactivated = "membership_reactivated"
    membership_expired = "membership_expired"
    membership_revoked = "membership_revoked"
    membership_application_submitted = "membership_application_submitted"
    membership_application_approved = "membership_application_approved"
    membership_application_rejected = "membership_application_rejected"
    invitation_created = "invitation_created"
    invitation_accepted = "invitation_accepted"
    invitation_rejected = "invitation_rejected"
    invitation_revoked = "invitation_revoked"
    invitation_expired = "invitation_expired"
    workspace_created = "workspace_created"
    workspace_activated = "workspace_activated"
    workspace_restricted = "workspace_restricted"
    workspace_suspended = "workspace_suspended"
    workspace_archived = "workspace_archived"
    workspace_deactivated = "workspace_deactivated"
    workspace_switched = "workspace_switched"
    workspace_provisioning_failed = "workspace_provisioning_failed"
    license_issued = "license_issued"
    license_suspended = "license_suspended"
    bootstrap_started = "bootstrap_started"
    bootstrap_completed = "bootstrap_completed"
    authority_created = "authority_created"
    authority_suspended = "authority_suspended"
    council_created = "council_created"
    appeal_submitted = "appeal_submitted"
    appeal_decided = "appeal_decided"
    appeal_escalated = "appeal_escalated"
    suspension_created = "suspension_created"
    suspension_lifted = "suspension_lifted"
    restoration_requested = "restoration_requested"
    restoration_completed = "restoration_completed"
    registry_registered = "registry_registered"
    registry_verified = "registry_verified"
    professional_verification_started = "professional_verification_started"
    professional_verification_completed = "professional_verification_completed"
    professional_verification_revoked = "professional_verification_revoked"
    manual_review_started = "manual_review_started"
    manual_review_completed = "manual_review_completed"
    certification_issued = "certification_issued"
    certification_revoked = "certification_revoked"
    trust_framework_created = "trust_framework_created"
    trust_framework_activated = "trust_framework_activated"
    assurance_profile_assigned = "assurance_profile_assigned"
    assurance_profile_expired = "assurance_profile_expired"
    trust_anchor_registered = "trust_anchor_registered"
    trust_anchor_revoked = "trust_anchor_revoked"
    federation_trust_established = "federation_trust_established"
    federation_trust_terminated = "federation_trust_terminated"
    identity_proofing_verified = "identity_proofing_verified"
    identity_proofing_rejected = "identity_proofing_rejected"
    trust_evaluation_completed = "trust_evaluation_completed"
    enterprise_registration_started = "enterprise_registration_started"
    enterprise_registration_approved = "enterprise_registration_approved"
    enterprise_registration_rejected = "enterprise_registration_rejected"
    workforce_request_submitted = "workforce_request_submitted"
    workforce_request_approved = "workforce_request_approved"
    workforce_account_activated = "workforce_account_activated"
    workforce_terminated = "workforce_terminated"
    government_appointment_created = "government_appointment_created"
    government_appointment_activated = "government_appointment_activated"
    government_promotion = "government_promotion"
    government_transfer = "government_transfer"
    government_retirement = "government_retirement"
    citizen_registered = "citizen_registered"
    citizen_verified = "citizen_verified"
    citizen_deactivated = "citizen_deactivated"
    citizen_death_registered = "citizen_death_registered"
    guardianship_created = "guardianship_created"
    guardianship_terminated = "guardianship_terminated"
    consent_granted = "consent_granted"
    consent_revoked = "consent_revoked"
    federated_identity_linked = "federated_identity_linked"
    federated_identity_unlinked = "federated_identity_unlinked"
    certificate_issued = "certificate_issued"
    certificate_revoked = "certificate_revoked"
    certificate_rotated = "certificate_rotated"
    api_key_generated = "api_key_generated"
    api_key_revoked = "api_key_revoked"
    risk_event_detected = "risk_event_detected"
    mfa_challenged = "mfa_challenged"
    mfa_verified = "mfa_verified"
    mfa_failed = "mfa_failed"
    session_policy_enforced = "session_policy_enforced"
    session_terminated_by_policy = "session_terminated_by_policy"
    impossible_travel_detected = "impossible_travel_detected"
    credential_stuffing_detected = "credential_stuffing_detected"
    brute_force_detected = "brute_force_detected"
    device_attested = "device_attested"
    device_compromised = "device_compromised"
    workflow_started = "workflow_started"
    workflow_completed = "workflow_completed"
    workflow_approved = "workflow_approved"
    workflow_rejected = "workflow_rejected"
    notification_sent = "notification_sent"
    notification_delivered = "notification_delivered"
    compliance_check_passed = "compliance_check_passed"
    compliance_check_failed = "compliance_check_failed"
    portal_created = "portal_created"
    portal_suspended = "portal_suspended"
    subscription_created = "subscription_created"
    subscription_expired = "subscription_expired"
    fhir_connection_tested = "fhir_connection_tested"
    audit_chain_verified = "audit_chain_verified"
    audit_tamper_detected = "audit_tamper_detected"
    audit_event_read = "audit_event_read"
    audit_export_requested = "audit_export_requested"
    audit_integrity_verified = "audit_integrity_verified"
    consent_checked = "consent_checked"
    consent_withdrawn = "consent_withdrawn"
    security_incident_created = "security_incident_created"
    security_incident_status_changed = "security_incident_status_changed"
    security_alert_detected = "security_alert_detected"
    data_export_requested = "data_export_requested"


def _audit_entry_uuid() -> str:
    """The canonical uuid authority for `niam_audit_entries` (NR-045).

    The column is NOT NULL with no server default, and `IdentityBaseEntity`
    supplies `id`, `created_at` and `updated_at` but not `uuid`. `AuditService`
    (event_version 1) passed one explicitly; `CanonicalAuditService`
    (event_version 2) did not, so every v2 insert violated the constraint and
    the clinical gateway — which audits before it allows *and* before it denies
    — answered 503 to every request.

    Putting the default on the column makes one place authoritative for every
    writer of this table rather than adding a second generator beside v1's.
    `AuditService` still passes its own value, which takes precedence, so its
    behaviour is unchanged. `uuid` is deliberately absent from v2's
    `_canonical_payload`, so populating it cannot alter any entry hash, past or
    future.
    """
    return str(_uuid.uuid4())


class IdentityAuditEntry(IdentityBaseEntity):
    __tablename__ = "niam_audit_entries"

    uuid = Column(String(36), unique=True, nullable=False, index=True, default=_audit_entry_uuid)

    action = Column(String(120), nullable=False, index=True)
    event_type = Column(String(120), nullable=True, index=True)
    event_version = Column(String(20), nullable=False, default="1")
    category = Column(String(40), nullable=True, index=True)
    actor_id = Column(String(36), nullable=True, index=True)
    actor_identity_id = Column(String(26), nullable=True, index=True)
    actor_type = Column(String(30), nullable=True)

    target_type = Column(String(50), nullable=True, index=True)
    target_id = Column(String(36), nullable=True, index=True)
    facility_id = Column(String(26), nullable=True, index=True)
    department_id = Column(String(26), nullable=True, index=True)
    workspace_id = Column(String(26), nullable=True, index=True)
    decision = Column(String(20), nullable=True, index=True)
    reason_code = Column(String(120), nullable=True, index=True)
    request_id = Column(String(120), nullable=True, index=True)
    correlation_id = Column(String(120), nullable=True, index=True)
    source = Column(String(40), nullable=True, index=True)
    data_classification = Column(String(30), nullable=True, index=True)

    changes = Column(JSON, nullable=True)
    extra_data = Column(JSON, nullable=True)
    context = Column(JSON, nullable=True)

    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(36), nullable=True)

    occurred_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True)
    organization_id = Column(String(36), nullable=True, index=True)

    entry_hash = Column(String(64), unique=True, nullable=True, index=True)
    previous_hash = Column(String(64), nullable=True, index=True)

    outcome = Column(String(20), default="success", nullable=False)
    error_message = Column(Text, nullable=True)
