"""Canonical resolution of a reported test to its `TestType` catalog entry.

A lab result arrives carrying a free-text `test_name` and, on some paths, a
`test_code`. `TestType` is the catalog that turns that into a linked entity with
a coded identity, a category, reference ranges and interpretation text.

The convention implemented here was already established inside
`app/routes/test_results.py`; it is moved out so the order, analyzer and seeding
paths use the same rule instead of each inventing one (or, as they did, skipping
the lookup entirely and writing a NULL link). See IA-019 / IA-020.

The rule, unchanged from its original form:

* an exact `test_code` match wins, because `test_types.test_code` is unique;
* otherwise fall back to a case-insensitive `test_name` match;
* a value the caller supplied is never overwritten — the catalog only fills
  what is missing.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..models.test_type import TestType


def resolve_test_type(
    db: Session,
    test_name: str,
    test_code: str | None,
    normal_low: float | None,
    normal_high: float | None,
    unit: str | None,
) -> tuple[float | None, float | None, str | None, TestType | None]:
    """Populate missing range/unit from the TestType catalog when available.

    Returns ``(normal_low, normal_high, unit, test_type)``. ``test_type`` is
    None when the catalog carries no match, which is a legitimate outcome for a
    test the lab has not catalogued — callers should pass that None through to
    ``LabResult.test_type_id`` rather than omitting the field, so that the
    attempt is recorded as having been made.
    """
    tt: TestType | None = None
    if test_code:
        tt = db.query(TestType).filter(TestType.test_code == test_code).first()
    if tt is None:
        tt = db.query(TestType).filter(TestType.test_name.ilike(test_name)).first()
    if tt is not None:
        if normal_low is None:
            normal_low = tt.normal_range_low
        if normal_high is None:
            normal_high = tt.normal_range_high
        if not unit:
            unit = tt.unit
    return normal_low, normal_high, unit, tt
