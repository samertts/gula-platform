"""Wave 03 — institutional boundary and delegation fail-closed conformance.

Synthetic fixtures only. These tests exercise the already-integrated canonical
authority primitives; they add no production behavior and mint no real
identifiers. They assert that organization, facility, department and unit
boundaries fail closed, and that guardian/delegation/consent never widen scope.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from types import SimpleNamespace

import pytest
from app._compat import UTC
from app.identity.services.authorization_decision import (
    AuthorizationDecisionService,
    AuthorizationReason,
    AuthorizationRequest,
)
from app.identity.services.canonical_audit import CanonicalAuditService
from app.identity.services.consent_service_v2 import NiamConsentError, NiamConsentService
from app.identity.services.delegation_service import DelegationService
from app.identity.services.phi_permission_map import (
    PhiPermissionUnresolved,
    require_phi_permission,
    resolve_phi_permission,
)
from app.identity.services.verified_guardian_guard import (
    evaluate_guardian_access,
)

_TODAY = date(2026, 11, 24)
_NOW = datetime(2026, 11, 24, 12, 0, tzinfo=UTC)


# ── Organization / facility / directorate boundaries ─────────────────────────


def _request(**overrides):
    values = dict(
        subject_account_id="ACCOUNT-1",
        action="read",
        resource_type="patient_record",
        resource_id="PATIENT-1",
        permission_key="patient_record.read",
        organization_id="ORG-A",
        facility_id="FACILITY-A",
        department_id="DEPT-A",
        unit_id=None,
        workspace_id=None,
        resource_context={
            "exists": True,
            "organization_id": "ORG-A",
            "facility_id": "FACILITY-A",
            "department_id": "DEPT-A",
        },
    )
    values.update(overrides)
    return AuthorizationRequest(**values)


def _membership(**overrides):
    values = dict(
        organization_id="ORG-A",
        facility_id="FACILITY-A",
        department_id="DEPT-A",
        unit_id=None,
        workspace_id=None,
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def test_cross_facility_access_is_denied():
    result = AuthorizationDecisionService._check_scope(
        _request(facility_id="FACILITY-B", resource_context={
            "exists": True, "organization_id": "ORG-A", "facility_id": "FACILITY-B",
        }),
        _membership(),
    )
    assert result is AuthorizationReason.scope_mismatch


def test_cross_directorate_access_is_denied():
    # Directorates are represented by distinct organization resources; a
    # membership in one directorate must not authorize another directorate.
    result = AuthorizationDecisionService._check_scope(
        _request(organization_id="ORG-B", resource_context={
            "exists": True, "organization_id": "ORG-B", "facility_id": "FACILITY-B",
        }),
        _membership(),
    )
    assert result is AuthorizationReason.cross_tenant_denied


def test_cross_workspace_access_is_denied():
    result = AuthorizationDecisionService._check_scope(
        _request(workspace_id="WORKSPACE-B", resource_context={
            "exists": True, "organization_id": "ORG-A", "facility_id": "FACILITY-A",
        }),
        _membership(workspace_id="WORKSPACE-A"),
    )
    assert result is AuthorizationReason.workspace_boundary_denied


def test_in_scope_access_passes_boundary_checks():
    assert AuthorizationDecisionService._check_scope(_request(), _membership()) is None
    assert AuthorizationDecisionService._check_resource_context(_request()) is None


def test_resource_context_facility_mismatch_is_denied():
    result = AuthorizationDecisionService._check_resource_context(
        _request(resource_context={
            "exists": True, "organization_id": "ORG-A", "facility_id": "FACILITY-B",
        })
    )
    assert result is AuthorizationReason.scope_mismatch


def test_blank_scope_strings_fail_closed():
    assert (
        AuthorizationDecisionService._check_scope(
            _request(facility_id=" "),
            _membership(facility_id=" "),
        )
        is AuthorizationReason.scope_mismatch
    )
    assert (
        AuthorizationDecisionService._check_scope(
            _request(workspace_id="WORKSPACE-A"),
            _membership(workspace_id="   "),
        )
        is AuthorizationReason.workspace_boundary_denied
    )
    assert (
        AuthorizationDecisionService._check_resource_context(
            _request(facility_id=" ", resource_context={"exists": True})
        )
        is AuthorizationReason.scope_mismatch
    )


def test_explicit_null_resource_scope_fails_closed_when_request_asserts_scope():
    assert (
        AuthorizationDecisionService._check_scope(
            _request(
                facility_id="FACILITY-A",
                resource_context={
                    "exists": True, "organization_id": "ORG-A", "facility_id": None,
                },
            ),
            _membership(),
        )
        is AuthorizationReason.scope_mismatch
    )
    assert (
        AuthorizationDecisionService._check_resource_context(
            _request(
                facility_id="FACILITY-A",
                resource_context={
                    "exists": True, "organization_id": "ORG-A", "facility_id": None,
                },
            )
        )
        is AuthorizationReason.scope_mismatch
    )
    assert (
        AuthorizationDecisionService._check_resource_context(
            _request(
                organization_id="ORG-A",
                resource_context={"exists": True, "organization_id": None},
            )
        )
        is AuthorizationReason.cross_tenant_denied
    )


def test_unresolved_resource_is_denied():
    result = AuthorizationDecisionService._check_resource_context(
        _request(resource_context={"exists": False})
    )
    assert result is AuthorizationReason.resource_unresolved


# ── Delegation scope containment ─────────────────────────────────────────────


def _scope(facility=None, department=None, unit=None, workspace=None):
    return {
        "facility_id": facility,
        "department_id": department,
        "unit_id": unit,
        "workspace_id": workspace,
    }


def test_delegation_cannot_widen_facility_scope():
    holder = SimpleNamespace(facility_id="FACILITY-A", department_id="DEPT-A", unit_id=None, workspace_id=None)
    assert DelegationService._scope_contains(
        holder, _scope(facility="FACILITY-B", department="DEPT-A")
    ) is False
    assert DelegationService._scope_contains(
        holder, _scope(facility="FACILITY-A", department="DEPT-A")
    ) is True


def test_delegation_cannot_widen_department_or_unit_scope():
    holder = SimpleNamespace(facility_id="FACILITY-A", department_id="DEPT-A", unit_id="UNIT-A", workspace_id=None)
    assert DelegationService._scope_contains(
        holder, _scope(facility="FACILITY-A", department="DEPT-B", unit="UNIT-A")
    ) is False
    assert DelegationService._scope_contains(
        holder, _scope(facility="FACILITY-A", department="DEPT-A", unit="UNIT-B")
    ) is False


def test_unscoped_holder_may_delegate_any_single_scope_value():
    holder = SimpleNamespace(facility_id=None, department_id=None, unit_id=None, workspace_id=None)
    assert DelegationService._scope_contains(holder, _scope(facility="FACILITY-B")) is True


# ── Guardian / minor access ──────────────────────────────────────────────────


def _minor(dob=date(2015, 5, 20)):
    return SimpleNamespace(
        id="CITIZEN-MINOR",
        date_of_birth=dob,
        national_id_hash=None,
        name_blocking_key="BLOCK-A",
        merged_into_id=None,
        is_deceased=False,
        identity_status=SimpleNamespace(value="active"),
    )


def _guardian_relationship(**overrides):
    values = dict(
        id="REL-1",
        relationship_type="guardian",
        verified_at=datetime(2026, 1, 1, tzinfo=UTC),
        purpose="guardian_access",
        metadata_={"guardian_type": "parent", "source_verified": True},
        is_active_at=lambda now=None: True,
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def test_verified_guardian_may_read_minor_record():
    decision = evaluate_guardian_access(
        subject=_minor(), relationship=_guardian_relationship(),
        action="read", today=_TODAY, now=_NOW,
    )
    assert decision.allowed is True
    assert decision.reason == "verified_guardian_access"


def test_adult_has_no_guardian_authority():
    decision = evaluate_guardian_access(
        subject=_minor(dob=date(2000, 1, 1)), relationship=_guardian_relationship(),
        action="read", today=_TODAY, now=_NOW,
    )
    assert decision.allowed is False
    assert decision.reason == "guardian_authority_ended"


def test_unverified_guardian_is_denied():
    decision = evaluate_guardian_access(
        subject=_minor(),
        relationship=_guardian_relationship(verified_at=None),
        action="read", today=_TODAY, now=_NOW,
    )
    assert decision.allowed is False
    assert decision.reason == "guardian_relationship_unverified"


def test_guardian_export_action_is_denied():
    decision = evaluate_guardian_access(
        subject=_minor(), relationship=_guardian_relationship(),
        action="export", today=_TODAY, now=_NOW,
    )
    assert decision.allowed is False
    assert decision.reason == "action_not_permitted_for_guardian"


def test_merged_subject_is_not_linkable():
    subject = _minor()
    subject.merged_into_id = "CITIZEN-OTHER"
    decision = evaluate_guardian_access(
        subject=subject, relationship=_guardian_relationship(),
        action="read", today=_TODAY, now=_NOW,
    )
    assert decision.allowed is False
    assert decision.reason == "subject_not_linkable"


# ── Per-action PHI fail-closed ───────────────────────────────────────────────


def test_phi_permission_is_exact_per_action():
    assert require_phi_permission("patient_record", "read") == "patient_record.read"
    assert require_phi_permission("lab_result", "export") == "lab_result.export"
    assert resolve_phi_permission("patient_record", "administrative") == "patient_record.administrative"


def test_unmapped_phi_action_fails_closed():
    assert resolve_phi_permission("patient_record", "teleport") is None
    with pytest.raises(PhiPermissionUnresolved):
        require_phi_permission("patient_record", "teleport")


# ── Consent enforcement ──────────────────────────────────────────────────────


def test_empty_consent_scope_is_rejected():
    with pytest.raises(NiamConsentError):
        NiamConsentService._validate_scope({})


def test_expired_consent_is_rejected():
    with pytest.raises(NiamConsentError):
        NiamConsentService._validate_expiry(datetime.now(UTC) - timedelta(minutes=1))


def test_overlong_consent_is_rejected():
    with pytest.raises(NiamConsentError):
        NiamConsentService._validate_expiry(datetime.now(UTC) + timedelta(hours=73))


def test_valid_consent_scope_and_expiry_are_accepted():
    assert NiamConsentService._validate_scope({"purpose": "TREATMENT"}) == {"purpose": "TREATMENT"}
    accepted = NiamConsentService._validate_expiry(datetime.now(UTC) + timedelta(hours=1))
    assert accepted.tzinfo is not None


# ── Audit integrity ──────────────────────────────────────────────────────────


def _audit_entry(**overrides):
    values = dict(
        action="clinical_record.read",
        actor_id="ACCOUNT-1",
        actor_identity_id="IDENTITY-1",
        actor_type="account",
        category="clinical",
        changes={},
        context={},
        correlation_id="CORR-1",
        data_classification="phi",
        decision="allow",
        department_id="DEPT-A",
        event_type="ClinicalRecordRead",
        event_version="2",
        facility_id="FACILITY-A",
        id="EVENT-1",
        extra_data={},
        organization_id="ORG-A",
        outcome="success",
        previous_hash="0" * 64,
        reason_code="ALLOWED",
        request_id="REQ-1",
        session_id="SESSION-1",
        source="integration",
        target_id="PATIENT-1",
        target_type="patient_record",
        workspace_id=None,
        occurred_at=_NOW,
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def test_audit_hash_is_deterministic_and_changes_with_content():
    first = CanonicalAuditService._hash(_audit_entry())
    assert CanonicalAuditService._hash(_audit_entry()) == first
    changed = CanonicalAuditService._hash(_audit_entry(outcome="denied"))
    assert changed != first


def test_audit_hash_redacts_sensitive_context():
    plain = CanonicalAuditService._hash(_audit_entry(context={"password": "synthetic-secret"}))
    redacted = CanonicalAuditService._hash(_audit_entry(context={"password": "another-secret"}))
    assert plain == redacted
