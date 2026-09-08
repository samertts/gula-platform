"""Canonical unit conversion for the medical ontology.

Every biomarker concept declares one ``canonical_unit_key``. Reference
ranges are seeded in that canonical unit; incoming lab values in a
different unit are converted before interpretation.

``convert()`` first looks for a concept-scoped conversion (glucose in
mg/dL ↔ mmol/L differs from creatinine or cholesterol because it depends
on molecular weight), then falls back to a universal (concept_scope IS
NULL) conversion. Missing conversions raise ``UnitConversionError`` — the
caller decides whether to reject the value or defer to a legacy engine.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ...models.medical_ontology import MedicalOntologyUnitConversion


class UnitConversionError(ValueError):
    """No conversion path exists from source unit to target unit for the
    given concept scope."""


def convert(
    session: Session,
    value: float,
    from_unit_key: str,
    to_unit_key: str,
    *,
    concept_scope_key: Optional[str] = None,
) -> float:
    """Convert ``value`` from ``from_unit_key`` to ``to_unit_key``.

    Same-unit conversion returns the value unchanged. Missing conversion
    raises ``UnitConversionError`` — never silently returns the input.
    """
    if from_unit_key == to_unit_key:
        return value

    # Prefer concept-scoped rows (mass↔molar depends on molecule).
    stmt = (
        select(MedicalOntologyUnitConversion.factor,
               MedicalOntologyUnitConversion.offset)
        .where(MedicalOntologyUnitConversion.from_unit_key == from_unit_key)
        .where(MedicalOntologyUnitConversion.to_unit_key == to_unit_key)
    )
    if concept_scope_key:
        scoped = session.execute(
            stmt.where(
                MedicalOntologyUnitConversion.concept_scope_key
                == concept_scope_key
            )
        ).first()
        if scoped is not None:
            factor, offset = scoped
            return value * float(factor) + float(offset)

    universal = session.execute(
        stmt.where(
            MedicalOntologyUnitConversion.concept_scope_key.is_(None)
        )
    ).first()
    if universal is not None:
        factor, offset = universal
        return value * float(factor) + float(offset)

    raise UnitConversionError(
        f"No conversion from {from_unit_key} to {to_unit_key}"
        + (f" (scope={concept_scope_key})" if concept_scope_key else "")
    )


__all__ = ["UnitConversionError", "convert"]
