"""De-identified public-health projection from released synthetic results.

This bridge reuses the existing surveillance engine and public-health report
contracts. It emits counts and signals only; no patient identifier, raw result
value, or identifiers from the laboratory slice are retained.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import asdict
from datetime import datetime

from app._compat import UTC
from app.lab_slice.models import SyntheticResult
from app.national.intelligence.public_health.surveillance import DiseaseSurveillanceEngine
from app.public_health.domain.entities import PublicHealthReport, SurveillanceSignal


def _signal_id(disease_code: str, region: str) -> str:
    digest = hashlib.sha256(f"{disease_code}:{region}".encode()).hexdigest()[:12]
    return f"synthetic-signal-{digest}"


def _alert_level(status: str) -> str:
    if status in {"high", "critical"}:
        return "warning"
    if status == "medium":
        return "watch"
    return "information"


def build_surveillance_signal(
    results: Sequence[SyntheticResult],
    *,
    disease_code: str,
    region: str,
    population: int,
    period_days: int = 30,
) -> SurveillanceSignal:
    """Aggregate released results into one de-identified surveillance signal."""
    if population <= 0:
        raise ValueError("population must be positive")
    case_count = sum(1 for result in results if result.reportable_condition == disease_code)
    engine = DiseaseSurveillanceEngine()
    engine.report_cases(disease_code, region, case_count, population)
    report = engine.monitor_disease(disease_code, region, period_days)
    recommendation = "; ".join(report.recommendations) or "Continue routine surveillance"
    return SurveillanceSignal(
        id=_signal_id(disease_code, region),
        disease=disease_code,
        region=region,
        case_count=case_count,
        expected_count=int(report.expected_cases),
        baseline_period_days=period_days,
        z_score=report.anomaly_score,
        alert_level=_alert_level(report.status),
        detected_at=datetime.now(UTC).isoformat(),
        recommendation=recommendation,
    )


def build_public_health_report(signal: SurveillanceSignal) -> PublicHealthReport:
    """Return a counts-only report suitable for synthetic review."""
    return PublicHealthReport(
        id=f"synthetic-report-{signal.id}",
        report_type="synthetic-slice",
        period_start=signal.detected_at,
        period_end=signal.detected_at,
        region=signal.region,
        total_cases=signal.case_count,
        total_deaths=0,
        diseases_reported=[
            {
                "disease_code": signal.disease,
                "case_count": signal.case_count,
                "expected_count": signal.expected_count,
            },
        ],
        outbreaks_active=0,
        alerts_raised=1 if signal.alert_level != "information" else 0,
        vaccination_coverage_pct=0.0,
        key_findings="Synthetic laboratory signals only; no real case data.",
        recommendations=signal.recommendation,
        published_by="synthetic-lab-slice",
        published_at=signal.detected_at,
    )


def assert_deidentified(
    report: PublicHealthReport,
    results: Sequence[SyntheticResult],
) -> None:
    """Fail if any slice identifier leaked into the public-health report."""
    serialized = json.dumps(asdict(report), sort_keys=True)
    for result in results:
        if result.patient_id in serialized or result.result_id in serialized:
            raise ValueError("de-identification check failed")
