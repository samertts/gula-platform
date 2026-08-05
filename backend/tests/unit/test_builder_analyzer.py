"""Unit tests for GULA-BUILDER-001 Phase 1 — Mission Analyzer."""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.builder.analyzer import (
    AnalyzerError,
    analyze,
    classify,
    classify_scores,
    complexity_score,
    cost_for,
    describe,
    expected_files_for,
    minutes_for,
    normalize,
    outputs_for,
    required_knowledge_for,
    risk_score,
    rollback_strategy_for,
    verification_strategy_for,
)


class TestNormalize:
    def test_lowercase_collapse(self):
        assert normalize("  Build   Patient \nManagement  ") == "build patient management"

    def test_empty_raises(self):
        with pytest.raises(AnalyzerError):
            normalize("   ")

    def test_whitespace_only_raises(self):
        with pytest.raises(AnalyzerError):
            analyze(" \n ")


class TestClassify:
    @pytest.mark.parametrize("objective,expected", [
        ("Build Patient Management", "feature"),
        ("Fix the login crash", "bug"),
        ("Deploy to production", "deployment"),
        ("Add security audit logging", "security"),
        ("Refactor the billing module", "refactor"),
        ("Write documentation for the API", "documentation"),
        ("Add performance benchmark for sample queries", "performance"),
        ("Add unit tests for lab service", "testing"),
        ("Propose an ADR for module boundaries", "architecture"),
        ("Set up docker and CI pipeline", "infrastructure"),
    ])
    def test_known_objectives(self, objective, expected):
        assert classify(objective) == expected

    def test_unknown_falls_back_to_architecture(self):
        assert classify("something completely unrelated") == "architecture"

    def test_scores_match_classify(self):
        scores = classify_scores("Add security audit logging")
        best = max(scores, key=scores.get)
        assert best == "security"
        assert scores["security"] >= 3


class TestScoring:
    def test_complexity_bounded(self):
        analysis = analyze("Build a very large patient management system")
        score = complexity_score("feature", analysis.objective, ["a", "b", "c"])
        assert 0 <= score <= 4

    def test_risk_scales_with_complexity(self):
        assert risk_score("security", 4) == 4
        assert risk_score("security", 0) == 4
        assert risk_score("documentation", 4) <= 2

    def test_cost_mapping(self):
        assert cost_for(0) == "trivial"
        assert cost_for(1) == "low"
        assert cost_for(2) == "medium"
        assert cost_for(3) == "high"
        assert cost_for(99) == "high"

    def test_minutes_positive(self):
        for mission in ("feature", "bug", "documentation", "security"):
            assert minutes_for(mission, 2) > 0


class TestAnalysis:
    def test_full_analysis(self):
        analysis = analyze("Build Patient Management")
        assert analysis.mission_type == "feature"
        assert analysis.complexity in {"trivial", "low", "moderate", "high", "critical"}
        assert analysis.risk in {"negligible", "low", "moderate", "high", "critical"}
        assert analysis.expected_files
        assert analysis.outputs
        assert analysis.verification_strategy
        assert analysis.rollback_strategy
        assert analysis.execution_time_minutes > 0
        assert analysis.execution_cost
        assert 0.0 < analysis.confidence <= 1.0

    def test_mission_id_default(self):
        a1 = analyze("Fix bug in API")
        a2 = analyze("Fix bug in API")
        assert a1.mission_id != a2.mission_id

    def test_custom_mission_id(self):
        assert analyze("x", mission_id="MSN-TEST").mission_id == "MSN-TEST"

    def test_to_dict(self):
        data = analyze("Add tests").to_dict()
        assert data["mission_type"] == "testing"
        assert isinstance(data["expected_files"], list)

    def test_describe_known(self):
        assert "New capability" in describe("feature")

    def test_describe_unknown(self):
        assert "Unknown" in describe("nope")


class TestLookups:
    def test_expected_files_for_all_types(self):
        from scripts.builder.core import MISSION_TYPES

        for mission in MISSION_TYPES:
            assert expected_files_for(mission)

    def test_required_knowledge_for_all_types(self):
        from scripts.builder.core import MISSION_TYPES

        for mission in MISSION_TYPES:
            assert required_knowledge_for(mission)

    def test_outputs_for_all_types(self):
        from scripts.builder.core import MISSION_TYPES

        for mission in MISSION_TYPES:
            assert outputs_for(mission)

    def test_strategies_for_all_types(self):
        from scripts.builder.core import MISSION_TYPES

        for mission in MISSION_TYPES:
            assert verification_strategy_for(mission)
            assert rollback_strategy_for(mission)
