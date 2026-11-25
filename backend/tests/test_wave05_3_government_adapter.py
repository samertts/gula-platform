"""Wave 05.3 government verification adapter tests.

Synthetic adapter results only. No network call, credential, real authority,
public key, or government verification claim is created.
"""

from __future__ import annotations

import hashlib
from dataclasses import replace
from datetime import datetime, timedelta

import pytest
from app._compat import UTC
from app.gateways.base import DataTrustLevel
from app.national.services.government_verification import (
    ALL_VERIFICATION_STATUSES,
    AdapterPolicy,
    AdapterSecurityError,
    AuthorityRegistry,
    AuthorityRegistryEntry,
    AuthorityRegistryError,
    GovernmentVerificationError,
    NonceReplayGuard,
    SyntheticGovernmentVerificationAdapter,
    VerificationRequest,
    VerificationResponse,
    VerificationStatus,
    VerifiedAttribute,
    bounded_backoff_delay,
    decision_for_adapter_result,
    government_evidence_from_response,
    request_audit_event,
    unauthorized_attempt_audit_event,
)
from app.national.services.identity_governance import IdentityEvidenceError

NOW = datetime(2026, 11, 25, 7, 2, 38, tzinfo=UTC)
SYNTHETIC_NID = "000000000001"
SYNTHETIC_AUTHORITY = "SYNTHETIC-AUTHORITY-0001"


def _request(key: str = "idem-1", correlation: str = "CORR-0001") -> VerificationRequest:
    return VerificationRequest(
        correlation_id=correlation,
        idempotency_key=key,
        subject_reference="SUBJECT-REF-0001",
        national_id_hash=hashlib.sha256(SYNTHETIC_NID.encode()).hexdigest(),
        lookup_token="v1." + "b" * 64,  # pragma: allowlist secret
        purpose="REGISTRATION",
        actor="registration-officer",
        organization_id="ORG-SYNTHETIC",
        facility_id="FACILITY-SYNTHETIC",
        requested_at=NOW,
    )


def _authority(**overrides) -> AuthorityRegistryEntry:
    values = {
        "authority_id": SYNTHETIC_AUTHORITY,
        "organization": "SYNTHETIC-ORGANIZATION",
        "service_name": "SYNTHETIC-VERIFICATION-SERVICE",
        "trust_level": DataTrustLevel.NON_CRITICAL,
        "valid_from": NOW - timedelta(days=1),
        "valid_until": NOW + timedelta(days=1),
        "approval_reference": "SYNTHETIC-APPROVAL-0001",
        "public_key_reference": "SYNTHETIC-PUBLIC-KEY-REF-0001",
        "revocation_reference": None,
        "revoked": False,
        "synthetic": True,
    }
    values.update(overrides)
    return AuthorityRegistryEntry(**values)


def _registry() -> AuthorityRegistry:
    registry = AuthorityRegistry()
    registry.register(_authority())
    return registry


def test_all_required_statuses_are_defined() -> None:
    assert {
        VerificationStatus.VERIFIED,
        VerificationStatus.NOT_VERIFIED,
        VerificationStatus.NOT_FOUND,
        VerificationStatus.INDETERMINATE,
        VerificationStatus.TEMPORARILY_UNAVAILABLE,
        VerificationStatus.INVALID_REQUEST,
        VerificationStatus.AUTHORITY_UNAVAILABLE,
    } == ALL_VERIFICATION_STATUSES


def test_request_uses_opaque_references_and_rejects_raw_nid() -> None:
    request = _request()
    assert SYNTHETIC_NID not in repr(request)
    with pytest.raises(GovernmentVerificationError, match="raw national number"):
        VerificationRequest(
            **{**request.__dict__, "subject_reference": SYNTHETIC_NID},
        )


def test_request_rejects_non_hash_identifier_material() -> None:
    request = _request()
    with pytest.raises(GovernmentVerificationError, match="64-character hex"):
        VerificationRequest(**{**request.__dict__, "national_id_hash": SYNTHETIC_NID})


def test_request_rejects_raw_nid_as_lookup_token() -> None:
    request = _request()
    with pytest.raises(GovernmentVerificationError, match="versioned keyed HMAC"):
        VerificationRequest(**{**request.__dict__, "lookup_token": SYNTHETIC_NID})


def test_request_rejects_raw_nid_as_lookup_token_version() -> None:
    request = _request()
    long_version = f"v1{SYNTHETIC_NID[1:]}"
    with pytest.raises(GovernmentVerificationError, match="bounded versioned keyed HMAC"):
        VerificationRequest(
            **{**request.__dict__, "lookup_token": f"{long_version}.{'b' * 64}"},
        )


