"""Engineering Leap 04 — synthetic federated infrastructure evidence.

This suite exercises only additive, route-free, in-memory contracts. It uses
synthetic fixtures and injected adapters; it creates no route, DDL, migration,
credential, real patient record, government connection, or release-state change.
A passing test is contract evidence only, never production or legal approval.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from app.clinical.observability import clinical_safety_metrics, prometheus_lines
from app.lab_slice.decision_engine import assess_result, authorize_release
from app.lab_slice.fhir_projector import build_bundle
from app.lab_slice.models import RELEASE_PENDING
from app.lab_slice.terminology_bindings import bind_test
from app.national.services.federated_health_infrastructure import (
    CONSENT_ACTIVE,
    CONSENT_WITHDRAWN,
    EXCHANGE_CONFLICT,
    EXCHANGE_DEAD_LETTER,
    EXCHANGE_DELIVERED,
    EXCHANGE_RETRY_SCHEDULED,
    FEDERATION_SCHEMA,
    INSTITUTION_AUTHORIZED,
    INSTITUTION_REGISTERED,
    INSTITUTION_REVOKED,
    INSTITUTION_VERIFIED,
    REFERRAL_ACCEPTED,
    REFERRAL_CANCELLED,
    REFERRAL_EXPIRED,
    REFERRAL_REJECTED,
    REFERRAL_TRANSMITTED,
    TRUST_ACTIVE,
    TRUST_REVOKED,
    DisclosureRequest,
    EmergencyGrant,
    ExchangeEnvelope,
    FederatedCoreCoordinator,
    FederatedExchangeBroker,
    FederatedInstitutionRegistry,
    FederatedObservability,
    FederatedOwnershipLedger,
    FederatedPolicyEngine,
    FederatedRecord,
    FederatedReferralRouter,
    FederationConflict,
    FederationDenied,
    FederationIntegrityError,
    FederationPolicy,
    FederationValidationError,
    ReferralRequest,
    precheck_fhir_bundle,
)
from app.services.reference.national_lab_catalog import NationalLaboratoryCatalog

# Reuse Leap 02/03 synthetic fixtures rather than duplicating or weakening them.
_LEAP02_PATH = Path(__file__).with_name("test_national_core_workflow_e2e.py")
_LEAP02_SPEC = importlib.util.spec_from_file_location("gula_leap04_fixtures", _LEAP02_PATH)
assert _LEAP02_SPEC is not None and _LEAP02_SPEC.loader is not None
_LEAP02 = importlib.util.module_from_spec(_LEAP02_SPEC)
_LEAP02_SPEC.loader.exec_module(_LEAP02)
_case = _LEAP02._case
PATIENT_REF = "synthetic-patient-ref"
RAW_NID = "123456789012"

AT = "2026-11-26T12:00:00+00:00"
SOON = "2026-11-26T12:00:00+00:00"
LATER = "2026-11-26T13:00:00+00:00"
AFTER_LATER = "2026-11-26T14:00:00+00:00"
EXPIRES = "2026-11-26T18:00:00+00:00"
FAR_FUTURE = "2026-12-01T00:00:00+00:00"
PAST = "2026-11-26T11:00:00+00:00"
PAYLOAD_DIGEST = hashlib.sha256(b"synthetic-payload").hexdigest()
_ALL_CATEGORIES = (
    "identity_reference",
    "referral",
    "lab_order",
    "lab_result",
    "clinical_document",
    "public_health_aggregate",
)


def _env(*, transport: Any = None, policy: FederationPolicy | None = None) -> SimpleNamespace:
    policy = policy or FederationPolicy(
        max_retries=3, retry_base_seconds=0.5, decision_window_seconds=86400
    )
    registry = FederatedInstitutionRegistry(policy)
    ledger = FederatedOwnershipLedger(registry, policy)
    engine = FederatedPolicyEngine(registry, ledger, policy)
    broker = FederatedExchangeBroker(registry, engine, transport, policy)
    referrals = FederatedReferralRouter(registry, engine, broker)
    observability = FederatedObservability(broker)
    coordinator = FederatedCoreCoordinator(
        registry, ledger, engine, broker, referrals, observability
    )

    def institution(
        *,
        identifier: str,
        kind: str,
        endpoint: str,
        directorate_id: str | None = None,
        status: str = INSTITUTION_AUTHORIZED,
        authorized_until: str | None = FAR_FUTURE,
    ) -> None:
        registry.register(
            kind=kind,
            endpoint_reference=endpoint,
            profiles=("synthetic-profile",),
            capabilities=("exchange",),
            status=status,
            directorate_id=directorate_id,
            facility_type="hospital" if kind == "facility" else None,
            authorized_until=authorized_until,
            institution_id=identifier,
        )

    institution(identifier="NAT-0001", kind="national", endpoint="synthetic-national-ref")
    institution(identifier="DIR-0001", kind="directorate", endpoint="synthetic-directorate-1")
    institution(identifier="DIR-0002", kind="directorate", endpoint="synthetic-directorate-2")
    institution(
        identifier="FAC-A", kind="facility", endpoint="synthetic-facility-a", directorate_id="DIR-0001"
    )
    institution(
        identifier="FAC-B", kind="facility", endpoint="synthetic-facility-b", directorate_id="DIR-0001"
    )
    institution(
        identifier="FAC-C", kind="facility", endpoint="synthetic-facility-c", directorate_id="DIR-0002"
    )
    institution(
        identifier="FAC-D", kind="facility", endpoint="synthetic-facility-d", directorate_id="DIR-0002"
    )
    institution(
        identifier="FAC-INACTIVE",
        kind="facility",
        endpoint="synthetic-inactive-ref",
        status=INSTITUTION_REGISTERED,
    )
    institution(
        identifier="FAC-EXPIRED",
        kind="facility",
        endpoint="synthetic-expired-ref",
        authorized_until=PAST,
    )
    institution(
        identifier="FAC-REVOKED",
        kind="facility",
        endpoint="synthetic-revoked-ref",
        status=INSTITUTION_REVOKED,
    )

    registry.add_trust(
        "FAC-A",
        "FAC-B",
        scope=_ALL_CATEGORIES,
        expires_at=FAR_FUTURE,
        actor_reference="NAT-0001",
        at=AT,
    )
    registry.add_trust(
        "FAC-A",
        "FAC-C",
        scope=_ALL_CATEGORIES,
        expires_at=FAR_FUTURE,
        actor_reference="NAT-0001",
        at=AT,
    )
    registry.add_trust(
        "FAC-B",
        "FAC-A",
        scope=_ALL_CATEGORIES,
        expires_at=FAR_FUTURE,
        actor_reference="NAT-0001",
        at=AT,
    )
    registry.add_trust(
        "FAC-A",
        "FAC-D",
        scope=("referral",),
        expires_at=FAR_FUTURE,
        actor_reference="NAT-0001",
        at=AT,
    )
    return SimpleNamespace(
        policy=policy,
        registry=registry,
        ledger=ledger,
        engine=engine,
        broker=broker,
        referrals=referrals,
        observability=observability,
        coordinator=coordinator,
    )


def _request(**overrides: Any) -> DisclosureRequest:
    values: dict[str, Any] = {
        "requester_reference": "synthetic-requester-ref",
        "requesting_institution_id": "FAC-A",
        "role": "physician",
        "relationship_reference": "synthetic-relationship-ref",
        "purpose": "treatment",
        "category": "clinical_document",
        "legal_basis_reference": "synthetic-legal-basis",
        "consent_status": CONSENT_ACTIVE,
        "audit_reference": "synthetic-audit-ref",
        "minimum_necessary": True,
        "at": AT,
        "patient_reference": PATIENT_REF,
        "record_reference": "rec-0001",
    }
    values.update(overrides)
    return DisclosureRequest(**values)


def _grant(**overrides: Any) -> EmergencyGrant:
    values: dict[str, Any] = {
        "approver_reference": "DIR-0001",
        "reason_code": "emergency",
        "categories": ("clinical_document",),
        "expires_at": LATER,
        "audit_reference": "synthetic-emergency-audit",
    }
    values.update(overrides)
    return EmergencyGrant(**values)


def _record(**overrides: Any) -> FederatedRecord:
    values: dict[str, Any] = {
        "record_id": "rec-0001",
        "institution_id": "FAC-A",
        "patient_reference": PATIENT_REF,
        "category": "clinical_document",
        "revision": 1,
        "event_sequence": 1,
        "recorded_at": AT,
        "classification": "synthetic_federated",
        "disclosure_policy": "minimum_necessary",
        "payload_digest": PAYLOAD_DIGEST,
    }
    values.update(overrides)
    return FederatedRecord(**values)


def _decision(env: SimpleNamespace, request: DisclosureRequest | None = None) -> Any:
    return env.engine.evaluate(request or _request(), target_institution_id="FAC-B")


def _envelope(
    env: SimpleNamespace,
    *,
    envelope_id: str = "env-0001",
    idempotency_key: str = "idem-0001",
    correlation_id: str = "corr-0001",
    source: str = "FAC-A",
    destination: str = "FAC-B",
    message_type: str = "clinical_document",
    category: str = "clinical_document",
    record_reference: str = "rec-0001",
    revision: int = 1,
    event_sequence: int = 1,
    expires_at: str = EXPIRES,
    provenance_digest: str | None = None,
    decision: Any = None,
    requester_reference: str | None = None,
) -> ExchangeEnvelope:
    decision = decision or _decision(env)
    return ExchangeEnvelope(
        envelope_id=envelope_id,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
        source_institution_id=source,
        destination_institution_id=destination,
        message_type=message_type,
        patient_reference=PATIENT_REF,
        record_reference=record_reference,
        category=category,
        revision=revision,
        event_sequence=event_sequence,
        expires_at=expires_at,
        decision_digest=decision.decision_digest,
        provenance_digest=provenance_digest or hashlib.sha256(b"synthetic-provenance").hexdigest(),
        requester_reference=requester_reference or decision.requester_reference,
    )


def _referral(**overrides: Any) -> ReferralRequest:
    values: dict[str, Any] = {
        "referral_id": "ref-0001",
        "source_facility_id": "FAC-A",
        "destination_facility_id": "FAC-B",
        "destination_directorate_id": "DIR-0001",
        "patient_reference": PATIENT_REF,
        "purpose": "referral",
        "priority": "routine",
        "reason_code": "synthetic-referral",
        "expires_at": EXPIRES,
        "correlation_id": "corr-referral-0001",
    }
    values.update(overrides)
    return ReferralRequest(**values)


def _valid_bundle() -> tuple[dict[str, Any], str]:
    case = _case("leap04-fhir")
    catalog = NationalLaboratoryCatalog()
    catalog.seed_common_tests()
    binding = bind_test(catalog, case.result.test_code)
    pending = assess_result(
        order=case.order,
        specimen=case.specimen,
        result=case.result,
        qc=case.qc,
        binding=binding,
    )
    assert pending.status == RELEASE_PENDING
    released = authorize_release(
        pending,
        reviewer="synthetic-reviewer-leap04",
        reason="synthetic manual release",
        idempotency_key="synthetic-leap04-release-key",
    )
    bundle = build_bundle(
        patient=case.patient,
        order=case.order,
        specimen=case.specimen,
        result=case.result,
        decision=released,
        binding=binding,
    )
    return bundle, case.patient.patient_id


# -- Institution trust and registry -----------------------------------------


def test_unknown_institution_is_denied() -> None:
    with pytest.raises(FederationDenied, match="unknown institution"):
        _env().registry.assert_authorized("FAC-MISSING", at=AT)


def test_registered_inactive_institution_is_denied() -> None:
    with pytest.raises(FederationDenied, match="not authorized"):
        _env().registry.assert_authorized("FAC-INACTIVE", at=AT)


def test_revoked_institution_is_denied() -> None:
    with pytest.raises(FederationDenied, match="not authorized"):
        _env().registry.assert_authorized("FAC-REVOKED", at=AT)


def test_expired_institution_authorization_is_denied() -> None:
    with pytest.raises(FederationDenied, match="expired"):
        _env().registry.assert_authorized("FAC-EXPIRED", at=AT)


def test_missing_explicit_trust_relation_is_denied() -> None:
    env = _env()
    decision = env.engine.evaluate(
        _request(requesting_institution_id="FAC-D"), target_institution_id="FAC-B"
    )
    assert decision.allowed is False


def test_trust_scope_mismatch_is_denied() -> None:
    env = _env()
    decision = env.engine.evaluate(_request(), target_institution_id="FAC-D")
    assert decision.allowed is False
    assert decision.reason_code in {"authorization_denied", "workflow_rejected"}


def test_revoked_trust_is_denied() -> None:
    env = _env()
    env.registry.revoke_trust("FAC-A", "FAC-B", actor_reference="NAT-0001")
    assert env.engine.evaluate(_request(), target_institution_id="FAC-B").allowed is False


def test_cross_directorate_referral_is_denied() -> None:
    env = _env()
    with pytest.raises(FederationDenied, match="outside the addressed directorate"):
        env.referrals.create(
            _referral(destination_facility_id="FAC-C"),
            requester_reference="synthetic-requester-ref",
            at=AT,
            actor_reference="FAC-A",
        )


def test_discovery_does_not_expose_endpoint_or_secrets() -> None:
    public = _env().registry.discover("FAC-A", at=AT)
    assert public["schema"] == FEDERATION_SCHEMA
    assert "endpoint_reference" not in public
    assert "secret" not in json.dumps(public).lower()


def test_tampered_registry_provenance_is_rejected_on_restore() -> None:
    env = _env()
    snapshot = env.registry.snapshot()
    snapshot["institutions"][0]["provenance_digest"] = "0" * 64
    with pytest.raises(FederationIntegrityError, match="provenance digest"):
        env.registry.restore(snapshot)


# -- Disclosure policy -------------------------------------------------------


def test_valid_disclosure_is_bounded_and_time_limited() -> None:
    env = _env()
    decision = env.coordinator.authorize(_request(), target_institution_id="FAC-B")
    assert decision.allowed is True
    assert decision.categories == ("clinical_document",)
    assert decision.expires_at > AT
    assert env.engine.decision(decision.decision_digest) == decision


def test_minimum_necessary_violation_is_denied() -> None:
    env = _env()
    decision = env.engine.evaluate(_request(minimum_necessary=False), target_institution_id="FAC-B")
    assert decision.allowed is False
    assert decision.categories == ()


def test_unapproved_purpose_is_denied() -> None:
    decision = _env().engine.evaluate(_request(purpose="marketing"), target_institution_id="FAC-B")
    assert decision.allowed is False


def test_unapproved_role_is_denied() -> None:
    decision = _env().engine.evaluate(_request(role="visitor"), target_institution_id="FAC-B")
    assert decision.allowed is False


def test_withdrawn_consent_is_denied() -> None:
    decision = _env().engine.evaluate(
        _request(consent_status=CONSENT_WITHDRAWN), target_institution_id="FAC-B"
    )
    assert decision.allowed is False


def test_revoked_authorization_is_denied() -> None:
    env = _env()
    env.registry.set_status(
        "FAC-A", INSTITUTION_REVOKED, actor_reference="NAT-0001", reason_code_value="revoked"
    )
    assert env.engine.evaluate(_request(), target_institution_id="FAC-B").allowed is False


def test_public_health_aggregate_request_is_denied() -> None:
    decision = _env().engine.evaluate(
        _request(category="public_health_aggregate", purpose="public_health_authorized"),
        target_institution_id="FAC-B",
    )
    assert decision.allowed is False


def test_valid_emergency_grant_is_narrow_and_time_bounded() -> None:
    env = _env()
    decision = env.engine.evaluate(
        _request(consent_status=CONSENT_WITHDRAWN, emergency_grant=_grant()),
        target_institution_id="FAC-B",
    )
    assert decision.allowed is True
    assert decision.categories == ("clinical_document",)
    assert decision.expires_at <= LATER


def test_expired_emergency_grant_is_denied() -> None:
    decision = _env().engine.evaluate(
        _request(consent_status=CONSENT_WITHDRAWN, emergency_grant=_grant(expires_at=PAST)),
        target_institution_id="FAC-B",
    )
    assert decision.allowed is False


def test_overbroad_emergency_grant_is_rejected_at_construction() -> None:
    with pytest.raises(FederationValidationError, match="public health"):
        _grant(categories=("clinical_document", "public_health_aggregate"))


def test_emergency_grant_with_unknown_approver_is_denied() -> None:
    decision = _env().engine.evaluate(
        _request(consent_status=CONSENT_WITHDRAWN, emergency_grant=_grant(approver_reference="APPROVER-MISSING")),
        target_institution_id="FAC-B",
    )
    assert decision.allowed is False


def test_emergency_grant_approver_must_be_coordination_authority() -> None:
    decision = _env().engine.evaluate(
        _request(consent_status=CONSENT_WITHDRAWN, emergency_grant=_grant(approver_reference="FAC-C")),
        target_institution_id="FAC-B",
    )
    assert decision.allowed is False


def test_raw_identifier_in_disclosure_metadata_is_rejected() -> None:
    with pytest.raises(FederationValidationError, match="identifier-shaped"):
        _request(audit_reference=f"audit-{RAW_NID}")


def test_denial_is_recorded_as_bounded_counter_only() -> None:
    env = _env()
    with pytest.raises(FederationDenied, match="disclosure denied"):
        env.coordinator.authorize(_request(minimum_necessary=False), target_institution_id="FAC-B")
    snapshot = env.observability.snapshot()
    assert snapshot["denials"][0]["institution_id"] == "FAC-A"
    assert snapshot["denials"][0]["count"] == 1
    assert RAW_NID not in str(clinical_safety_metrics.snapshot())
    assert RAW_NID not in "\n".join(prometheus_lines())


# -- Referral lifecycle ------------------------------------------------------


def test_referral_is_routed_and_transmitted() -> None:
    env = _env()
    state = env.referrals.create(
        _referral(),
        requester_reference="synthetic-requester-ref",
        at=AT,
        actor_reference="FAC-A",
    )
    assert state.status == REFERRAL_TRANSMITTED
    assert state.to_public_dict()["canonical_referral_status"] == "sent"
    assert env.broker.summary()["states"] == {EXCHANGE_DELIVERED: 1}


def test_transmission_is_distinct_from_acceptance() -> None:
    env = _env()
    state = env.referrals.create(
        _referral(),
        requester_reference="synthetic-requester-ref",
        at=AT,
        actor_reference="FAC-A",
    )
    receipt = env.broker.summary()
    assert state.status == REFERRAL_TRANSMITTED
    assert receipt["acknowledged"] == 0
    assert receipt["accepted"] == 0
    with pytest.raises(FederationDenied, match="acknowledge before deciding"):
        env.referrals.accept_or_reject(
            "ref-0001",
            institution_id="FAC-B",
            at=LATER,
            actor_reference="FAC-B",
            accepted=True,
        )


def test_wrong_institution_cannot_acknowledge() -> None:
    env = _env()
    env.referrals.create(
        _referral(), requester_reference="synthetic-requester-ref", at=AT, actor_reference="FAC-A"
    )
    with pytest.raises(FederationDenied, match="destination institution"):
        env.referrals.acknowledge(
            "ref-0001", institution_id="FAC-C", at=LATER, actor_reference="FAC-C"
        )


def test_acceptance_requires_explicit_acknowledgement() -> None:
    env = _env()
    env.referrals.create(
        _referral(), requester_reference="synthetic-requester-ref", at=AT, actor_reference="FAC-A"
    )
    with pytest.raises(FederationDenied, match="acknowledge before deciding"):
        env.referrals.accept_or_reject(
            "ref-0001",
            institution_id="FAC-B",
            at=LATER,
            actor_reference="FAC-B",
            accepted=True,
        )


def test_accepted_and_rejected_referrals_are_tracked() -> None:
    env = _env()
    for suffix, accepted, expected in (
        ("ref-accepted", True, REFERRAL_ACCEPTED),
        ("ref-rejected", False, REFERRAL_REJECTED),
    ):
        env.referrals.create(
            _referral(referral_id=suffix, correlation_id=f"corr-{suffix}"),
            requester_reference="synthetic-requester-ref",
            at=AT,
            actor_reference="FAC-A",
        )
        env.referrals.acknowledge(
            suffix, institution_id="FAC-B", at=LATER, actor_reference="FAC-B"
        )
        state = env.referrals.accept_or_reject(
            suffix,
            institution_id="FAC-B",
            at=AFTER_LATER,
            actor_reference="FAC-B",
            accepted=accepted,
        )
        assert state.status == expected
        assert state.decision_by == "FAC-B"


def test_referral_can_be_cancelled_before_terminal_state() -> None:
    env = _env()
    env.referrals.create(
        _referral(), requester_reference="synthetic-requester-ref", at=AT, actor_reference="FAC-A"
    )
    state = env.referrals.cancel("ref-0001", at=LATER, actor_reference="FAC-A")
    assert state.status == REFERRAL_CANCELLED
    with pytest.raises(FederationDenied, match="terminal referral"):
        env.referrals.cancel("ref-0001", at=AFTER_LATER, actor_reference="FAC-A")


def test_referral_expiry_is_enforced() -> None:
    env = _env()
    env.referrals.create(
        _referral(), requester_reference="synthetic-requester-ref", at=AT, actor_reference="FAC-A"
    )
    with pytest.raises(FederationDenied, match="not yet expired"):
        env.referrals.expire("ref-0001", at=LATER, actor_reference="FAC-A")
    state = env.referrals.expire("ref-0001", at=FAR_FUTURE, actor_reference="FAC-A")
    assert state.status == REFERRAL_EXPIRED


def test_expired_referral_cannot_be_created() -> None:
    env = _env()
    with pytest.raises(FederationDenied, match="expired at creation"):
        env.referrals.create(
            _referral(expires_at=PAST),
            requester_reference="synthetic-requester-ref",
            at=AT,
            actor_reference="FAC-A",
        )


def test_duplicate_referral_identifier_is_rejected() -> None:
    env = _env()
    env.referrals.create(
        _referral(), requester_reference="synthetic-requester-ref", at=AT, actor_reference="FAC-A"
    )
    with pytest.raises(FederationConflict, match="already exists"):
        env.referrals.create(
            _referral(),
            requester_reference="synthetic-requester-ref",
            at=AT,
            actor_reference="FAC-A",
        )


# -- Exchange, synchronization, and recovery ---------------------------------


def test_duplicate_delivery_replays_original_receipt() -> None:
    env = _env()
    envelope = _envelope(env)
    first = env.broker.send(envelope, at=AT, actor_reference="FAC-A")
    replay = env.broker.send(envelope, at=LATER, actor_reference="FAC-A")
    assert first is replay
    assert replay.attempts == 1
    assert env.broker.summary()["total"] == 1


def test_idempotency_key_reuse_with_changed_content_is_conflict() -> None:
    env = _env()
    envelope = _envelope(env)
    env.broker.send(envelope, at=AT, actor_reference="FAC-A")
    changed = replace(envelope, revision=2)
    with pytest.raises(FederationConflict, match="idempotency key reused"):
        env.broker.send(changed, at=AT, actor_reference="FAC-A")


def test_stale_event_cannot_overwrite_newer_revision() -> None:
    env = _env()
    env.ledger.register(_record(revision=3, event_sequence=9))
    with pytest.raises(FederationConflict, match="stale event"):
        env.ledger.detect_conflict(_record(revision=1, event_sequence=2))


def test_conflicting_revision_creates_explicit_conflict() -> None:
    env = _env()
    envelope = _envelope(env, provenance_digest=hashlib.sha256(b"first").hexdigest())
    env.broker.receive(envelope, at=AT, actor_reference="FAC-B", ownership=env.ledger)
    changed = replace(envelope, provenance_digest=hashlib.sha256(b"second").hexdigest())
    with pytest.raises(FederationConflict, match="conflicting clinical revision"):
        env.broker.receive(changed, at=LATER, actor_reference="FAC-B", ownership=env.ledger)


def test_inbound_receive_registers_custody_metadata_and_lineage() -> None:
    env = _env()
    envelope = _envelope(env)
    record = env.broker.receive(envelope, at=AT, actor_reference="FAC-B", ownership=env.ledger)
    assert env.ledger.assert_owned("rec-0001", "FAC-A") == record
    assert env.ledger.lineage("rec-0001") == ("rec-0001",)


def test_correction_appends_lineage_without_overwrite() -> None:
    env = _env()
    original = env.ledger.register(_record())
    replacement = env.ledger.supersede(
        "rec-0001",
        _record(record_id="rec-0002", revision=2, event_sequence=2),
    )
    assert env.ledger.lineage("rec-0002") == ("rec-0001", "rec-0002")
    assert env.ledger.assert_owned("rec-0001", "FAC-A") == original
    assert env.ledger.assert_owned("rec-0002", "FAC-A") == replacement


def test_cross_institution_correction_is_denied() -> None:
    env = _env()
    env.ledger.register(_record())
    with pytest.raises(FederationDenied, match="cross-institution"):
        env.ledger.supersede(
            "rec-0001", _record(record_id="rec-0002", institution_id="FAC-B", revision=2, event_sequence=2)
        )


def test_injected_adapter_failure_schedules_bounded_retry() -> None:
    calls: list[int] = []

    def flaky(bundle: dict[str, Any]) -> dict[str, Any]:
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError("synthetic endpoint unavailable")
        return {"status": "delivered", "envelope_digest": bundle["envelope_digest"]}

    env = _env(transport=flaky)
    receipt = env.broker.send(_envelope(env), at=AT, actor_reference="FAC-A")
    assert receipt.status == EXCHANGE_RETRY_SCHEDULED
    assert env.broker.retry_due(at=SOON, actor_reference="FAC-A") == 0
    assert env.broker.retry_due(at=AFTER_LATER, actor_reference="FAC-A") == 1
    assert env.broker.summary()["states"] == {EXCHANGE_DELIVERED: 1}
    assert len(calls) == 2


def test_retry_exhaustion_dead_letters_without_silent_drop() -> None:
    def failing(bundle: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("synthetic endpoint unavailable")

    env = _env(transport=failing)
    receipt = env.broker.send(_envelope(env), at=AT, actor_reference="FAC-A")
    assert receipt.status == EXCHANGE_RETRY_SCHEDULED
    assert env.broker.retry_due(at=LATER, actor_reference="FAC-A") == 1
    assert env.broker.retry_due(at=AFTER_LATER, actor_reference="FAC-A") == 1
    assert receipt.status == EXCHANGE_DEAD_LETTER
    assert env.broker.summary()["states"] == {EXCHANGE_DEAD_LETTER: 1}


def test_conflict_requires_explicit_reconciliation() -> None:
    env = _env()
    env.broker.send(_envelope(env), at=AT, actor_reference="FAC-A")
    with pytest.raises(FederationDenied, match="only a conflicting envelope"):
        env.broker.reconcile(
            "env-0001", reviewer_reference="NAT-0001", at=LATER, resolution_digest="a" * 64
        )
    env.broker.mark_conflict("env-0001", actor_reference="FAC-B", at=LATER)
    assert env.broker._receipt(env_or_id="env-0001").status == EXCHANGE_CONFLICT
    receipt = env.broker.reconcile(
        "env-0001", reviewer_reference="NAT-0001", at=AFTER_LATER, resolution_digest="a" * 64
    )
    assert receipt.status == EXCHANGE_DELIVERED


def test_tampered_audit_chain_is_detected() -> None:
    env = _env()
    env.broker.send(_envelope(env), at=AT, actor_reference="FAC-A")
    assert env.broker.audit_chain()["status"] == "VALID"
    env.broker._audit[0]["state"] = "tampered"
    result = env.broker.audit_chain()
    assert result["status"] == "INVALID"
    with pytest.raises(FederationIntegrityError, match="audit"):
        env.broker.restore(env.broker.snapshot())


def test_tampered_record_integrity_is_rejected_on_restore() -> None:
    env = _env()
    env.ledger.register(_record())
    snapshot = env.ledger.snapshot()
    snapshot["records"][0]["payload_digest"] = "b" * 64
    with pytest.raises(FederationIntegrityError, match="integrity digest"):
        env.ledger.restore(snapshot)


def test_snapshot_restore_preserves_federated_state() -> None:
    env = _env()
    env.ledger.register(_record())
    decision = env.coordinator.authorize(_request(), target_institution_id="FAC-B")
    env.broker.send(_envelope(env, decision=decision), at=AT, actor_reference="FAC-A")
    env.referrals.create(
        _referral(), requester_reference="synthetic-requester-ref", at=AT, actor_reference="FAC-A"
    )
    snapshot = env.coordinator.snapshot()

    restored = _env()
    restored.coordinator.restore(snapshot)
    assert restored.registry.discover("FAC-A", at=AT)["status"] == INSTITUTION_AUTHORIZED
    assert restored.ledger.assert_owned("rec-0001", "FAC-A").revision == 1
    assert restored.engine.decision(decision.decision_digest) == decision
    assert restored.broker.summary()["total"] == 2
    assert restored.broker.audit_chain()["status"] == "VALID"
    assert restored.broker.send(
        _envelope(restored, decision=decision), at=LATER, actor_reference="FAC-A"
    ).attempts == 1
    assert restored.referrals._state("ref-0001").status == REFERRAL_TRANSMITTED


def test_restore_rejects_cross_section_schema_mismatch() -> None:
    env = _env()
    snapshot = env.coordinator.snapshot()
    snapshot["registry"] = {"schema": "other.schema"}
    with pytest.raises(FederationIntegrityError, match="unsupported federation snapshot schema"):
        env.coordinator.restore(snapshot)


# -- FHIR, privacy, and leakage ----------------------------------------------


def test_valid_synthetic_bundle_passes_bounded_precheck() -> None:
    bundle, patient_id = _valid_bundle()
    result = precheck_fhir_bundle(bundle, expected_patient_reference=patient_id)
    assert result.valid is True
    assert result.reason_code == "none"
    assert "Patient" in result.resource_types


def test_malformed_bundle_fails_closed_without_raw_error_text() -> None:
    result = precheck_fhir_bundle(
        {"resourceType": "Bundle", "id": "synthetic-bundle", "type": "collection", "entry": []},
        expected_patient_reference=PATIENT_REF,
    )
    assert result.valid is False
    assert result.reason_code == "validation_failed"


def test_raw_identifier_in_bundle_fails_closed() -> None:
    bundle, patient_id = _valid_bundle()
    bundle = copy.deepcopy(bundle)
    bundle["entry"][0]["resource"]["id"] = RAW_NID
    result = precheck_fhir_bundle(bundle, expected_patient_reference=patient_id)
    assert result.valid is False
    assert result.reason_code == "validation_failed"


def test_unsupported_code_system_fails_closed() -> None:
    bundle, patient_id = _valid_bundle()
    bundle = copy.deepcopy(bundle)
    for entry in bundle["entry"]:
        resource = entry["resource"]
        coding = resource.get("code", {})
        if isinstance(coding, dict) and isinstance(coding.get("coding"), list):
            for item in coding["coding"]:
                if isinstance(item, dict):
                    item["system"] = "http://unapproved.example/system"
    result = precheck_fhir_bundle(bundle, expected_patient_reference=patient_id)
    assert result.valid is False


def test_transport_failure_text_never_reaches_audit_or_metrics() -> None:
    secret = "synthetic-secret-endpoint-987654321"

    def failing(bundle: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(secret)

    env = _env(transport=failing)
    env.broker.send(_envelope(env), at=AT, actor_reference="FAC-A")
    snapshot = json.dumps(env.coordinator.snapshot())
    assert secret not in snapshot
    assert secret not in str(clinical_safety_metrics.snapshot())
    assert secret not in "\n".join(prometheus_lines())
    assert env.broker.audit_chain()["status"] == "VALID"


def test_observability_snapshot_never_contains_patient_payload() -> None:
    env = _env()
    env.ledger.register(_record())
    env.broker.send(_envelope(env), at=AT, actor_reference="FAC-A")
    snapshot = json.dumps(env.observability.snapshot())
    for forbidden in (RAW_NID, "synthetic-payload", "birthdate", "telecom"):
        assert forbidden not in snapshot


def test_bounded_caps_reject_unbounded_inputs() -> None:
    registry = FederatedInstitutionRegistry(FederationPolicy(max_institutions=1))
    registry.register(
        kind="national",
        endpoint_reference="synthetic-first-ref",
        profiles=(),
        capabilities=(),
        status=INSTITUTION_AUTHORIZED,
        institution_id="NAT-FIRST",
    )
    with pytest.raises(FederationValidationError, match="registry depth cap"):
        registry.register(
            kind="national",
            endpoint_reference="synthetic-overflow-ref",
            profiles=(),
            capabilities=(),
            status=INSTITUTION_AUTHORIZED,
            institution_id="NAT-OVERFLOW",
        )


def test_integration_envelope_reuses_canonical_shape() -> None:
    env = _env()
    envelope = _envelope(env)
    event = envelope.to_integration_event(
        tenant_id="synthetic-tenant", actor_id="synthetic-actor", occurred_at=_LEAP02.NOW
    )
    payload = event.model_dump(mode="json")
    assert payload["entity_id"] == "rec-0001"
    assert payload["correlation_id"] == "corr-0001"
    assert payload["payload"]["category"] == "clinical_document"
    assert "patient" not in json.dumps(payload).lower()


# -- Independent-review fixes (H1-H8) ---------------------------------------


def test_decision_cannot_be_reused_for_another_institution() -> None:
    env = _env()
    decision = _decision(env)
    with pytest.raises(FederationDenied, match="target institution mismatch"):
        env.broker.send(
            _envelope(env, destination="FAC-C", decision=decision),
            at=AT,
            actor_reference="FAC-A",
        )


def test_decision_cannot_be_reused_for_another_category() -> None:
    env = _env()
    decision = _decision(env)
    with pytest.raises(FederationDenied, match="category mismatch"):
        env.broker.send(
            _envelope(env, category="lab_result", decision=decision),
            at=AT,
            actor_reference="FAC-A",
        )


def test_decision_cannot_be_reused_for_another_patient_or_record() -> None:
    env = _env()
    decision = _decision(env)
    with pytest.raises(FederationDenied, match="patient reference mismatch"):
        env.broker.send(
            replace(_envelope(env, decision=decision), patient_reference="synthetic-other-patient"),
            at=AT,
            actor_reference="FAC-A",
        )
    with pytest.raises(FederationDenied, match="record reference mismatch"):
        env.broker.send(
            replace(_envelope(env, decision=decision), record_reference="rec-0002"),
            at=AT,
            actor_reference="FAC-A",
        )


def test_decision_cannot_be_reused_by_another_requester() -> None:
    env = _env()
    decision = _decision(env)
    with pytest.raises(FederationDenied, match="requester mismatch"):
        env.broker.send(
            _envelope(env, decision=decision, requester_reference="synthetic-other-requester"),
            at=AT,
            actor_reference="FAC-A",
        )


def test_expired_decision_is_rejected_on_send() -> None:
    env = _env()
    decision = _decision(env)
    envelope = replace(
        _envelope(env, decision=decision), expires_at="2026-11-29T00:00:00+00:00"
    )
    with pytest.raises(FederationDenied, match="decision is expired"):
        env.broker.send(envelope, at="2026-11-28T00:00:00+00:00", actor_reference="FAC-A")


def test_unbound_disclosure_request_is_denied() -> None:
    env = _env()
    decision = env.engine.evaluate(
        _request(patient_reference=None, record_reference=None), target_institution_id="FAC-B"
    )
    assert decision.allowed is False


def test_forged_decision_restore_is_rejected() -> None:
    env = _env()
    decision = _decision(env)
    snapshot = env.engine.snapshot()
    snapshot["decisions"][0]["categories"] = ["clinical_document", "public_health_aggregate"]
    with pytest.raises(FederationIntegrityError, match="digest does not match"):
        env.engine.restore(snapshot)
    assert env.engine.decision(decision.decision_digest) == decision


def test_restored_envelopes_remain_retryable() -> None:
    calls: list[int] = []

    def flaky(bundle: dict[str, Any]) -> dict[str, Any]:
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError("synthetic endpoint unavailable")
        return {"status": "delivered", "envelope_digest": bundle["envelope_digest"]}

    env = _env(transport=flaky)
    env.broker.send(_envelope(env), at=AT, actor_reference="FAC-A")
    snapshot = env.coordinator.snapshot()
    restored = _env(transport=flaky)
    restored.coordinator.restore(snapshot)
    assert restored.broker.retry_due(at=LATER, actor_reference="FAC-A") == 1
    assert restored.broker.summary()["states"] == {EXCHANGE_DELIVERED: 1}


def test_restored_delivered_envelope_can_be_acknowledged() -> None:
    env = _env()
    env.broker.send(_envelope(env), at=AT, actor_reference="FAC-A")
    snapshot = env.coordinator.snapshot()
    restored = _env()
    restored.coordinator.restore(snapshot)
    receipt = restored.broker.acknowledge(
        "env-0001", institution_id="FAC-B", at=LATER, actor_reference="FAC-B"
    )
    assert receipt.acknowledged is True


def test_restore_rejects_envelope_digest_mismatch() -> None:
    env = _env()
    env.broker.send(_envelope(env), at=AT, actor_reference="FAC-A")
    snapshot = env.broker.snapshot()
    snapshot["envelopes"]["env-0001"]["record_reference"] = "rec-tampered"
    with pytest.raises(FederationIntegrityError, match="envelope digest does not match"):
        env.broker.restore(snapshot)


def test_retry_after_trust_revocation_is_dead_lettered() -> None:
    def failing(bundle: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("synthetic endpoint unavailable")

    env = _env(transport=failing)
    env.broker.send(_envelope(env), at=AT, actor_reference="FAC-A")
    env.registry.revoke_trust("FAC-A", "FAC-B", actor_reference="NAT-0001")
    assert env.broker.retry_due(at=LATER, actor_reference="FAC-A") == 1
    receipt = env.broker._receipt(env_or_id="env-0001")
    assert receipt.status == EXCHANGE_DEAD_LETTER
    assert receipt.reason_code != "none"


def test_conflicting_revision_sets_explicit_conflict_state() -> None:
    env = _env()
    envelope = _envelope(env, provenance_digest=hashlib.sha256(b"first").hexdigest())
    env.broker.receive(envelope, at=AT, actor_reference="FAC-B", ownership=env.ledger)
    changed = replace(envelope, provenance_digest=hashlib.sha256(b"second").hexdigest())
    with pytest.raises(FederationConflict, match="conflicting clinical revision"):
        env.broker.receive(changed, at=LATER, actor_reference="FAC-B", ownership=env.ledger)
    receipt = env.broker._receipt(env_or_id="env-0001")
    assert receipt.status == EXCHANGE_CONFLICT
    resolved = env.broker.reconcile(
        "env-0001",
        reviewer_reference="NAT-0001",
        at=AFTER_LATER,
        resolution_digest="c" * 64,
    )
    assert resolved.status == EXCHANGE_DELIVERED


def test_revoked_institution_cannot_be_reauthorized_without_transition() -> None:
    env = _env()
    env.registry.set_status(
        "FAC-B", INSTITUTION_REVOKED, actor_reference="anyone", reason_code_value="revoked"
    )
    with pytest.raises(FederationDenied, match="transition is not allowed"):
        env.registry.set_status(
            "FAC-B", INSTITUTION_AUTHORIZED, actor_reference="anyone", reason_code_value="restore"
        )


def test_institution_lifecycle_requires_verification_before_authorization() -> None:
    registry = FederatedInstitutionRegistry(FederationPolicy(max_institutions=4))
    registry.register(
        kind="facility",
        endpoint_reference="synthetic-lifecycle-ref",
        profiles=(),
        capabilities=(),
        status=INSTITUTION_REGISTERED,
        institution_id="FAC-LIFECYCLE",
    )
    with pytest.raises(FederationDenied, match="transition is not allowed"):
        registry.set_status(
            "FAC-LIFECYCLE",
            INSTITUTION_AUTHORIZED,
            actor_reference="anyone",
            reason_code_value="skip",
        )
    assert (
        registry.set_status(
            "FAC-LIFECYCLE",
            INSTITUTION_VERIFIED,
            actor_reference="anyone",
            reason_code_value="verify",
        ).status
        == INSTITUTION_VERIFIED
    )


def test_audit_cap_fails_before_transport_side_effect() -> None:
    delivered: list[str] = []

    def transport(bundle: dict[str, Any]) -> dict[str, Any]:
        delivered.append(bundle["envelope_id"])
        return {"status": "delivered", "envelope_digest": bundle["envelope_digest"]}

    env = _env(policy=FederationPolicy(max_audit_events=1, decision_window_seconds=86400), transport=transport)
    env.broker.send(_envelope(env), at=AT, actor_reference="FAC-A")
    assert len(delivered) == 1
    with pytest.raises(FederationValidationError, match="audit depth cap"):
        env.broker.send(
            _envelope(env, envelope_id="env-0002", idempotency_key="idem-0002"),
            at=AT,
            actor_reference="FAC-A",
        )
    assert len(delivered) == 1


def test_emergency_reason_catalogue_and_unconditional_expiry() -> None:
    with pytest.raises(FederationValidationError, match="emergency reason"):
        _grant(reason_code="unapproved")
    env = _env()
    valid = env.engine.evaluate(
        _request(emergency_grant=_grant(reason_code="trauma")), target_institution_id="FAC-B"
    )
    assert valid.allowed is True
    expired = env.engine.evaluate(
        _request(emergency_grant=_grant(reason_code="trauma", expires_at=PAST)),
        target_institution_id="FAC-B",
    )
    assert expired.allowed is False
