"""Unit tests for PROGRAM-012 governance scripts (project_brain, validation engine)."""

from __future__ import annotations

import json
import os
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts import enterprise_validation_engine as eve
from scripts import project_brain as pb


class TestCheckRegressions:
    def test_equal_to_baseline_is_not_regression(self):
        results = {"ruff": {"ruff_errors": 379}}
        baseline = {"ruff_errors": 379}
        assert eve.check_regressions(results, baseline) == []

    def test_increased_error_count_is_regression(self):
        results = {"ruff": {"ruff_errors": 380}}
        baseline = {"ruff_errors": 379}
        assert eve.check_regressions(results, baseline) == ["ruff_errors: 379 -> 380 (increased)"]

    def test_decreased_error_count_is_improvement(self):
        results = {"ruff": {"ruff_errors": 300}}
        baseline = {"ruff_errors": 379}
        assert eve.check_regressions(results, baseline) == []

    def test_decreased_score_is_regression(self):
        results = {"scorecard": {"scorecard_score": 70}}
        baseline = {"scorecard_score": 73}
        assert eve.check_regressions(results, baseline) == ["scorecard_score: 73 -> 70 (decreased)"]

    def test_increased_score_is_improvement(self):
        results = {"scorecard": {"scorecard_score": 80}}
        baseline = {"scorecard_score": 73}
        assert eve.check_regressions(results, baseline) == []

    def test_fewer_tests_is_regression(self):
        results = {"unit-tests": {"unit_test_count": 145}}
        baseline = {"unit_test_count": 150}
        assert eve.check_regressions(results, baseline) == ["unit_test_count: 150 -> 145 (decreased)"]

    def test_missing_baseline_metric_is_not_regression(self):
        assert eve.check_regressions({"ruff": {"ruff_errors": 100}}, {}) == []

    def test_missing_current_metric_is_not_regression(self):
        assert eve.check_regressions({}, {"ruff_errors": 379}) == []


class TestVerdict:
    def test_all_hard_pass_no_regressions(self):
        ok, fails = eve.verdict({"_meta": {"regressions": []}, "ruff": {"status": "pass", "policy": "hard"}})
        assert ok and not fails

    def test_regression_blocks(self):
        ok, fails = eve.verdict({"_meta": {"regressions": ["ruff_errors: 379 -> 400 (increased)"]}})
        assert not ok and len(fails) == 1

    def test_hard_failure_blocks(self):
        ok, fails = eve.verdict({"_meta": {"regressions": []}, "ruff": {"status": "fail", "policy": "hard"}})
        assert not ok and "ruff" in fails[0]

    def test_advisory_failure_does_not_block(self):
        ok, _fails = eve.verdict(
            {"_meta": {"regressions": []}, "arch": {"status": "fail", "policy": "advisory"}}
        )
        assert ok


class TestRenderMarkdown:
    def test_report_contains_verdict_and_table(self):
        results = {
            "_meta": {"generated_at": "2026-07-31T00:00:00+00:00", "scope": "fast", "duration_s": 5, "regressions": []},
            "ruff": {"status": "pass", "policy": "hard", "detail": "0 violations", "duration_s": 0.5},
        }
        md = eve.render_markdown(results, True)
        assert "PASS" in md and "| ruff | hard |" in md

    def test_regressions_listed_in_report(self):
        results = {
            "_meta": {"generated_at": "2026-07-31T00:00:00+00:00", "scope": "fast", "duration_s": 5,
                      "regressions": ["ruff_errors: 1 -> 2 (increased)"]},
            "ruff": {"status": "fail", "policy": "hard", "detail": "2 violations", "duration_s": 0.5},
        }
        md = eve.render_markdown(results, False)
        assert "Regressions Detected (BLOCKING)" in md and "ruff_errors" in md


class TestProjectBrainCollect:
    def test_collect_returns_counts(self):
        data = pb.collect()
        assert "counts" in data and "programs" in data
        assert data["counts"]["migrations"] >= 50
        assert "backend/app" in data["counts"]["modules"]
        assert data["repo"]["name"] == "gula-platform"

    def test_collect_programs_includes_program_012(self):
        programs = pb.collect()["programs"]
        assert any("012" in p for p in programs)

    def test_render_markdown_contains_navigation(self):
        md = pb.render_markdown(pb.collect())
        assert "Project Brain" in md and "Knowledge Navigation" in md

    def test_brain_json_serializable(self):
        json.dumps(pb.collect(), ensure_ascii=False)