def test_policy_is_bounded() -> None:
    with pytest.raises(GovernmentVerificationError):
        AdapterPolicy(timeout_seconds=0)
    with pytest.raises(GovernmentVerificationError):
        AdapterPolicy(max_attempts=99)
    with pytest.raises(GovernmentVerificationError):
        AdapterPolicy(bounded_backoff_base_seconds=5, bounded_backoff_max_seconds=1)


def test_bounded_backoff_is_capped() -> None:
    policy = AdapterPolicy()
    assert bounded_backoff_delay(0, policy) == 0
    assert bounded_backoff_delay(1, policy) == 0.5
    assert bounded_backoff_delay(99, policy) == policy.bounded_backoff_max_seconds


def test_default_registry_is_closed_and_result_is_labelled_synthetic() -> None:
    adapter = SyntheticGovernmentVerificationAdapter(status=VerificationStatus.VERIFIED)
    response = adapter.verify(_request(), authority_id=SYNTHETIC_AUTHORITY, registry=AuthorityRegistry(), at=NOW)
    assert response.status is VerificationStatus.AUTHORITY_UNAVAILABLE
    assert response.synthetic is True
    assert response.failure_reason is not None
    assert SYNTHETIC_NID not in repr(response.public())


def test_registry_rejects_key_material_and_real_authority() -> None:
    with pytest.raises(AuthorityRegistryError):
        _authority(public_key_reference="-----BEGIN PUBLIC KEY-----")
    registry = AuthorityRegistry()
    registry.register(_authority(synthetic=False))
    with pytest.raises(AuthorityRegistryError, match="NOT APPROVED"):
        registry.resolve(SYNTHETIC_AUTHORITY, at=NOW)


def test_registry_rejects_expired_and_revoked_authorities() -> None:
    registry = AuthorityRegistry()
    registry.register(_authority(valid_until=NOW - timedelta(seconds=1)))
    with pytest.raises(AuthorityRegistryError, match="validity window"):
        registry.resolve(SYNTHETIC_AUTHORITY, at=NOW)

    registry = AuthorityRegistry()
    registry.register(_authority())
    registry.revoke(SYNTHETIC_AUTHORITY, reference="SYNTHETIC-REVOCATION-0001", at=NOW)
    with pytest.raises(AuthorityRegistryError, match="revoked"):
        registry.resolve(SYNTHETIC_AUTHORITY, at=NOW)


def test_synthetic_verified_result_is_never_authoritative() -> None:
    adapter = SyntheticGovernmentVerificationAdapter(status=VerificationStatus.VERIFIED)
    request = _request()
    response = adapter.verify(request, authority_id=SYNTHETIC_AUTHORITY, registry=_registry(), at=NOW)
    assert response.status is VerificationStatus.VERIFIED
    assert response.synthetic is True
    assert SYNTHETIC_NID not in repr(response.public())

    decision = decision_for_adapter_result(
        request,
        response,
        _registry(),
        actor="reviewer",
        at=NOW,
    )
    assert decision.state_upgrade_allowed is False
    assert decision.verification_event == "REVIEW_REQUIRED"
    with pytest.raises(IdentityEvidenceError, match="synthetic"):
        government_evidence_from_response(response, registry=_registry(), at=NOW)


def test_non_synthetic_flag_cannot_bypass_synthetic_authority_block(monkeypatch) -> None:
    request = _request(key="idem-non-synthetic-flag")
    response = VerificationResponse(
        correlation_id=request.correlation_id,
        request_id="SYNTHETIC-REQ-0003",
        status=VerificationStatus.VERIFIED,
        source_authority=SYNTHETIC_AUTHORITY,
        verified_attributes=(),
        timestamp=NOW,
        response_status="200",
        failure_reason=None,
        evidence_reference="SYNTHETIC-EVIDENCE-0003",
        nonce="SYNTHETIC-NONCE-0003",
        sent_at=NOW,
        signature_reference="SYNTHETIC-SIGNATURE-0003",
        synthetic=False,
    )
    registry = _registry()
    monkeypatch.setattr(registry, "resolve", lambda *args, **kwargs: _authority(synthetic=False))
    decision = decision_for_adapter_result(request, response, registry, actor="reviewer", at=NOW)
    assert decision.state_upgrade_allowed is False
    assert decision.verification_event == "REVIEW_REQUIRED"


def test_verification_result_audit_rejects_raw_nid_in_adapter_text() -> None:
    request = _request(key="idem-audit-leak")
    response = VerificationResponse(
        correlation_id=request.correlation_id,
        request_id="SYNTHETIC-REQ-0004",
        status=VerificationStatus.NOT_VERIFIED,
        source_authority=SYNTHETIC_AUTHORITY,
        verified_attributes=(),
        timestamp=NOW,
        response_status="422",
        failure_reason=f"SYNTHETIC rejection {SYNTHETIC_NID}",
        evidence_reference="SYNTHETIC-EVIDENCE-0004",
        nonce="SYNTHETIC-NONCE-0004",
        sent_at=NOW,
        signature_reference="SYNTHETIC-SIGNATURE-0004",
        synthetic=True,
    )
    with pytest.raises(IdentityEvidenceError, match="full national ID"):
        decision_for_adapter_result(request, response, _registry(), actor="reviewer", at=NOW)


