"""High-level entry point for the synthetic laboratory vertical slice.

It composes existing canonical components in a fail-closed order:
bind → assess → authorize → project → queue → aggregate. No route, migration,
external connector, or production configuration is created or changed. This
slice never binds a real actor or real result; the local release policy is not
a substitute for the canonical Authorization Decision Engine, which remains
mandatory for any production clinical access or release.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from app.integration.fhir_r4_exchange import _safe_audit_resource_id
from app.lab_slice.analytics_bridge import (
    assert_deidentified,
    build_public_health_report,
    build_surveillance_signal,
)
from app.lab_slice.decision_engine import assess_result, authorize_release
from app.lab_slice.event_pipeline import PipelineSummary, SyntheticLabEventPipeline
from app.lab_slice.fhir_projector import build_bundle
from app.lab_slice.models import (
    RELEASE_PENDING,
    RELEASE_QUARANTINED,
    SyntheticLabCase,
    SyntheticResult,
)
from app.lab_slice.terminology_bindings import bind_test
from app.national.intelligence.laboratory.analytics import DeltaCheckEngine
from app.public_health.domain.entities import PublicHealthReport, SurveillanceSignal
from app.services.reference.national_lab_catalog import NationalLaboratoryCatalog


@dataclass(frozen=True, slots=True)
class SliceResult:
    released: tuple[SyntheticResult, ...]
    quarantined: tuple[str, ...]
    bundles: tuple[dict[str, Any], ...]
    pipeline: PipelineSummary
    surveillance_signal: SurveillanceSignal
    public_health_report: PublicHealthReport


def execute_synthetic_lab_slice(
    cases: Sequence[SyntheticLabCase],
    *,
    reviewer: str,
    reason: str,
    idempotency_prefix: str,
    disease_code: str,
    region: str,
    population: int,
    catalog: NationalLaboratoryCatalog | None = None,
    delta_engine: DeltaCheckEngine | None = None,
) -> SliceResult:
    """Run one bounded, synthetic batch through the composed capabilities."""
    if not reason.strip() or not idempotency_prefix.strip():
        raise ValueError("reason and idempotency_prefix are required")

    active_catalog = catalog or NationalLaboratoryCatalog()
    if not active_catalog.count().get("tests", 0):
        active_catalog.seed_common_tests()
    active_delta = delta_engine or DeltaCheckEngine()
    for test_code in {case.result.test_code for case in cases}:
        active_delta.set_delta_threshold(test_code, 2.0, 20.0)

    pipeline = SyntheticLabEventPipeline()
    released: list[SyntheticResult] = []
    quarantined: list[str] = []
    bundles: list[dict[str, Any]] = []

    for case in cases:
        binding = bind_test(active_catalog, case.result.test_code)
        decision = assess_result(
            order=case.order,
            specimen=case.specimen,
            result=case.result,
            qc=case.qc,
            binding=binding,
            delta_engine=active_delta,
        )
        safe_result_id = _safe_audit_resource_id(case.result.result_id)
        if decision.status == RELEASE_PENDING:
            released_decision = authorize_release(
                decision,
                reviewer=reviewer,
                reason=reason,
                idempotency_key=f"{idempotency_prefix}-{case.result.result_id}",
            )
            bundle = build_bundle(
                patient=case.patient,
                order=case.order,
                specimen=case.specimen,
                result=case.result,
                decision=released_decision,
                binding=binding,
            )
            bundles.append(bundle)
            released.append(case.result)
            pipeline.publish(SyntheticLabEventPipeline.released_event(case.result.result_id))
            pipeline.audit.record(
                action="lab_slice.release",
                outcome="released",
                resource_type="Observation",
                resource_id=safe_result_id,
            )
        elif decision.status == RELEASE_QUARANTINED:
            quarantined.append(case.result.result_id)
            pipeline.audit.record(
                action="lab_slice.release",
                outcome="quarantined",
                resource_type="Observation",
                resource_id=safe_result_id,
            )

    pipeline_summary = pipeline.process()
    signal = build_surveillance_signal(
        released,
        disease_code=disease_code,
        region=region,
        population=population,
    )
    report = build_public_health_report(signal)
    assert_deidentified(report, released)

    return SliceResult(
        released=tuple(released),
        quarantined=tuple(quarantined),
        bundles=tuple(bundles),
        pipeline=pipeline_summary,
        surveillance_signal=signal,
        public_health_report=report,
    )
