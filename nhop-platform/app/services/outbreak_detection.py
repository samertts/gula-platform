"""Outbreak detection over the national disease-case stream.

Three public entry points, all pure read-only over the ORM session:

* :func:`check_outbreak`        - hourly background scan; returns alerts
* :func:`get_disease_heatmap`   - geographic distribution for a disease
* :func:`get_resistance_report` - antibiotic resistance surveillance

The detector compares the last 24 hours against a 30-day daily baseline per
(disease, province). Because the last 24h are included in the 30-day window
we subtract them out before averaging — otherwise a single huge day would
mask itself. The baseline therefore uses the 29 prior daily counts.

Severity thresholds (from the spec):
    ratio > 5x  -> critical
    ratio > 2x  -> warning
anything lower is not reported.

A minimum absolute count (``_MIN_CASES``) suppresses noise when the
baseline is near zero: 1 case one day and 3 the next is a 3x ratio but not
a public-health signal.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from ..models.antibiotic_sensitivity import AntibioticSensitivity
from ..models.disease_case import DiseaseCase


# ─── Tunables ───────────────────────────────────────────────────────────────

WARNING_RATIO  = 2.0
CRITICAL_RATIO = 5.0
BASELINE_DAYS  = 30
_MIN_CASES     = 3   # ignore (disease, province) pairs with fewer than N in 24h


# ─── Public dataclasses ─────────────────────────────────────────────────────

@dataclass(frozen=True)
class OutbreakAlert:
    disease_code: str
    disease_name: Optional[str]
    province: str
    current_count: int
    baseline_avg: float
    ratio: float
    severity: str            # "warning" | "critical"
    detected_at: datetime


# ─── check_outbreak ─────────────────────────────────────────────────────────

def _classify(ratio: float) -> Optional[str]:
    if ratio > CRITICAL_RATIO:
        return "critical"
    if ratio > WARNING_RATIO:
        return "warning"
    return None


def check_outbreak(db: Session, *, now: Optional[datetime] = None) -> list[OutbreakAlert]:
    """Scan the last 24h vs the prior 29-day baseline and emit alerts.

    ``now`` is injectable for testability; defaults to UTC now.
    """
    now = now or datetime.now(timezone.utc)
    window_start   = now - timedelta(hours=24)
    baseline_start = now - timedelta(days=BASELINE_DAYS)

    # Current-window counts per (disease_code, province).
    current_rows = (
        db.query(
            DiseaseCase.disease_code,
            DiseaseCase.province,
            func.max(DiseaseCase.disease_name).label("disease_name"),
            func.count(DiseaseCase.id).label("current_count"),
        )
        .filter(DiseaseCase.is_positive.is_(True))
        .filter(DiseaseCase.reported_at >= window_start)
        .filter(DiseaseCase.reported_at <= now)
        .group_by(DiseaseCase.disease_code, DiseaseCase.province)
        .having(func.count(DiseaseCase.id) >= _MIN_CASES)
        .all()
    )
    if not current_rows:
        return []

    # Baseline counts exclude the last 24h; average over 29 days → per-day rate.
    baseline_rows = (
        db.query(
            DiseaseCase.disease_code,
            DiseaseCase.province,
            func.count(DiseaseCase.id).label("baseline_total"),
        )
        .filter(DiseaseCase.is_positive.is_(True))
        .filter(DiseaseCase.reported_at >= baseline_start)
        .filter(DiseaseCase.reported_at < window_start)
        .group_by(DiseaseCase.disease_code, DiseaseCase.province)
        .all()
    )
    baseline_map: dict[tuple[str, str], int] = {
        (r.disease_code, r.province): int(r.baseline_total) for r in baseline_rows
    }

    baseline_days = max(BASELINE_DAYS - 1, 1)
    alerts: list[OutbreakAlert] = []
    for row in current_rows:
        baseline_total = baseline_map.get((row.disease_code, row.province), 0)
        baseline_avg   = baseline_total / baseline_days
        # Guard against a zero baseline: compare against a floor of 1 case/day so a
        # single blip on a previously silent disease still registers proportionally.
        denominator = max(baseline_avg, 1.0)
        ratio = row.current_count / denominator
        severity = _classify(ratio)
        if severity is None:
            continue
        alerts.append(OutbreakAlert(
            disease_code=row.disease_code,
            disease_name=row.disease_name,
            province=row.province,
            current_count=int(row.current_count),
            baseline_avg=round(baseline_avg, 4),
            ratio=round(ratio, 4),
            severity=severity,
            detected_at=now,
        ))

    # Critical first, then by raw magnitude so operators triage worst-first.
    alerts.sort(key=lambda a: (a.severity != "critical", -a.current_count, -a.ratio))
    return alerts


# ─── get_disease_heatmap ────────────────────────────────────────────────────

def get_disease_heatmap(
    db: Session,
    disease_code: str,
    days: int = 7,
    *,
    now: Optional[datetime] = None,
) -> dict:
    """Per-province case counts for ``disease_code`` over the last ``days`` days."""
    if days < 1:
        raise ValueError("days must be >= 1")
    now = now or datetime.now(timezone.utc)
    window_start = now - timedelta(days=days)

    rows = (
        db.query(
            DiseaseCase.province,
            func.count(DiseaseCase.id).label("count"),
        )
        .filter(DiseaseCase.disease_code == disease_code)
        .filter(DiseaseCase.is_positive.is_(True))
        .filter(DiseaseCase.reported_at >= window_start)
        .filter(DiseaseCase.reported_at <= now)
        .group_by(DiseaseCase.province)
        .order_by(func.count(DiseaseCase.id).desc())
        .all()
    )

    by_province = [{"province": r.province, "count": int(r.count)} for r in rows]
    return {
        "disease_code": disease_code,
        "days": days,
        "window_start": window_start,
        "window_end": now,
        "total": sum(item["count"] for item in by_province),
        "by_province": by_province,
    }


# ─── get_resistance_report ──────────────────────────────────────────────────

def get_resistance_report(
    db: Session,
    province: Optional[str] = None,
) -> dict:
    """Resistance rates per (bacterium, antibiotic[, province]).

    Passing ``province`` narrows the scope to a single governorate; otherwise
    each row in the output still carries its province so a single response
    can power a full national heat-table.
    """
    resistant_flag = case((AntibioticSensitivity.is_resistant.is_(True), 1), else_=0)

    q = db.query(
        AntibioticSensitivity.bacterium,
        AntibioticSensitivity.antibiotic,
        AntibioticSensitivity.province,
        func.count(AntibioticSensitivity.id).label("tested"),
        func.sum(resistant_flag).label("resistant"),
    )
    if province:
        q = q.filter(AntibioticSensitivity.province == province)

    rows = (
        q.group_by(
            AntibioticSensitivity.bacterium,
            AntibioticSensitivity.antibiotic,
            AntibioticSensitivity.province,
        )
        .order_by(func.count(AntibioticSensitivity.id).desc())
        .all()
    )

    pairs = []
    for r in rows:
        tested = int(r.tested or 0)
        resistant = int(r.resistant or 0)
        rate = (resistant / tested) if tested > 0 else 0.0
        pairs.append({
            "bacterium": r.bacterium,
            "antibiotic": r.antibiotic,
            "province": r.province,
            "tested": tested,
            "resistant": resistant,
            "resistance_rate": round(rate, 4),
        })

    # Highest resistance rates first, breaking ties on sample size so a 100%
    # result from a single test doesn't outrank 80% from 200 tests.
    pairs.sort(key=lambda p: (-p["resistance_rate"], -p["tested"]))

    return {
        "generated_at": datetime.now(timezone.utc),
        "province_filter": province,
        "total_pairs": len(pairs),
        "pairs": pairs,
    }
