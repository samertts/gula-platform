from __future__ import annotations

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
    account_created = "account_created"
    account_locked = "account_locked"
    account_unlocked = "account_unlocked"
    account_status_changed = "account_status_changed"
    account_suspended = "account_suspended"
    account_restored = "account_restored"
    account_deactivated = "account_deactivated"
    login_succeeded = "login_succeeded"
    login_failed = "login_failed"
    logout_succeeded = "logout_succeeded"
    account_password_changed = "account_password_changed"
    account_mfa_enabled = "account_mfa_enabled"
    account_mfa_disabled = "account_mfa_disabled"
    employment_created = "employment_created"
    employment_terminated = "employment_terminated"
    assignment_created = "assignment_created"
    assignment_revoked = "assignment_revoked"
    session_started = "session_started"
    session_terminated = "session_terminated"
    credential_created = "credential_created"
    credential_revoked = "credential_revoked"
    role_assigned = "role_assigned"
    role_revoked = "role_revoked"
    permission_granted = "permission_granted"
    permission_revoked = "permission_revoked"
    policy_created = "policy_created"
    policy_updated = "policy_updated"
    policy_enforced = "policy_enforced"
    policy_denied = "policy_denied"
    device_trusted = "device_trusted"
    device_revoked = "device_revoked"
    breach_detected = "breach_detected"
    organization_created = "organization_created"
    organization_updated = "organization_updated"
    organization_hierarchy_changed = "organization_hierarchy_changed"
    license_issued = "license_issued"
    license_suspended = "license_suspended"
    authorization_issued = "authorization_issued"
    authorization_renewed = "authorization_renewed"
    authorization_suspended = "authorization_suspended"
    authorization_revoked = "authorization_revoked"
    bootstrap_started = "bootstrap_started"
    bootstrap_completed = "bootstrap_completed"
    authority_created = "authority_created"
    authority_suspended = "authority_suspended"
    authority_boundary_enforced = "authority_boundary_enforced"
    authority_boundary_denied = "authority_boundary_denied"
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
    workspace_created = "workspace_created"
    workspace_updated = "workspace_updated"
    workspace_suspended = "workspace_suspended"
    workspace_closed = "workspace_closed"
    workspace_member_invited = "workspace_member_invited"
    workspace_member_joined = "workspace_member_joined"
    workspace_member_removed = "workspace_member_removed"
    workspace_role_created = "workspace_role_created"
    workspace_role_updated = "workspace_role_updated"
    workspace_role_assigned = "workspace_role_assigned"
    workspace_role_revoked = "workspace_role_revoked"
    workspace_selected = "workspace_selected"
    workspace_delegation_granted = "workspace_delegation_granted"
    workspace_delegation_revoked = "workspace_delegation_revoked"
    professional_registered = "professional_registered"
    professional_verified = "professional_verified"
    professional_suspended = "professional_suspended"
    professional_revoked = "professional_revoked"
    citizen_provider_registered = "citizen_provider_registered"
    citizen_identifier_verified = "citizen_identifier_verified"
    session_workspace_bound = "session_workspace_bound"
    session_workspace_unbound = "session_workspace_unbound"
    session_max_concurrent_enforced = "session_max_concurrent_enforced"


class IdentityAuditEntry(IdentityBaseEntity):
    __tablename__ = "niam_audit_entries"

    uuid = Column(String(36), unique=True, nullable=False, index=True)

    action = Column(String(50), nullable=False, index=True)
    actor_id = Column(String(36), nullable=True, index=True)
    actor_type = Column(String(30), nullable=True)

    target_type = Column(String(50), nullable=True, index=True)
    target_id = Column(String(36), nullable=True, index=True)

    changes = Column(JSON, nullable=True)
    extra_data = Column(JSON, nullable=True)
    context = Column(JSON, nullable=True)

    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(36), nullable=True)

    occurred_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True
    )
    organization_id = Column(String(36), nullable=True, index=True)

    entry_hash = Column(String(64), unique=True, nullable=True, index=True)
    previous_hash = Column(String(64), nullable=True, index=True)

    outcome = Column(String(20), default="success", nullable=False)
    error_message = Column(Text, nullable=True)
