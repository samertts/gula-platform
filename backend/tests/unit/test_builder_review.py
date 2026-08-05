"""Unit tests for GULA-BUILDER-001 Phase 7 — Self Review."""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.builder.core import ReviewFinding, ReviewReport
from scripts.builder.review import (
    AREA_EVIDENCE,
    REVIEW_AREAS,
    can_continue,
    review,
    review_verdict,
    summary,
)
from scripts.kernel.core import Severity


def _clean_context():
    return {
        "adr": True, "security_verified": True, "benchmark_pass": True,
        "tests_run": True, "tests_pass": True, "deploy_verified": True,
        "docs_updated": True, "ruff_clean": True, "registry_updated": True,
    }


class TestReview:
    def test_clean_evidence_passes(self):
        report = review("MSN-1", _clean_context())
        assert can_continue(report)
        assert review_verdict(report) == "PASS"

    def test_all_areas_reported(self):
        report = review("MSN-1")
        areas = {finding.area for finding in report.findings}
        assert areas == set(REVIEW_AREAS)

    def test_empty_context_fails(self):
        report = review("MSN-1")
        assert not can_continue(report)
        assert review_verdict(report) == "FAIL"

    def test_partial_evidence(self):
        report = review("MSN-1", {"tests_run": True, "tests_pass": True})
        failed = report.failed()
        assert all(f.area != "testing" for f in failed)

    def test_missing_evidence_names_keys(self):
        report = review("MSN-1")
        architecture = next(f for f in report.findings if f.area == "architecture")
        assert "adr" in architecture.detail

    def test_to_dict(self):
        report = review("MSN-1", _clean_context())
        data = report.to_dict()
        assert data["verdict"] == "PASS"
        assert len(data["findings"]) == 8


class TestAreaEvidence:
    def test_all_areas_have_evidence(self):
        for area in REVIEW_AREAS:
            assert AREA_EVIDENCE[area]

    def test_eight_areas(self):
        assert len(REVIEW_AREAS) == 8


class TestSummary:
    def test_summary_passes(self):
        report = review("MSN-1", _clean_context())
        assert report.verdict() in summary(report)

    def test_review_finding(self):
        finding = ReviewFinding(area="testing", severity=Severity.HIGH, detail="missing", passed=False)
        assert not finding.passed
        assert finding.to_dict()["area"] == "testing"

    def test_review_report_failed(self):
        report = ReviewReport(mission_id="MSN-1")
        report.findings.append(ReviewFinding("x", Severity.HIGH, "d", passed=False))
        assert report.failed()
        assert report.verdict() == "FAIL"