def test_decision_audit_rejects_raw_nid_in_request_caller_text() -> None:
    request = replace(_request(key="idem-purpose-leak"), purpose=f"PURPOSE {SYNTHETIC_NID}")
    adapter = SyntheticGovernmentVerificationAdapter(status=VerificationStatus.NOT_VERIFIED)
    response = adapter.verify(request, authority_id=SYNTHETIC_AUTHORITY, registry=_registry(), at=NOW)
    with pytest.raises(IdentityEvidenceError, match="full national ID"):
        decision_for_adapter_result(request, response, _registry(), actor="reviewer", at=NOW)


@pytest.mark.parametrize(
    "status",
    [
        VerificationStatus.NOT_VERIFIED,
        VerificationStatus.NOT_FOUND,
        VerificationStatus.INDETERMINATE,
        VerificationStatus.TEMPORARILY_UNAVAILABLE,
        VerificationStatus.INVALID_REQUEST,
        VerificationStatus.AUTHORITY_UNAVAILABLE,
    ],
)
def test_non_verified_statuses_never_upgrade_state(status: VerificationStatus) -> None:
    request = _request()
    response = VerificationResponse(
        correlation_id=request.correlation_id,
        request_id="SYNTHETIC-REQ-0001",
        status=status,
        source_authority=SYNTHETIC_AUTHORITY,
        verified_attributes=(),
        timestamp=NOW,
        response_status="400",
        failure_reason=f"SYNTHETIC_{status.value}",
        evidence_reference="SYNTHETIC-EVIDENCE-0001",
        nonce="SYNTHETIC-NONCE-0001",
        sent_at=NOW,
        signature_reference="SYNTHETIC-SIGNATURE-0001",
        synthetic=True,
    )
    decision = decision_for_adapter_result(request, response, _registry(), actor="reviewer", at=NOW)
    assert decision.verification_event is None
    assert decision.state_upgrade_allowed is False


def test_verified_response_requires_approved_authority() -> None:
    request = _request()
    response = VerificationResponse(
        correlation_id=request.correlation_id,
        request_id="SYNTHETIC-REQ-0002",
        status=VerificationStatus.VERIFIED,
        source_authority="UNREGISTERED-AUTHORITY",
        verified_attributes=(
            VerifiedAttribute(
                name="identity_presence",
                protected_value="ATTESTED-SUBJECT-REF",
                source_authority="SYNTHETIC-AUTHORITY",
            ),
        ),
        timestamp=NOW,
        response_status="200",
        failure_reason=None,
        evidence_reference="SYNTHETIC-EVIDENCE-0002",
        nonce="SYNTHETIC-NONCE-0002",
        sent_at=NOW,
        signature_reference="SYNTHETIC-SIGNATURE-0002",
        synthetic=True,
    )
    with pytest.raises(AdapterSecurityError, match="approved authority"):
        decision_for_adapter_result(request, response, AuthorityRegistry(), actor="reviewer", at=NOW)


def test_idempotent_adapter_replay_returns_same_result() -> None:
    adapter = SyntheticGovernmentVerificationAdapter(status=VerificationStatus.NOT_VERIFIED)
    registry = _registry()
    request = _request(key="idem-replay")
    first = adapter.verify(request, authority_id=SYNTHETIC_AUTHORITY, registry=registry, at=NOW)
    second = adapter.verify(request, authority_id=SYNTHETIC_AUTHORITY, registry=registry, at=NOW)
    assert first == second


def test_idempotency_key_reuse_with_different_request_is_invalid() -> None:
    adapter = SyntheticGovernmentVerificationAdapter(status=VerificationStatus.VERIFIED)
    registry = _registry()
    first_request = _request(key="idem-reuse", correlation="CORR-A")
    adapter.verify(first_request, authority_id=SYNTHETIC_AUTHORITY, registry=registry, at=NOW)
    changed = _request(key="idem-reuse", correlation="CORR-B")
    response = adapter.verify(changed, authority_id=SYNTHETIC_AUTHORITY, registry=registry, at=NOW)
    assert response.status is VerificationStatus.INVALID_REQUEST


