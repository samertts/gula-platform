"""GULA Reviewer Engine (GULA-REVIEWER-001).

The independent engineering verification authority. Reviews every Builder
output before acceptance with deterministic PASS / PASS WITH WARNINGS / REJECT
verdicts across eight areas. Never writes production features.
"""

from __future__ import annotations

from scripts.reviewer.core import (
    AREA_NAMES,
    AREA_WEIGHT,
    REVIEW_AREAS,
    SEVERITY_PENALTY,
    AreaReview,
    Decision,
    ReviewFinding,
    ReviewReport,
    decide_area,
    decide_overall,
    ensure_dirs,
    overall_score,
    read_json,
    score_area,
    write_json,
)

__all__ = [
    "AREA_NAMES",
    "AREA_WEIGHT",
    "REVIEW_AREAS",
    "SEVERITY_PENALTY",
    "AreaReview",
    "Decision",
    "ReviewFinding",
    "ReviewReport",
    "decide_area",
    "decide_overall",
    "ensure_dirs",
    "overall_score",
    "read_json",
    "score_area",
    "write_json",
]
