"""Demographic-aware reference range interpretation engine.

Given a biomarker concept, a value + unit, and a patient demographic
context, ``interpret()`` returns a structured ``Interpretation`` with:

  * ``matched_range``  — which reference-range row was chosen and why
  * ``value_canonical`` — value converted into the canonical unit
  * ``level``          — one of ``normal`` / ``mildly_abnormal`` /
                        ``moderately_abnormal`` / ``severely_abnormal`` /
                        ``critical``
  * ``direction``      — ``low`` / ``high`` / ``in_range``
  * ``risk_level``     — mapped medical-safety class
                        (``informational`` / ``low_risk`` / ``moderate_risk``
                         / ``high_risk`` / ``emergency_risk``)
  * ``escalation_required`` — True iff risk_level ≥ high_risk
  * ``provenance``     — source, source_version, source_url of the range

No text generation, no clinical advice — the engine returns *structured*
interpretation. Presentation-layer text (bilingual explanations, doctor-
review prompts) is a separate concern; keeping this layer text-free
preserves auditability.

Match specificity (best row wins; ties broken by created_at desc):

  score = 100·(analyzer=input) + 50·(pregnancy=input) + 25·(sex=input)
        + 10·(age band covers input) + 5·(specimen=input)
        +  1·(lab_id=input)

`sex: any` and `pregnancy_status: any` contribute half score, since they
match but are less specific than an exact demographic row.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ...models.medical_ontology import (
    MedicalOntologyConcept,
    MedicalOntologyReferenceRange,
)
from .units import UnitConversionError, convert

# ─── Value objects ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Provenance:
    source: str
    source_version: str | None
    source_url: str | None
    notes: str | None


@dataclass(frozen=True)
class MatchedRange:
    range_id: Any
    unit_key: str
    low: float | None
    high: float | None
    critical_low: float | None
    critical_high: float | None
    specificity_score: int
    age_min_years: float | None
    age_max_years: float | None
    sex: str
    pregnancy_status: str
    specimen_key: str | None
    analyzer: str | None


@dataclass(frozen=True)
class Interpretation:
    concept_key: str
    value_input: float
    unit_input: str
    value_canonical: float
    unit_canonical: str
    matched_range: MatchedRange
    provenance: Provenance
    direction: str          # 'low' | 'high' | 'in_range'
    level: str              # 'normal' | 'mildly_abnormal' | ... | 'critical'
    deviation_pct: float | None
    risk_level: str         # 'informational' ... 'emergency_risk'
    escalation_required: bool
    warnings: list[str] = field(default_factory=list)


class ReferenceRangeError(Exception):
    """Raised when no reference range is available for the requested
    concept / demographic tuple. Callers may fall back to legacy
    interpretation."""


# ─── Public entry point ──────────────────────────────────────────────────────

def interpret(
    session: Session,
    concept_key: str,
    value: float,
    unit_key: str,
    *,
    age_years: float | None,
    sex: str = "any",
    pregnancy_status: str = "any",
    specimen: str | None = None,
    analyzer: str | None = None,
    lab_id: int | None = None,
) -> Interpretation:
    """Interpret ``value`` against the demographic-aware reference ranges.

    Raises ``ReferenceRangeError`` when the concept is unknown or has no
    reference range covering the demographic tuple.
    """
    concept = session.execute(
        select(MedicalOntologyConcept).where(
            MedicalOntologyConcept.concept_key == concept_key,
            MedicalOntologyConcept.status == "active",
        )
    ).scalar_one_or_none()
    if concept is None:
        raise ReferenceRangeError(f"Unknown concept: {concept_key}")

    canonical_unit = concept.canonical_unit_key or unit_key
    warnings: list[str] = []

    # Convert into canonical unit for range comparison.
    try:
        value_canonical = convert(
            session, value, unit_key, canonical_unit,
            concept_scope_key=concept_key,
        )
    except UnitConversionError as exc:
        raise ReferenceRangeError(str(exc)) from None

    candidates = _load_candidates(session, concept.id, canonical_unit, lab_id)
    if not candidates:
        raise ReferenceRangeError(
            f"No reference ranges seeded for {concept_key}"
        )

    scored: list[tuple[int, Any]] = []
    for r in candidates:
        score = _specificity_score(
            r,
            age_years=age_years,
            sex=sex,
            pregnancy_status=pregnancy_status,
            specimen=specimen,
            analyzer=analyzer,
            lab_id=lab_id,
        )
        if score < 0:
            continue  # hard exclusion (e.g. age out of band)
        scored.append((score, r))

    if not scored:
        raise ReferenceRangeError(
            f"No reference range covers demographics "
            f"(concept={concept_key}, age={age_years}, sex={sex}, "
            f"pregnancy={pregnancy_status})"
        )

    scored.sort(key=lambda t: (t[0], t[1].created_at), reverse=True)
    best_score, best = scored[0]

    direction, level, deviation_pct = _classify(value_canonical, best)
    risk_level, escalation = _risk_level(direction, level, best)

    if lab_id is not None and best.lab_id != lab_id:
        warnings.append("no lab-specific range; using platform default")
    if sex != "any" and best.sex == "any":
        warnings.append("no sex-specific range; using generic")

    return Interpretation(
        concept_key=concept_key,
        value_input=value,
        unit_input=unit_key,
        value_canonical=value_canonical,
        unit_canonical=canonical_unit,
        matched_range=MatchedRange(
            range_id=best.id,
            unit_key=best.unit_key,
            low=best.low,
            high=best.high,
            critical_low=best.critical_low,
            critical_high=best.critical_high,
            specificity_score=best_score,
            age_min_years=best.age_min_years,
            age_max_years=best.age_max_years,
            sex=best.sex,
            pregnancy_status=best.pregnancy_status,
            specimen_key=best.specimen_key,
            analyzer=best.analyzer,
        ),
        provenance=Provenance(
            source=best.source,
            source_version=best.source_version,
            source_url=best.source_url,
            notes=best.notes,
        ),
        direction=direction,
        level=level,
        deviation_pct=deviation_pct,
        risk_level=risk_level,
        escalation_required=escalation,
        warnings=warnings,
    )


# ─── Internals ───────────────────────────────────────────────────────────────

def _load_candidates(
    session: Session,
    concept_id: Any,
    unit_key: str,
    lab_id: int | None,
) -> list[MedicalOntologyReferenceRange]:
    stmt = (
        select(MedicalOntologyReferenceRange)
        .where(MedicalOntologyReferenceRange.concept_id == concept_id)
        .where(MedicalOntologyReferenceRange.unit_key == unit_key)
        .where(MedicalOntologyReferenceRange.status == "active")
    )
    if lab_id is not None:
        stmt = stmt.where(
            (MedicalOntologyReferenceRange.lab_id == lab_id)
            | (MedicalOntologyReferenceRange.lab_id.is_(None))
        )
    else:
        stmt = stmt.where(MedicalOntologyReferenceRange.lab_id.is_(None))
    return list(session.execute(stmt).scalars().all())


def _specificity_score(
    r: MedicalOntologyReferenceRange,
    *,
    age_years: float | None,
    sex: str,
    pregnancy_status: str,
    specimen: str | None,
    analyzer: str | None,
    lab_id: int | None,
) -> int:
    """Higher is better; -1 = row is not eligible."""
    if age_years is not None:
        if r.age_min_years is not None and age_years < r.age_min_years:
            return -1
        if r.age_max_years is not None and age_years > r.age_max_years:
            return -1

    # r.sex is 'male' | 'female' | 'any'; 'any' matches any input.
    if r.sex not in ("any", sex):
        return -1

    if r.pregnancy_status not in ("any", pregnancy_status):
        # Row is pregnancy-scoped — only match when the input matches exactly.
        return -1

    score = 0

    # Analyzer specificity (rare but strongest signal when populated).
    if r.analyzer and analyzer and r.analyzer == analyzer:
        score += 100

    # Pregnancy status: exact > any.
    if r.pregnancy_status != "any" and r.pregnancy_status == pregnancy_status:
        score += 50
    elif r.pregnancy_status == "any":
        score += 25

    # Sex: exact > any.
    if r.sex != "any" and r.sex == sex:
        score += 25
    elif r.sex == "any":
        score += 12

    # Age-band tightness: closed band > half-open > unbounded.
    if r.age_min_years is not None and r.age_max_years is not None:
        score += 10
    elif r.age_min_years is not None or r.age_max_years is not None:
        score += 5

    # Specimen: exact > unspecified.
    if r.specimen_key and specimen and r.specimen_key == specimen:
        score += 5

    # Lab-specific rule beats platform default.
    if lab_id is not None and r.lab_id == lab_id:
        score += 1

    return score


def _classify(
    value: float,
    r: MedicalOntologyReferenceRange,
) -> tuple[str, str, float | None]:
    """Return ``(direction, level, deviation_pct)`` for value vs range."""
    if r.critical_low is not None and value <= r.critical_low:
        return "low", "critical", None
    if r.critical_high is not None and value >= r.critical_high:
        return "high", "critical", None

    if r.low is not None and value < r.low:
        deviation = ((r.low - value) / r.low * 100.0) if r.low else 0.0
        return "low", _band(deviation), deviation
    if r.high is not None and value > r.high:
        deviation = ((value - r.high) / r.high * 100.0) if r.high else 0.0
        return "high", _band(deviation), deviation

    return "in_range", "normal", 0.0


def _band(deviation_pct: float) -> str:
    if deviation_pct < 15:
        return "mildly_abnormal"
    if deviation_pct < 40:
        return "moderately_abnormal"
    return "severely_abnormal"


def _risk_level(
    direction: str,
    level: str,
    r: MedicalOntologyReferenceRange,
) -> tuple[str, bool]:
    """Map classification to medical-risk class + escalation flag."""
    if level == "critical":
        return "emergency_risk", True
    if level == "severely_abnormal":
        return "high_risk", True
    if level == "moderately_abnormal":
        return "moderate_risk", False
    if level == "mildly_abnormal":
        return "low_risk", False
    return "informational", False


__all__ = [
    "Interpretation",
    "MatchedRange",
    "Provenance",
    "ReferenceRangeError",
    "interpret",
]
