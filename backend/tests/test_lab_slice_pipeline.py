"""Synthetic laboratory vertical slice tests.

All data is synthetic. These tests compose existing LIMS, QC, FHIR, offline, and
surveillance primitives without routes, migrations, real patient data, or
external services.
"""

from __future__ import annotations

import json
from dataclasses import asdict, replace

import pytest
from app.integration.fhir_r4_exchange import (
    FHIRContractError,
    validate_synthetic_bundle,
)
from app.lab_slice.analytics_bridge import (
    assert_deidentified,
    build_public_health_report,
    build_surveillance_signal,
)
from app.lab_slice.decision_engine import assess_result, authorize_release, reject_release
from app.lab_slice.event_pipeline import SyntheticLabEventPipeline
from app.lab_slice.fhir_projector import build_bundle
from app.lab_slice.models import (
    RELEASE_PENDING,
    RELEASE_QUARANTINED,
    RELEASE_RELEASED,
    CustodyEvent,
    SyntheticLabCase,
    SyntheticOrder,
    SyntheticPatient,
    SyntheticQCControl,
    SyntheticResult,
    SyntheticSpecimen,
)
from app.lab_slice.service import execute_synthetic_lab_slice
from app.lab_slice.terminology_bindings import (
    BINDING_LOCAL,
    BINDING_MAPPED,
    BINDING_UNMAPPED,
    bind_test,
)
from app.national.fhir.validation import FHIRValidationEngine
from app.national.intelligence.laboratory.analytics import DeltaCheckEngine
from app.services.reference.national_lab_catalog import NationalLaboratoryCatalog


def _catalog() -> NationalLaboratoryCatalog:
    catalog = NationalLaboratoryCatalog()
    catalog.seed_common_tests()
    return catalog


def _delta() -> DeltaCheckEngine:
    engine = DeltaCheckEngine()
    engine.set_delta_threshold("GLU", 2.0, 20.0)
    return engine


def _case(suffix: str = "001", *, value: float = 90.0, order_status: str = "completed") -> SyntheticLabCase:
    patient = SyntheticPatient(
        patient_id=f"synthetic-patient-{suffix}",
        age_years=35,
        region="synthetic-region",
    )
    order = SyntheticOrder(
        order_id=f"synthetic-order-{suffix}",
        patient_id=patient.patient_id,
        test_code="GLU",
        status=order_status,
    )
    specimen = SyntheticSpecimen(
        specimen_id=f"synthetic-specimen-{suffix}",
        order_id=order.order_id,
        patient_id=patient.patient_id,
        specimen_type="Serum",
        state="analyzed",
        custody=(
            CustodyEvent(
                event_id=f"synthetic-custody-{suffix}",
                location="synthetic-facility-001",
                actor="synthetic-phlebotomist-001",
                recorded_at="2026-11-25T12:00:00+00:00",
            ),
        ),
    )
    qc = SyntheticQCControl(
        control_id=f"synthetic-qc-{suffix}",
        test_code="GLU",
        value=100.0,
        mean=100.0,
        sd=2.0,
        history=(99.0, 101.0),
    )
    result = SyntheticResult(
        result_id=f"synthetic-result-{suffix}",
        order_id=order.order_id,
        specimen_id=specimen.specimen_id,
        patient_id=patient.patient_id,
        test_code="GLU",
        value=value,
        unit="mg/dL",
        reference_low=70.0,
        reference_high=110.0,
        critical_low=50.0,
        critical_high=300.0,
        previous_value=88.0,
        reportable_condition="influenza",
    )
    return SyntheticLabCase(
        patient=patient,
        order=order,
        specimen=specimen,
        result=result,
        qc=qc,
    )


def _decision(case: SyntheticLabCase):
    return assess_result(
        order=case.order,
        specimen=case.specimen,
        result=case.result,
        qc=case.qc,
        binding=bind_test(_catalog(), case.result.test_code),
        delta_engine=_delta(),
    )


def _released(case: SyntheticLabCase):
    decision = authorize_release(
        _decision(case),
        reviewer="synthetic-reviewer-001",
        reason="synthetic documented review",
        idempotency_key="synthetic-idem-001",
    )
    return decision, build_bundle(
        patient=case.patient,
        order=case.order,
        specimen=case.specimen,
        result=case.result,
        decision=decision,
        binding=bind_test(_catalog(), case.result.test_code),
    )


def test_terminology_binding_distinguishes_mapped_local_and_unmapped() -> None:
    catalog = _catalog()

    mapped = bind_test(catalog, "GLU")
    assert mapped.status == BINDING_MAPPED
    assert mapped.code_system == "http://loinc.org"

    unmapped = bind_test(catalog, "UNKNOWN-SYNTHETIC-TEST")
    assert unmapped.status == BINDING_UNMAPPED
    assert unmapped.code_system == "urn:gula:lab-test-name"

    local = bind_test(catalog, "INR")
    assert local.status == BINDING_LOCAL
    assert local.code_system == "urn:gula:lab-test-name"
    assert bind_test(catalog, "GLU", unit="").status == BINDING_UNMAPPED


def test_valid_synthetic_result_requires_manual_release() -> None:
    decision = _decision(_case())

    assert decision.status == RELEASE_PENDING
    assert "manual_release_required" in decision.reasons
    assert decision.reviewer is None

    released = authorize_release(
        decision,
        reviewer="synthetic-reviewer-001",
        reason="synthetic documented review",
        idempotency_key="synthetic-idem-001",
    )
    assert released.status == RELEASE_RELEASED
    assert released.reviewer == "synthetic-reviewer-001"
    assert released.idempotency_key == "synthetic-idem-001"


