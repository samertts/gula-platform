"""Wave 05.3 authorization and audit boundary tests.

Synthetic roles and references only. The canonical Decision Engine remains the
only authorization decision source; these tests pin the fail-closed identity
constraints layered around an already-allow decision.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from app._compat import UTC
from app.identity.services.authorization_decision import (
    AuthorizationDecision,
    AuthorizationReason,
)
from app.national.services.identity_access import (
    IDENTITY_CREATED,
    IDENTITY_READ,
    WAVE053_AUDIT_OPERATIONS,
    IdentityAccessContext,
    IdentityAccessDeniedError,
    IdentityRole,
    assert_break_glass_window,
    assert_identity_access_v2,
    assert_minimum_necessary,
    build_wave053_audit_event,
)
from app.national.services.identity_governance import (
    IdentityAccessDeniedError as GovernanceAccessDenied,
)
from app.national.services.identity_governance import IdentityEvidenceError

NOW = datetime(2026, 11, 25, 7, 2, 38, tzinfo=UTC)
SYNTHETIC_GULA_ID = "199000000001"
SYNTHETIC_HASH = "a" * 64
SYNTHETIC_NID = "000000000001"


def _context(**overrides) -> IdentityAccessContext:
    values = {
        "decision": AuthorizationDecision.allow(),
        "role": IdentityRole.IDENTITY_REVIEWER,
        "actor_id": "reviewer-1",
        "organization_id": "ORG-SYNTHETIC",
        "facility_id": "FACILITY-SYNTHETIC",
        "purpose": "AUDIT",
        "action": IDENTITY_READ,
        "requested_fields": ("gula_citizen_identifier", "verification_state"),
        "gula_citizen_identifier": SYNTHETIC_GULA_ID,
        "national_id_hash": SYNTHETIC_HASH,
        "now": NOW,
    }
    values.update(overrides)
    return IdentityAccessContext(**values)


def test_canonical_deny_is_never_overridden() -> None:
    context = _context(
        decision=AuthorizationDecision.deny(AuthorizationReason.permission_missing),
    )
    with pytest.raises(IdentityAccessDeniedError, match="canonical authorization denied"):
        assert_identity_access_v2(context)


def test_unknown_operation_fails_closed() -> None:
    with pytest.raises(IdentityAccessDeniedError, match="unknown identity operation"):
        assert_identity_access_v2(_context(action="ANYTHING"))


def test_system_administrator_does_not_receive_general_identity_access() -> None:
    context = _context(role=IdentityRole.SYSTEM_ADMINISTRATOR, action=IDENTITY_READ)
    with pytest.raises(IdentityAccessDeniedError, match="role is not approved"):
        assert_identity_access_v2(context)


@pytest.mark.parametrize("role", list(IdentityRole))
def test_no_role_receives_raw_national_identifier(role: IdentityRole) -> None:
    with pytest.raises(GovernanceAccessDenied, match="raw identity fields are never released"):
        assert_minimum_necessary(role, ("national_id",))


def test_laboratory_technician_cannot_read_mother_name() -> None:
    context = _context(
        role=IdentityRole.LABORATORY_TECHNICIAN,
        requested_fields=("gula_citizen_identifier", "mother_name"),
    )
    with pytest.raises(GovernanceAccessDenied, match="outside the role"):
        assert_identity_access_v2(context)


def test_laboratory_technician_receives_only_minimum_necessary_fields() -> None:
    grant = assert_identity_access_v2(
        _context(
            role=IdentityRole.LABORATORY_TECHNICIAN,
            requested_fields=("gula_citizen_identifier", "birth_date", "facility_id"),
        ),
    )
    assert grant.allowed_fields == ("birth_date", "facility_id", "gula_citizen_identifier")
    assert grant.role is IdentityRole.LABORATORY_TECHNICIAN


def test_purpose_must_be_approved() -> None:
    with pytest.raises(IdentityAccessDeniedError, match="purpose is not approved"):
        assert_identity_access_v2(_context(purpose="UNDEFINED_PURPOSE"))


def test_consent_and_relationship_are_required_when_marked() -> None:
    with pytest.raises(IdentityAccessDeniedError, match="consent is required"):
        assert_identity_access_v2(_context(consent_required=True))
    with pytest.raises(IdentityAccessDeniedError, match="patient relationship is required"):
        assert_identity_access_v2(_context(relationship_required=True))


def test_valid_break_glass_is_bounded_and_audited() -> None:
    grant = assert_identity_access_v2(
        _context(
            role=IdentityRole.IDENTITY_REVIEWER,
            break_glass=True,
            break_glass_authorized=True,
            break_glass_reason="synthetic emergency",
            break_glass_expires_at=NOW + timedelta(minutes=10),
        ),
    )
    assert grant.break_glass is True
    assert grant.audit_event.decision == "success"
    assert "break_glass" in repr(grant.audit_event.metadata)


def test_target_must_be_a_gula_identifier_not_a_raw_nid() -> None:
    with pytest.raises(IdentityEvidenceError, match="birth-year prefix"):
        assert_identity_access_v2(_context(gula_citizen_identifier=SYNTHETIC_NID))


def test_actor_id_cannot_carry_raw_nid_into_audit() -> None:
    with pytest.raises(IdentityEvidenceError, match="full national ID"):
        assert_identity_access_v2(_context(actor_id=SYNTHETIC_NID))


def test_national_id_hash_must_be_a_digest_not_a_raw_nid() -> None:
    with pytest.raises(IdentityEvidenceError, match="64-character hex"):
        assert_identity_access_v2(_context(national_id_hash=SYNTHETIC_NID))


def test_patient_relationship_free_text_cannot_leak_raw_nid_into_audit() -> None:
    with pytest.raises(IdentityEvidenceError, match="full national ID"):
        assert_identity_access_v2(
            _context(
                relationship_required=True,
                patient_relationship=f"relative of {SYNTHETIC_NID}",
            ),
        )


def test_break_glass_reason_free_text_cannot_leak_raw_nid_into_audit() -> None:
    with pytest.raises(IdentityEvidenceError, match="full national ID"):
        assert_identity_access_v2(
            _context(
                break_glass=True,
                break_glass_authorized=True,
                break_glass_reason=f"emergency {SYNTHETIC_NID}",
                break_glass_expires_at=NOW + timedelta(minutes=10),
            ),
        )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"break_glass": True, "break_glass_authorized": False, "reason": "x", "expires_at": NOW},
        {"break_glass": True, "break_glass_authorized": True, "reason": None, "expires_at": NOW},
        {"break_glass": True, "break_glass_authorized": True, "reason": "x", "expires_at": None},
        {"break_glass": True, "break_glass_authorized": True, "reason": "x", "expires_at": NOW - timedelta(seconds=1)},
    ],
)
def test_broken_break_glass_windows_are_denied(kwargs) -> None:
    with pytest.raises(IdentityAccessDeniedError):
        assert_break_glass_window(
            break_glass=kwargs["break_glass"],
            authorized=kwargs["break_glass_authorized"],
            reason=kwargs["reason"],
            expires_at=kwargs["expires_at"],
            now=NOW,
        )


def test_required_audit_operations_are_covered() -> None:
    assert {
        IDENTITY_CREATED,
        IDENTITY_READ,
        "NID_VERIFICATION_REQUESTED",
        "NID_VERIFICATION_RESULT",
        "OCR_EXTRACTION",
        "NFC_EXTRACTION",
        "DOCUMENT_AUTHENTICITY_CHECK",
        "ORIGINAL_CARD_PRESENTED",
        "LIVE_CAPTURE_STARTED",
        "LIVE_CAPTURE_COMPLETED",
        "MRZ_EXTRACTION",
        "AUTHENTICITY_INSPECTION",
        "AUTHENTICITY_FAILURE",
        "COPY_REJECTION",
        "SUSPICIOUS_DOCUMENT",
        "DOCUMENT_REVIEW",
        "REVIEW_OUTCOME",
        "IDENTITY_APPROVAL",
        "IDENTITY_REJECTION",
        "UNAUTHORIZED_VERIFICATION_ATTEMPT",
        "MANUAL_OVERRIDE_ATTEMPT",
        "IDENTITY_CORRECTION",
        "IDENTITY_SUSPENSION",
        "IDENTITY_REACTIVATION",
        "PATIENT_LINKAGE",
        "LINKAGE_REVIEW",
        "LINKAGE_ROLLBACK",
        "DATA_EXPORT",
        "UNAUTHORIZED_ACCESS_ATTEMPT",
        "KEY_ACCESS",
        "KEY_ROTATION",
        "KEY_REVOCATION",
    } == WAVE053_AUDIT_OPERATIONS


@pytest.mark.parametrize("operation", sorted(WAVE053_AUDIT_OPERATIONS))
def test_audit_event_builder_covers_every_operation_without_raw_nid(operation: str) -> None:
    event = build_wave053_audit_event(
        operation=operation,
        actor_id="actor-1",
        purpose="AUDIT",
        facility_id="FACILITY-SYNTHETIC",
        organization_id="ORG-SYNTHETIC",
        gula_citizen_identifier=SYNTHETIC_GULA_ID,
        national_id_hash=SYNTHETIC_HASH,
        correlation_id="CORR-SYNTHETIC",
        raw_nid_for_check=SYNTHETIC_NID,
    )
    assert event.action == operation.lower()
    assert event.correlation_id == "CORR-SYNTHETIC"
    assert event.target_id == SYNTHETIC_GULA_ID
    assert SYNTHETIC_NID not in repr(event)


def test_audit_builder_scans_all_embedded_free_text_for_raw_nid() -> None:
    common = {
        "operation": IDENTITY_READ,
        "actor_id": "reviewer-1",
        "purpose": "AUDIT",
        "facility_id": "FACILITY-SYNTHETIC",
        "organization_id": "ORG-SYNTHETIC",
        "gula_citizen_identifier": SYNTHETIC_GULA_ID,
        "national_id_hash": SYNTHETIC_HASH,
    }
    with pytest.raises(IdentityEvidenceError, match="full national ID"):
        build_wave053_audit_event(**common, correlation_id=SYNTHETIC_NID)
    with pytest.raises(IdentityEvidenceError, match="full national ID"):
        build_wave053_audit_event(**common, metadata={"note": SYNTHETIC_NID})
    with pytest.raises(IdentityEvidenceError, match="full national ID"):
        build_wave053_audit_event(**{**common, "gula_citizen_identifier": f"GULA-{SYNTHETIC_NID}"})
    with pytest.raises(IdentityEvidenceError, match="full national ID"):
        build_wave053_audit_event(
            **common,
            metadata={"synthetic_count": int(f"1{SYNTHETIC_NID[1:]}")},
        )


def test_audit_metadata_rejects_raw_nid_key_and_value() -> None:
    with pytest.raises(IdentityEvidenceError, match="raw national ID is forbidden"):
        build_wave053_audit_event(
            operation=IDENTITY_READ,
            actor_id="actor-1",
            purpose="AUDIT",
            facility_id="FACILITY-SYNTHETIC",
            organization_id="ORG-SYNTHETIC",
            gula_citizen_identifier=SYNTHETIC_GULA_ID,
            national_id_hash=SYNTHETIC_HASH,
            metadata={"national_id": SYNTHETIC_NID},
            raw_nid_for_check=SYNTHETIC_NID,
        )
    with pytest.raises(IdentityEvidenceError):
        build_wave053_audit_event(
            operation=IDENTITY_READ,
            actor_id="actor-1",
            purpose="AUDIT",
            facility_id="FACILITY-SYNTHETIC",
            organization_id="ORG-SYNTHETIC",
            gula_citizen_identifier=SYNTHETIC_GULA_ID,
            national_id_hash=SYNTHETIC_HASH,
            metadata={"note": SYNTHETIC_NID},
            raw_nid_for_check=SYNTHETIC_NID,
        )


def test_registration_officer_can_create_identity_with_limited_fields() -> None:
    grant = assert_identity_access_v2(
        _context(
            role=IdentityRole.REGISTRATION_OFFICER,
            action=IDENTITY_CREATED,
            purpose="TREATMENT",
            requested_fields=("full_name", "gula_citizen_identifier"),
        ),
    )
    assert grant.action == IDENTITY_CREATED
    assert "national_id" not in grant.allowed_fields
