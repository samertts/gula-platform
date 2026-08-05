"""Unit tests for GULA-REVIEWER-001 — core scoring and decision model."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.kernel.core import Severity
from scripts.reviewer.core import (
    AREA_NAMES,
    AREA_WEIGHT,
    REVIEW_AREAS,
    SEVERITY_PENALTY,
    AreaReview,
    Decision,
    ReviewFinding,
    decide_area,
    decide_overall,
    overall_score,
    score_area,
)


def make_finding(severity: Severity) -> ReviewFinding:
    return ReviewFinding("tests", severity, "sample", detail="d")


class TestConstants:
    def test_review_areas_match_area_names(self):
        assert set(REVIEW_AREAS) == set(AREA_NAMES)

    def test_area_weights_sum_to_one(self):
        assert abs(sum(AREA_WEIGHT.values()) - 1.0) < 1e-9

    def test_weights_cover_all_areas(self):
        assert set(AREA_WEIGHT) == set(REVIEW_AREAS)

    def test_severity_penalty_ordered(self):
        assert (SEVERITY_PENALTY[Severity.LOW]
                < SEVERITY_PENALTY[Severity.MEDIUM]
                < SEVERITY_PENALTY[Severity.HIGH]
                < SEVERITY_PENALTY[Severity.CRITICAL])


class TestScoreArea:
    def test_clean_area_scores_full(self):
        assert score_area([]) == 100.0

    def test_single_low_penalizes(self):
        assert score_area([make_finding(Severity.LOW)]) == 98.0

    def test_critical_penalizes_heavily(self):
        score = score_area([make_finding(Severity.CRITICAL)])
        assert score == 70.0

    def test_critical_caps_at_zero(self):
        findings = [make_finding(Severity.CRITICAL)] * 5
        assert score_area(findings) == 0.0

    def test_multiple_findings_accumulate(self):
        score = score_area([
            make_finding(Severity.MEDIUM),
            make_finding(Severity.MEDIUM),
        ])
        assert score == 90.0

    def test_never_below_zero(self):
        findings = [make_finding(Severity.CRITICAL)] * 5
        assert score_area(findings) == 0.0


class TestDecideArea:
    def test_empty_is_pass(self):
        assert decide_area([]) == Decision.PASS.value

    def test_low_only_is_warning(self):
        assert decide_area([make_finding(Severity.LOW)]) == Decision.PASS_WITH_WARNINGS.value

    def test_high_rejects(self):
        assert decide_area([make_finding(Severity.HIGH)]) == Decision.REJECT.value

    def test_critical_rejects(self):
        assert decide_area([make_finding(Severity.CRITICAL)]) == Decision.REJECT.value


class TestDecideOverall:
    def test_all_pass(self):
        reviews = [AreaReview(area="a", decision=Decision.PASS.value)]
        assert decide_overall(reviews) == Decision.PASS.value

    def test_any_warning_warns(self):
        reviews = [
            AreaReview(area="a", decision=Decision.PASS.value),
            AreaReview(area="b", decision=Decision.PASS_WITH_WARNINGS.value),
        ]
        assert decide_overall(reviews) == Decision.PASS_WITH_WARNINGS.value

    def test_any_reject_rejects(self):
        reviews = [
            AreaReview(area="a", decision=Decision.PASS.value),
            AreaReview(area="b", decision=Decision.REJECT.value),
        ]
        assert decide_overall(reviews) == Decision.REJECT.value


class TestOverallScore:
    def test_weighted_score(self):
        reviews = [
            AreaReview(area="architecture", score=100.0, decision="PASS"),
            AreaReview(area="security", score=50.0, decision="PASS"),
        ]
        expected = (100 * AREA_WEIGHT["architecture"] + 50 * AREA_WEIGHT["security"])
        assert overall_score(reviews) == expected

    def test_empty_reviews(self):
        assert overall_score([]) == 0.0