def test_qc_out_of_control_is_quarantined_and_cannot_be_released() -> None:
    case = _case()
    case = replace(case, qc=replace(case.qc, value=108.0))
    decision = _decision(case)

    assert decision.status == RELEASE_QUARANTINED
    assert "qc_out_of_control" in decision.reasons
    assert any(reason.startswith("qc_rule:") for reason in decision.reasons)
    assert authorize_release(
        decision,
        reviewer="synthetic-reviewer-001",
        reason="synthetic documented review",
        idempotency_key="synthetic-idem-002",
    ) == decision


def test_invalid_state_transitions_are_quarantined() -> None:
    case = _case(order_status="pending")
    decision = _decision(case)

    assert decision.status == RELEASE_QUARANTINED
    assert "invalid_order_transition" in decision.reasons


def test_critical_value_is_quarantined_and_cannot_be_released() -> None:
    case = _case(value=350.0)
    decision = _decision(case)

    assert decision.status == RELEASE_QUARANTINED
    assert "critical_value" in decision.reasons
    assert "outside_reference_range" in decision.reasons
    assert "delta_check_significant" in decision.reasons
    assert authorize_release(
        decision,
        reviewer="synthetic-reviewer-001",
        reason="synthetic documented review",
        idempotency_key="synthetic-idem-003",
    ) == decision
    rejected = reject_release(decision, reason="synthetic safety hold")
    assert rejected.status == "rejected"


def test_fhir_bundle_is_structurally_valid_and_explicitly_synthetic() -> None:
    _, bundle = _released(_case())

    assert validate_synthetic_bundle(bundle) == []
    validator = FHIRValidationEngine()
    for entry in bundle["entry"]:
        assert validator.validate(entry["resource"]).valid is True
        assert entry["fullUrl"].startswith("urn:uuid:synthetic-")
    serialized = json.dumps(bundle, sort_keys=True)
    assert "national_id" not in serialized
    assert "synthetic-patient-001" in serialized


def test_unreleased_bundle_projection_is_denied() -> None:
    case = _case()
    with pytest.raises(FHIRContractError):
        build_bundle(
            patient=case.patient,
            order=case.order,
            specimen=case.specimen,
            result=case.result,
            decision=_decision(case),
            binding=bind_test(_catalog(), case.result.test_code),
        )


def test_event_pipeline_dedupes_and_replay_is_idempotent() -> None:
    pipeline = SyntheticLabEventPipeline()
    event = SyntheticLabEventPipeline.released_event("synthetic-result-001")

    assert pipeline.publish(event) is True
    assert pipeline.publish(event) is False
    first = pipeline.process()
    assert first.delivered == ("synthetic-result-001-lims.result.validated",)
    assert first.duplicates == ()
    assert first.conflicts == ()

    replayed = SyntheticLabEventPipeline.released_event("synthetic-result-001", version=2)
    assert pipeline.publish(replayed) is True
    second = pipeline.process()
    assert second.delivered == ()
    assert second.duplicates == ("synthetic-result-001-lims.result.validated",)
    assert second.conflicts == ()
    outcomes = [outcome.outcome for outcome in pipeline.audit.decisions]
    assert outcomes.count("delivered") == 1
    assert outcomes.count("duplicate") == 1


def test_clinical_conflict_is_failed_closed() -> None:
    pipeline = SyntheticLabEventPipeline()
    event = SyntheticLabEventPipeline.released_event("synthetic-result-002", version=0)
    assert pipeline.publish(event) is True

    summary = pipeline.process()
    assert summary.delivered == ()
    assert summary.conflicts == ("synthetic-result-002-lims.result.validated",)
    assert any(outcome.outcome == "quarantined" for outcome in pipeline.audit.decisions)


def test_end_to_end_slice_releases_valid_case_and_quarantines_invalid_case() -> None:
    valid = _case("101")
    invalid = _case(order_status="pending", suffix="102")
    invalid = replace(invalid, result=replace(invalid.result, reportable_condition=None))

    result = execute_synthetic_lab_slice(
        [valid, invalid],
        reviewer="synthetic-reviewer-001",
        reason="synthetic documented review",
        idempotency_prefix="synthetic-batch-001",
        disease_code="influenza",
        region="synthetic-region",
        population=100000,
    )

    assert len(result.released) == 1
    assert result.quarantined == ("synthetic-result-102",)
    assert len(result.bundles) == 1
    assert result.pipeline.delivered == ("synthetic-result-101-lims.result.validated",)
    assert result.surveillance_signal.case_count == 1
    assert result.public_health_report.total_cases == 1
    assert result.public_health_report.alerts_raised == 0
    assert_deidentified(result.public_health_report, result.released)


def test_end_to_end_slice_never_releases_critical_results() -> None:
    critical = _case("103", value=350.0)

    result = execute_synthetic_lab_slice(
        [critical],
        reviewer="synthetic-reviewer-001",
        reason="synthetic documented review",
        idempotency_prefix="synthetic-batch-002",
        disease_code="influenza",
        region="synthetic-region",
        population=100000,
    )

    assert result.released == ()
    assert result.quarantined == ("synthetic-result-103",)
    assert result.bundles == ()
    assert result.pipeline.delivered == ()
    assert result.surveillance_signal.case_count == 0


def test_public_health_report_is_deidentified_and_value_free() -> None:
    case = _case(value=123.456)
    signal = build_surveillance_signal(
        [case.result],
        disease_code="influenza",
        region="synthetic-region",
        population=100000,
    )
    report = build_public_health_report(signal)
    serialized = json.dumps(asdict(report), sort_keys=True)

    assert case.result.patient_id not in serialized
    assert case.result.result_id not in serialized
    assert "123.456" not in serialized
    assert_deidentified(report, [case.result])
