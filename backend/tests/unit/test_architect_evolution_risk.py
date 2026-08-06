"""Unit tests for GULA-ARCHITECT-001 — evolution (Phase 4) + risk engine (Phase 5)."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.architect.evolution import (
    REFACTORING_STRATEGY,
    SCALABILITY_PLAN,
    build_roadmap,
    persist_roadmap,
)
from scripts.architect.evolution import (
    render_markdown as render_evolution,
)
from scripts.architect.risk import (
    STRATEGIC_RISKS,
    _priority,
    build_risks,
    exposure,
    persist_risks,
)
from scripts.architect.risk import (
    render_markdown as render_risk,
)


class TestEvolution:
    def test_roadmap_covers_three_horizons(self):
        horizons = {m.horizon for m in build_roadmap()}
        assert horizons == {"1-year", "3-year", "5-year"}

    def test_roadmap_has_nine_milestones(self):
        assert len(build_roadmap()) == 9

    def test_every_milestone_has_technology_and_migration(self):
        for milestone in build_roadmap():
            assert milestone.technology
            assert milestone.migration

    def test_roadmap_sorted_by_horizon(self):
        milestones = build_roadmap()
        order = [m.horizon for m in milestones]
        assert order == sorted(order)

    def test_scalability_plan_spans_scales(self):
        assert len(SCALABILITY_PLAN) == 4
        scales = [s for s, _ in SCALABILITY_PLAN]
        assert scales == ["100-1k users", "1k-10k users",
                          "10k-100k users", "100k-1M users"]

    def test_refactoring_strategy_preserves_compatibility(self):
        joined = " ".join(REFACTORING_STRATEGY).lower()
        assert "behavioral compatibility" in joined

    def test_persist_roadmap_writes_file(self, tmp_path):
        path = persist_roadmap()
        assert path.exists()
        import json

        data = json.loads(path.read_text(encoding="utf-8"))
        assert len(data["milestones"]) == 9
        assert "scalability_plan" in data
        assert "refactoring_strategy" in data

    def test_render_contains_plans(self):
        text = render_evolution(build_roadmap())
        assert "Scalability Plan" in text
        assert "Refactoring Strategy" in text
        assert "Migration strategy" in text


class TestRisk:
    def test_exposure_bounded(self):
        assert exposure("low", "low") == 1
        assert exposure("critical", "critical") == 16

    def test_exposure_scales(self):
        assert exposure("high", "high") > exposure("low", "low")

    def test_priority_classification(self):
        assert _priority("high", "high") == "critical"
        assert _priority("medium", "medium") == "medium"
        assert _priority("low", "low") == "low"

    def test_build_risks_covers_all_categories(self):
        categories = {r.category for r in build_risks()}
        assert {"technical", "business", "operational", "security", "ai",
                "knowledge"} <= categories

    def test_risks_have_priority_and_exposure(self):
        for risk in build_risks():
            assert risk.priority in {"low", "medium", "high", "critical"}
            assert 1 <= risk.exposure <= 16

    def test_risks_include_dependency_finding(self):
        risks = build_risks()
        assert any(r.area == "architecture" for r in risks)

    def test_strategic_risks_categories_valid(self):
        valid = {"technical", "business", "operational", "security",
                 "infrastructure", "ai", "knowledge"}
        for record in STRATEGIC_RISKS:
            assert record[0] in valid

    def test_persist_risks_writes_file(self, tmp_path):
        path = persist_risks(tmp_path)
        assert path.exists()
        import json

        data = json.loads(path.read_text(encoding="utf-8"))
        assert len(data["risks"]) >= 8
        assert "categories" in data

    def test_render_has_mitigations(self):
        text = render_risk(build_risks())
        assert "## Mitigations" in text
        assert "exposure" in text

    def test_risks_sorted_by_exposure_desc(self):
        risks = build_risks()
        exposures = [r.exposure for r in risks]
        assert exposures == sorted(exposures, reverse=True)
