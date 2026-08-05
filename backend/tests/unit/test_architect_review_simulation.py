"""Unit tests for GULA-ARCHITECT-001 — design review (Phase 6) + simulation (Phase 7)."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.architect.review import (
    DIMENSION_EVIDENCE,
    persist_review,
    render_markdown as render_review,
    review_design,
    _verdict,
)
from scripts.architect.simulation import (
    SCALE_STEPS,
    project_full,
    project_scale,
    persist_simulation,
    render_markdown as render_simulation,
)


class TestReview:
    def test_review_covers_eight_dimensions(self):
        review = review_design("test-candidate")
        assert len(review.findings) == 8

    def test_review_dimensions_match_mission(self):
        dimensions = {f.dimension for f in review_design("x").findings}
        assert dimensions == {"architecture", "scalability", "reliability",
                              "maintainability", "security", "performance",
                              "cost", "compliance"}

    def test_review_scores_bounded(self):
        review = review_design("x")
        assert 0 <= review.overall_score() <= 100
        for finding in review.findings:
            assert 0 <= finding.score <= 100

    def test_review_verdict_valid(self):
        review = review_design("x")
        assert review.verdict in {"pass", "conditional", "fail"}

    def test_empty_repo_fails_review(self, tmp_path):
        review = review_design("empty", tmp_path)
        assert review.verdict == "fail"

    def test_full_repo_review_passes(self):
        review = review_design("gula-platform")
        assert review.verdict == "pass"

    def test_persist_review_writes_file(self, tmp_path):
        path = persist_review("candidate", tmp_path)
        assert path.exists()

    def test_render_contains_verdict(self):
        text = render_review(review_design("x"))
        assert "Overall verdict" in text
        assert "Candidate" in text

    def test_evidence_covers_every_dimension(self):
        for dimension in ("architecture", "scalability", "reliability",
                          "maintainability", "security", "performance",
                          "cost", "compliance"):
            assert dimension in DIMENSION_EVIDENCE

    def test_verdict_thresholds(self):
        assert _verdict(90) == "pass"
        assert _verdict(70) == "conditional"
        assert _verdict(30) == "fail"


class TestSimulation:
    def test_project_scale_single_node(self):
        projection = project_scale(100)
        assert projection.tier == "single-node"
        assert projection.app_replicas >= 1

    def test_project_full_covers_five_steps(self):
        projections = project_full()
        assert len(projections) == 5
        assert [p.users for p in projections] == list(SCALE_STEPS)

    def test_requests_monotonic(self):
        projections = project_full()
        rps = [p.requests_per_second for p in projections]
        assert rps == sorted(rps)

    def test_every_projection_has_storage_cost_bottleneck(self):
        for projection in project_full():
            assert projection.storage_gb >= 0
            assert projection.monthly_cost_usd >= 0
            assert projection.predicted_bottleneck

    def test_tier_progression(self):
        tiers = [p.tier for p in project_full()]
        assert tiers == ["single-node", "small-cluster", "regional",
                         "multi-region", "national"]

    def test_million_users_replicas_bounded(self):
        final = project_full()[-1]
        assert final.users == 1_000_000
        assert 1 <= final.app_replicas <= 10

    def test_cache_memory_scales_with_users(self):
        small = project_scale(1_000)
        large = project_scale(1_000_000)
        assert large.cache_memory_gb > small.cache_memory_gb

    def test_persist_simulation_writes_file(self, tmp_path):
        path = persist_simulation()
        assert path.exists()
        import json

        data = json.loads(path.read_text(encoding="utf-8"))
        assert len(data["projections"]) == 5
        assert "assumptions" in data

    def test_render_contains_bottlenecks(self):
        text = render_simulation(project_full())
        assert "Predicted Bottlenecks" in text
        assert "Monthly cost" in text