def test_nonce_replay_and_stale_messages_fail_closed() -> None:
    guard = NonceReplayGuard()
    request = _request()
    response = VerificationResponse(
        correlation_id=request.correlation_id,
        request_id="SYNTHETIC-REQ-0003",
        status=VerificationStatus.NOT_VERIFIED,
        source_authority=SYNTHETIC_AUTHORITY,
        verified_attributes=(),
        timestamp=NOW,
        response_status="200",
        failure_reason="SYNTHETIC_NOT_VERIFIED",
        evidence_reference="SYNTHETIC-EVIDENCE-0003",
        nonce="SYNTHETIC-NONCE-0003",
        sent_at=NOW,
        signature_reference="SYNTHETIC-SIGNATURE-0003",
        synthetic=True,
    )
    guard.check(nonce=response.nonce, sent_at=response.sent_at, now=NOW, policy=AdapterPolicy())
    with pytest.raises(AdapterSecurityError, match="already been used"):
        guard.check(nonce=response.nonce, sent_at=response.sent_at, now=NOW, policy=AdapterPolicy())
    with pytest.raises(AdapterSecurityError, match="outside the replay window"):
        guard.check(
            nonce="SYNTHETIC-NONCE-0004",
            sent_at=NOW - timedelta(minutes=10),
            now=NOW,
            policy=AdapterPolicy(),
        )


def test_rate_limit_and_circuit_breaker_fail_closed() -> None:
    policy = AdapterPolicy(rate_limit_per_minute=1, circuit_failure_threshold=3)
    adapter = SyntheticGovernmentVerificationAdapter(
        policy=policy,
        status=VerificationStatus.NOT_VERIFIED,
    )
    registry = _registry()
    adapter.verify(_request(key="rate-1"), authority_id=SYNTHETIC_AUTHORITY, registry=registry, at=NOW)
    limited = adapter.verify(
        _request(key="rate-2", correlation="CORR-0002"),
        authority_id=SYNTHETIC_AUTHORITY,
        registry=registry,
        at=NOW,
    )
    assert limited.status is VerificationStatus.TEMPORARILY_UNAVAILABLE

    circuit_adapter = SyntheticGovernmentVerificationAdapter(
        policy=AdapterPolicy(circuit_failure_threshold=1),
        status=VerificationStatus.VERIFIED,
    )
    circuit_adapter.verify(
        _request(key="circuit-1"),
        authority_id=SYNTHETIC_AUTHORITY,
        registry=AuthorityRegistry(),
        at=NOW,
    )
    blocked = circuit_adapter.verify(
        _request(key="circuit-2", correlation="CORR-0003"),
        authority_id=SYNTHETIC_AUTHORITY,
        registry=registry,
        at=NOW,
    )
    assert blocked.status is VerificationStatus.TEMPORARILY_UNAVAILABLE


def test_adapter_audit_events_contain_no_raw_nid() -> None:
    request = _request()
    request_event = request_audit_event(request, authority_id=SYNTHETIC_AUTHORITY)
    denied_event = unauthorized_attempt_audit_event(
        actor=request.actor,
        purpose=request.purpose,
        organization_id=request.organization_id,
        facility_id=request.facility_id,
        subject_reference=request.subject_reference,
        national_id_hash=request.national_id_hash,
        reason_code="AUTHORITY_UNAVAILABLE",
    )
    assert request_event.correlation_id == request.correlation_id
    assert denied_event.decision == "deny"
    assert SYNTHETIC_NID not in repr(request_event)
    assert SYNTHETIC_NID not in repr(denied_event)


def test_request_audit_rejects_raw_nid_embedded_in_subject_reference() -> None:
    request = replace(_request(), subject_reference=f"SUBJECT-{SYNTHETIC_NID}")
    with pytest.raises(IdentityEvidenceError, match="full national ID"):
        request_audit_event(request, authority_id=SYNTHETIC_AUTHORITY)


def test_request_audit_rejects_raw_nid_in_caller_text() -> None:
    request = replace(_request(), actor=SYNTHETIC_NID)
    with pytest.raises(IdentityEvidenceError, match="full national ID"):
        request_audit_event(request, authority_id=SYNTHETIC_AUTHORITY)


def test_unauthorized_audit_rejects_raw_nid_in_caller_text() -> None:
    request = _request()
    with pytest.raises(IdentityEvidenceError, match="full national ID"):
        unauthorized_attempt_audit_event(
            actor=SYNTHETIC_NID,
            purpose=request.purpose,
            organization_id=request.organization_id,
            facility_id=request.facility_id,
            subject_reference=request.subject_reference,
            national_id_hash=request.national_id_hash,
            reason_code="AUTHORITY_UNAVAILABLE",
        )


def test_unauthorized_audit_rejects_raw_nid_hash() -> None:
    request = _request()
    with pytest.raises(IdentityEvidenceError, match="64-character hex"):
        unauthorized_attempt_audit_event(
            actor=request.actor,
            purpose=request.purpose,
            organization_id=request.organization_id,
            facility_id=request.facility_id,
            subject_reference=request.subject_reference,
            national_id_hash=SYNTHETIC_NID,
            reason_code="AUTHORITY_UNAVAILABLE",
        )
