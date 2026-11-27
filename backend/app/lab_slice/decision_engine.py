"""Pure, fail-closed release policy for the synthetic laboratory slice.

This module is not the canonical Authorization Decision Engine and must not be
used to authorize real patient data access. It composes the existing LIMS state
machine, Westgard engine, and delta engine to classify synthetic results, and
it never writes to a database, calls a route, or grants release without an
explicit synthetic reviewer. Critical and out-of-reference results are
quarantined and cannot be promoted from this slice.
"""

from __future__ import annotations

import hashlib
from dataclasses import replace
from datetime import datetime

from app._compat import UTC
from app.lab_slice.models import (
    RELEASE_PENDING,
    RELEASE_QUARANTINED,
    RELEASE_REJECTED,
    RELEASE_RELEASED,
    ReleaseDecision,
    SyntheticOrder,
    SyntheticQCControl,
    SyntheticResult,
    SyntheticSpecimen,
    require_synthetic_id,
)
from app.lab_slice.terminology_bindings import BINDING_UNMAPPED, TerminologyBinding
from app.lims.quality import evaluate_westgard
from app.lims.state_machine import can_transition_order, can_transition_specimen
from app.national.intelligence.laboratory.analytics import DeltaCheckEngine


def _decision_id(result_id: str, status: str, reasons: tuple[str, ...], suffix: str = "") -> str:
    material = f"{result_id}:{status}:{','.join(reasons)}:{suffix}"
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:20]
    return f"synthetic-decision-{digest}"


def _is_outside_reference(result: SyntheticResult) -> bool:
    return result.value < result.reference_low or result.value > result.reference_high


def _is_critical(result: SyntheticResult) -> bool:
    low_breach = result.critical_low is not None and result.value <= result.critical_low
    high_breach = result.critical_high is not None and result.value >= result.critical_high
    return low_breach or high_breach


def assess_result(
    *,
    order: SyntheticOrder,
    specimen: SyntheticSpecimen,
    result: SyntheticResult,
    qc: SyntheticQCControl,
    binding: TerminologyBinding,
    delta_engine: DeltaCheckEngine | None = None,
) -> ReleaseDecision:
    """Return a bounded release decision; never release automatically."""
    reasons: list[str] = []
    if not can_transition_order(order.status, "validated"):
        reasons.append("invalid_order_transition")
    if not can_transition_specimen(specimen.state, "verified"):
        reasons.append("invalid_specimen_transition")
    if binding.status == BINDING_UNMAPPED:
        reasons.append("terminology_unmapped")
    if result.unit != binding.unit:
        reasons.append("unit_mismatch")

    qc_violation, qc_rules = evaluate_westgard(qc.value, qc.mean, qc.sd, qc.history)
    if qc_violation == "out_of_control":
        reasons.append("qc_out_of_control")
        reasons.extend(f"qc_rule:{rule}" for rule in qc_rules)
    elif qc_violation == "warning":
        reasons.append("qc_warning")
        reasons.extend(f"qc_rule:{rule}" for rule in qc_rules)

    if delta_engine is not None:
        delta = delta_engine.evaluate_delta(
            result.patient_id,
            result.test_code,
            result.value,
            result.previous_value,
        )
        if delta["significant"]:
            reasons.append("delta_check_significant")

    if _is_outside_reference(result):
        reasons.append("outside_reference_range")
    if _is_critical(result):
        reasons.append("critical_value")

    quarantining_reasons = {
        "invalid_order_transition",
        "invalid_specimen_transition",
        "terminology_unmapped",
        "unit_mismatch",
        "qc_out_of_control",
        "outside_reference_range",
        "critical_value",
    }
    if any(reason in quarantining_reasons for reason in reasons):
        status = RELEASE_QUARANTINED
    else:
        status = RELEASE_PENDING
        if not reasons:
            reasons.append("manual_release_required")

    return ReleaseDecision(
        decision_id=_decision_id(result.result_id, status, tuple(reasons)),
        result_id=result.result_id,
        status=status,
        reasons=tuple(reasons),
    )


def authorize_release(
    decision: ReleaseDecision,
    *,
    reviewer: str,
    reason: str,
    idempotency_key: str,
) -> ReleaseDecision:
    """Promote only a pending decision to released with explicit review."""
    require_synthetic_id(reviewer, "reviewer")
    if not reason.strip() or not idempotency_key.strip():
        raise ValueError("reason and idempotency_key are required")
    if decision.status != RELEASE_PENDING:
        return decision
    reasons = (*decision.reasons, "manual_release_authorized")
    return replace(
        decision,
        decision_id=_decision_id(decision.result_id, RELEASE_RELEASED, reasons, idempotency_key),
        status=RELEASE_RELEASED,
        reasons=reasons,
        reviewer=reviewer,
        reason=reason,
        idempotency_key=idempotency_key,
        released_at=datetime.now(UTC).isoformat(),
    )


def reject_release(decision: ReleaseDecision, *, reason: str) -> ReleaseDecision:
    """Explicitly reject a pending or review decision."""
    if not reason.strip() or decision.status == RELEASE_RELEASED:
        raise ValueError("a released decision cannot be rejected in this slice")
    if decision.status == RELEASE_REJECTED:
        return decision
    reasons = (*decision.reasons, "manually_rejected")
    return replace(
        decision,
        decision_id=_decision_id(decision.result_id, RELEASE_REJECTED, reasons),
        status=RELEASE_REJECTED,
        reasons=reasons,
        reason=reason,
    )
