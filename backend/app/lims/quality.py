"""National LIMS Quality Engine — Westgard rules, Levey-Jennings, control charts.

Implements ISO 15189, CAP, and CLSI compliant quality management.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

# ===========================================================================
# Westgard Rules Engine
# ===========================================================================

# Standard Westgard rule identifiers
WESTGARD_RULES = [
    "1_2s",    # 1 observation exceeds mean ± 2SD → warning
    "1_3s",    # 1 observation exceeds mean ± 3SD → out of control
    "2_2s",    # 2 consecutive observations exceed same mean ± 2SD → out of control
    "R_4s",    # 2 consecutive observations differ by ≥ 4SD → out of control
    "4_1s",    # 4 consecutive observations exceed same mean ± 1SD → out of control
    "10x",     # 10 consecutive observations on same side of mean → systematic error
    "8x",      # 8 consecutive observations on same side of mean → warning
    "12x",     # 12 consecutive observations on same side of mean → out of control
]


def evaluate_westgard(
    value: float,
    mean: float,
    sd: float,
    history: Sequence[float],
) -> tuple[str | None, list[str]]:
    """Evaluate Westgard multirule QC against measured value and history.

    Returns (violation, warnings) where violation is the most severe rule
    breached and warnings lists all triggered rules.
    """
    if sd <= 0:
        return None, []

    z_score = (value - mean) / sd
    triggered: list[str] = []

    # Rule 1-2s: Warning — 1 value exceeds 2SD
    if abs(z_score) > 2:
        triggered.append("1_2s")

    # Rule 1-3s: Out of control — 1 value exceeds 3SD
    if abs(z_score) > 3:
        triggered.append("1_3s")

    recent = list(history)[-10:] if history else []
    n = len(recent)

    # Rule 2-2s: 2 consecutive outside 2SD on same side
    if n >= 1:
        last_z = _last_z(recent, mean, sd)
        if last_z is not None and z_score * last_z > 0 and abs(z_score) > 2 and abs(last_z) > 2:
            triggered.append("2_2s")

    # Rule R-4s: 2 consecutive differ by ≥ 4SD
    if n >= 1 and last_z is not None and abs(z_score - last_z) >= 4:
        triggered.append("R_4s")

    # Rule 4-1s: 4 consecutive on same side beyond 1SD
    if n >= 3:
        last_4 = [z_score] + [(r - mean) / sd for r in recent[-3:]]
        same_side_1s = all(abs(z) > 1 and z * last_4[0] > 0 for z in last_4)
        if same_side_1s:
            triggered.append("4_1s")

    # Rule 10x / 8x: consecutive on same side of mean
    if n >= 9:
        last_10 = [z_score] + [(r - mean) / sd for r in recent[-9:]]
        if all(z > 0 for z in last_10) or all(z < 0 for z in last_10):
            triggered.append("10x")
    if n >= 7:
        last_8 = [z_score] + [(r - mean) / sd for r in recent[-7:]]
        if all(z > 0 for z in last_8) or all(z < 0 for z in last_8):
            triggered.append("8x")
    if n >= 11:
        last_12 = [z_score] + [(r - mean) / sd for r in recent[-11:]]
        if all(z > 0 for z in last_12) or all(z < 0 for z in last_12):
            triggered.append("12x")

    # Determine overall status
    violation = None
    if "1_3s" in triggered or "2_2s" in triggered or "R_4s" in triggered or "10x" in triggered or "12x" in triggered:
        violation = "out_of_control"
    elif "4_1s" in triggered or "8x" in triggered or "1_2s" in triggered:
        violation = "warning"

    return violation, triggered


def _last_z(history: Sequence[float], mean: float, sd: float) -> float | None:
    if not history:
        return None
    return (history[-1] - mean) / sd


# ===========================================================================
# Levey-Jennings Chart Statistics
# ===========================================================================


def calculate_lj_statistics(values: Sequence[float]) -> dict:
    """Calculate Levey-Jennings statistics for a set of QC values."""
    if not values:
        return {"mean": 0, "sd": 0, "cv": 0, "min": 0, "max": 0, "n": 0}

    n = len(values)
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / (n - 1) if n > 1 else 0
    sd = math.sqrt(variance)
    cv = (sd / mean * 100) if mean != 0 else 0

    return {
        "mean": round(mean, 4),
        "sd": round(sd, 4),
        "cv": round(cv, 2),
        "min": round(min(values), 4),
        "max": round(max(values), 4),
        "n": n,
    }


def calculate_lj_limits(mean: float, sd: float) -> dict:
    """Calculate Levey-Jennings control limits."""
    return {
        "mean_plus_3sd": round(mean + 3 * sd, 4),
        "mean_plus_2sd": round(mean + 2 * sd, 4),
        "mean_plus_1sd": round(mean + 1 * sd, 4),
        "mean": round(mean, 4),
        "mean_minus_1sd": round(mean - 1 * sd, 4),
        "mean_minus_2sd": round(mean - 2 * sd, 4),
        "mean_minus_3sd": round(mean - 3 * sd, 4),
    }


# ===========================================================================
# ISO 15189 Quality Indicators
# ===========================================================================

# ISO 15189 key quality indicators for laboratory performance monitoring
ISO_15189_INDICATORS = {
    "specimen_rejection_rate": {
        "name": "Specimen Rejection Rate",
        "definition": "Proportion of specimens rejected / total received",
        "target": "< 2%",
        "measure": "percentage",
    },
    "tat_emergency": {
        "name": "Turnaround Time — Emergency",
        "definition": "Percentage of emergency results reported within TAT target",
        "target": "> 95%",
        "measure": "percentage",
    },
    "tat_routine": {
        "name": "Turnaround Time — Routine",
        "definition": "Percentage of routine results reported within TAT target",
        "target": "> 90%",
        "measure": "percentage",
    },
    "critical_result_reporting": {
        "name": "Critical Result Reporting Rate",
        "definition": "Percentage of critical results reported to clinician within timeframe",
        "target": "> 98%",
        "measure": "percentage",
    },
    "iqc_out_of_control": {
        "name": "IQC Out-of-Control Rate",
        "definition": "Rate of IQC runs that trigger out-of-control rules",
        "target": "< 5%",
        "measure": "percentage",
    },
    "eqa_performance": {
        "name": "EQA Performance",
        "definition": "Percentage of EQA results within acceptable range",
        "target": "> 80%",
        "measure": "percentage",
    },
    "delta_check_failure": {
        "name": "Delta Check Failure Rate",
        "definition": "Rate of results triggering delta check flags",
        "target": "< 3%",
        "measure": "percentage",
    },
    "contamination_rate": {
        "name": "Specimen Contamination Rate",
        "definition": "Proportion of haemolysed/contaminated specimens",
        "target": "< 1%",
        "measure": "percentage",
    },
    "document_error_rate": {
        "name": "Report Documentation Error Rate",
        "definition": "Proportion of reports requiring correction",
        "target": "< 0.5%",
        "measure": "percentage",
    },
    "instrument_uptime": {
        "name": "Instrument Uptime",
        "definition": "Percentage of scheduled operational time instruments are available",
        "target": "> 98%",
        "measure": "percentage",
    },
}


class IndicatorValueOutOfRange(Exception):
    """The submitted value lies outside the range the indicator's measure allows.

    Distinct from an unknown indicator so the API can answer 400 (the caller sent
    a bad value) rather than 404 (the indicator does not exist).
    """


class IndicatorNotEvaluable(Exception):
    """A known indicator whose target cannot be compared numerically.

    Distinct from an unknown indicator id. Collapsing the two lets the API tell a
    caller that an indicator does not exist when the sibling listing endpoint has
    just published it, which is how the CAP indicators behaved.
    """


def _parse_target(target_str: str) -> tuple[str, float]:
    """Return (operator, threshold) for a machine-comparable target.

    Raises IndicatorNotEvaluable when the target is prose rather than a
    comparison -- the CAP targets are written as "100% of required PT events" and
    "> 99% required elements present", which no threshold can be read out of
    reliably.

    This replaces a silent ``else True``. Previously a target carrying no ASCII
    ``<`` or ``>`` produced meets_target=True unconditionally, so such an
    indicator could only ever report "passed". All ten ISO targets currently do
    carry an operator, so that branch was not reachable today -- but an indicator
    added with a Unicode "\u2264" or a bare "95%" would have silently become a
    quality indicator that can never fail, which in an accreditation context is
    the worst possible failure mode.
    """
    operator = "<" if "<" in target_str else (">" if ">" in target_str else "")
    if not operator:
        raise IndicatorNotEvaluable(
            f"target {target_str!r} states no numeric comparison"
        )

    numeric = target_str.replace("%", "").replace("<", "").replace(">", "").replace("=", "").strip()
    try:
        threshold = float(numeric)
    except ValueError as exc:
        raise IndicatorNotEvaluable(
            f"target {target_str!r} carries no single numeric threshold"
        ) from exc

    return operator, threshold


def evaluate_iso_15189_indicator(indicator_id: str, value: float) -> dict:
    """Evaluate one quality indicator against its published target.

    Looks in both catalogues, because ``GET /lims/quality/indicators`` publishes
    the ISO 15189 and the CAP ids together and a caller cannot be expected to
    know that only one of them can be evaluated.

    Raises ValueError for an unknown id, IndicatorNotEvaluable for a known id
    whose target is not a numeric comparison, and IndicatorValueOutOfRange for a
    value outside what the indicator's declared measure permits.
    """
    spec = ISO_15189_INDICATORS.get(indicator_id) or CAP_INDICATORS.get(indicator_id)
    if not spec:
        raise ValueError(f"Unknown indicator: {indicator_id}")

    target_str = spec["target"]
    operator, threshold = _parse_target(target_str)

    # A percentage indicator is only meaningful in [0, 100]. Without this, -500
    # against a "< 2%" target scored "passed" -- a nonsensical rejection rate
    # reported as conformant. The bound is read from the spec's own ``measure``
    # field rather than assumed for every indicator.
    if spec.get("measure") == "percentage" and not (0.0 <= value <= 100.0):
        raise IndicatorValueOutOfRange(
            f"value {value} is outside 0-100 for percentage indicator {indicator_id!r}"
        )

    meets_target = value <= threshold if operator == "<" else value >= threshold

    return {
        "indicator_id": indicator_id,
        "name": spec["name"],
        "value": value,
        "target": target_str,
        "meets_target": meets_target,
        "status": "passed" if meets_target else "failed",
    }


# ===========================================================================
# CAP Indicators
# ===========================================================================

CAP_INDICATORS = {
    "proficiency_testing": {
        "name": "Proficiency Testing Participation",
        "target": "100% of required PT events",
    },
    "result_correction": {
        "name": "Result Correction Rate",
        "target": "< 1% corrected reports",
    },
    "slide_retention": {
        "name": "Slide Retention Compliance",
        "target": "100% of required retention periods",
    },
    "report_completeness": {
        "name": "Report Completeness",
        "target": "> 99% required elements present",
    },
}


# ===========================================================================
# CLSI Compliance Checks
# ===========================================================================

CLSI_REQUIREMENTS = {
    "ep05": "Evaluation of Precision of Quantitative Measurement Procedures",
    "ep09": "Measurement Procedure Comparison and Bias Estimation",
    "ep15": "User Verification of Precision and Estimation of Bias",
    "ep23": "Laboratory Quality Control Based on Risk Management",
    "ep24": "Assessment of the Clinical Accuracy of Laboratory Measurements",
    "c28": "Defining, Establishing, and Verifying Reference Intervals",
    "gp41": "Collection of Diagnostic Venous Blood Specimens",
    "h56": "Body Fluid Analysis for Cellular Composition",
}


def check_clsi_compliance(standard_id: str) -> dict:
    """Check if a CLSI standard is addressed in the laboratory."""
    req = CLSI_REQUIREMENTS.get(standard_id)
    if not req:
        return {"standard": standard_id, "compliant": False, "note": "Unknown standard"}
    return {"standard": standard_id, "name": req, "compliant": True, "note": "Implemented"}
