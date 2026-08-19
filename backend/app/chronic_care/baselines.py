from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite, sqrt
from statistics import median
from typing import Iterable


@dataclass(frozen=True)
class BaselineSnapshot:
    metric_code: str
    sample_count: int
    median: float | None
    mad: float | None
    lower_bound: float | None
    upper_bound: float | None
    confidence: float
    status: str
    reason: str
    generated_at: datetime


@dataclass(frozen=True)
class BaselineEvaluation:
    metric_code: str
    value: float
    is_anomaly: bool
    severity: str
    deviation_score: float | None
    confidence: float
    explanation: str
    requires_clinician_review: bool


class BaselineError(ValueError):
    pass


def _clean(values: Iterable[float]) -> list[float]:
    cleaned = [float(value) for value in values if isfinite(float(value))]
    if not cleaned:
        raise BaselineError("At least one finite historical value is required")
    return cleaned


def build_baseline(
    metric_code: str,
    values: Iterable[float],
    *,
    min_samples: int = 7,
    mad_multiplier: float = 3.5,
) -> BaselineSnapshot:
    if not metric_code.strip():
        raise BaselineError("metric_code is required")
    if min_samples < 3:
        raise BaselineError("min_samples must be at least 3")
    if mad_multiplier <= 0:
        raise BaselineError("mad_multiplier must be positive")

    cleaned = _clean(values)
    center = median(cleaned)
    deviations = [abs(value - center) for value in cleaned]
    mad = median(deviations)
    # 1.4826 makes MAD comparable to standard deviation for a normal distribution.
    robust_sigma = max(1.4826 * mad, 1e-9)
    margin = mad_multiplier * robust_sigma
    confidence = min(1.0, max(0.0, len(cleaned) / max(min_samples * 4, 1)))
    ready = len(cleaned) >= min_samples
    return BaselineSnapshot(
        metric_code=metric_code,
        sample_count=len(cleaned),
        median=center,
        mad=mad,
        lower_bound=center - margin,
        upper_bound=center + margin,
        confidence=round(confidence, 4),
        status="ready" if ready else "warming_up",
        reason=(
            "Personal baseline is ready for advisory anomaly detection"
            if ready
            else f"Need {min_samples - len(cleaned)} additional valid samples before alerting"
        ),
        generated_at=datetime.now(timezone.utc),
    )


def evaluate_against_baseline(
    baseline: BaselineSnapshot,
    value: float,
    *,
    alert_confidence_threshold: float = 0.75,
) -> BaselineEvaluation:
    numeric_value = float(value)
    if not isfinite(numeric_value):
        raise BaselineError("value must be finite")
    if not 0 <= alert_confidence_threshold <= 1:
        raise BaselineError("alert_confidence_threshold must be between 0 and 1")

    if baseline.status != "ready" or baseline.median is None or baseline.mad is None:
        return BaselineEvaluation(
            metric_code=baseline.metric_code,
            value=numeric_value,
            is_anomaly=False,
            severity="insufficient_data",
            deviation_score=None,
            confidence=baseline.confidence,
            explanation=baseline.reason,
            requires_clinician_review=False,
        )

    robust_sigma = max(1.4826 * baseline.mad, 1e-9)
    score = abs(numeric_value - baseline.median) / robust_sigma
    outside = numeric_value < (baseline.lower_bound or numeric_value) or numeric_value > (baseline.upper_bound or numeric_value)
    confident = baseline.confidence >= alert_confidence_threshold
    anomaly = outside and confident
    severity = "high" if anomaly and score >= 7 else "moderate" if anomaly else "normal"
    direction = "below" if numeric_value < baseline.median else "above"
    explanation = (
        f"{baseline.metric_code} is {direction} the patient's personal median "
        f"({baseline.median:.2f}) by robust score {score:.2f}; this is advisory and requires clinical context."
        if anomaly
        else f"{baseline.metric_code} remains within the patient's learned personal range."
    )
    return BaselineEvaluation(
        metric_code=baseline.metric_code,
        value=numeric_value,
        is_anomaly=anomaly,
        severity=severity,
        deviation_score=round(score, 4),
        confidence=baseline.confidence,
        explanation=explanation,
        requires_clinician_review=anomaly,
    )
