"""Unit tests for GULA-OPTIMIZER-001 — safe optimization, evolution, quality."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.optimizer.core import (
    EVOLUTION_TARGETS,
    OptimizationStatus,
)
from scripts.optimizer.evolution import (
    load_proposals,
    persist_proposals,
    propose_evolution,
    set_proposal_status,
)
from scripts.optimizer.quality import (
    render_markdown,
    run_validation,
)
from scripts.optimizer.safe import (
    load_runs,
    persist_run,
    regressed_runs,
    run_optimization,
    verified_runs,
)


class TestSafeOptimization:
    def test_improvement_is_verified(self, tmp_path, monkeypatch):
        from scripts.optimizer import safe as safe_module

        monkeypatch.setattr(safe_module, "BENCHMARK_DIR", tmp_path)
        monkeypatch.setattr(safe_module, "RUNS_PATH", tmp_path / "runs.json")
        run = run_optimization("bundle-size", 100.0, 80.0, tests_passed=True)
        assert run.status == OptimizationStatus.VERIFIED.value
        assert run.regression is False
        assert run.benchmarked is True
        assert run.improved() is True

    def test_regression_is_reverted(self, tmp_path, monkeypatch):
        from scripts.optimizer import safe as safe_module

        monkeypatch.setattr(safe_module, "BENCHMARK_DIR", tmp_path)
        monkeypatch.setattr(safe_module, "RUNS_PATH", tmp_path / "runs.json")
        run = run_optimization("api-latency", 100.0, 120.0, tests_passed=True)
        assert run.status == OptimizationStatus.REVERTED.value
        assert run.regression is True
        assert run.reverted is True

    def test_failing_tests_are_reverted(self, tmp_path, monkeypatch):
        from scripts.optimizer import safe as safe_module

        monkeypatch.setattr(safe_module, "BENCHMARK_DIR", tmp_path)
        monkeypatch.setattr(safe_module, "RUNS_PATH", tmp_path / "runs.json")
        run = run_optimization("disk-usage", 100.0, 80.0, tests_passed=False)
        assert run.status == OptimizationStatus.REVERTED.value
        assert run.regression is True
        assert run.tests_passed is False

    def test_ids_are_sequential(self, tmp_path, monkeypatch):
        from scripts.optimizer import safe as safe_module

        monkeypatch.setattr(safe_module, "BENCHMARK_DIR", tmp_path)
        monkeypatch.setattr(safe_module, "RUNS_PATH", tmp_path / "runs.json")
        first = run_optimization("bundle-size", 100.0, 80.0)
        second = run_optimization("api-latency", 10.0, 9.0)
        assert first.optimization_id == "OPT-000001"
        assert second.optimization_id == "OPT-000002"

    def test_persist_run_is_idempotent(self, tmp_path, monkeypatch):
        from scripts.optimizer import safe as safe_module

        monkeypatch.setattr(safe_module, "BENCHMARK_DIR", tmp_path)
        monkeypatch.setattr(safe_module, "RUNS_PATH", tmp_path / "runs.json")
        run = run_optimization("bundle-size", 100.0, 80.0)
        persist_run(run)
        runs = load_runs()
        assert len(runs) == 1

    def test_verified_runs_filters(self, tmp_path, monkeypatch):
        from scripts.optimizer import safe as safe_module

        monkeypatch.setattr(safe_module, "BENCHMARK_DIR", tmp_path)
        monkeypatch.setattr(safe_module, "RUNS_PATH", tmp_path / "runs.json")
        run_optimization("bundle-size", 100.0, 80.0)
        run_optimization("api-latency", 100.0, 120.0)
        assert len(verified_runs()) == 1
        assert len(regressed_runs()) == 1

    def test_load_runs_empty(self, tmp_path, monkeypatch):
        from scripts.optimizer import safe as safe_module

        monkeypatch.setattr(safe_module, "BENCHMARK_DIR", tmp_path)
        monkeypatch.setattr(safe_module, "RUNS_PATH", tmp_path / "missing.json")
        assert load_runs() == []


class TestEvolution:
    def test_proposes_seven_targets(self):
        proposals = propose_evolution()
        assert len(proposals) == 7

    def test_targets_are_distinct(self):
        proposals = propose_evolution()
        assert len({p.target for p in proposals}) == 7

    def test_targets_cover_all(self):
        proposals = propose_evolution()
        targets = {p.target for p in proposals}
        for target in EVOLUTION_TARGETS:
            assert target in targets

    def test_each_proposal_has_rationale(self):
        for proposal in propose_evolution():
            assert proposal.rationale
            assert proposal.status == "open"

    def test_ids_sequential_and_deterministic(self, tmp_path, monkeypatch):
        from scripts.optimizer import evolution as evolution_module

        monkeypatch.setattr(evolution_module, "PROPOSAL_DIR", tmp_path)
        monkeypatch.setattr(evolution_module, "PROPOSALS_PATH", tmp_path / "evo.json")
        proposals = propose_evolution()
        assert [p.proposal_id for p in proposals] == [
            f"EVO-{i + 1:06d}" for i in range(7)
        ]

    def test_persist_and_load_round_trip(self, tmp_path, monkeypatch):
        from scripts.optimizer import evolution as evolution_module

        monkeypatch.setattr(evolution_module, "PROPOSAL_DIR", tmp_path)
        monkeypatch.setattr(evolution_module, "PROPOSALS_PATH", tmp_path / "evo.json")
        proposals = propose_evolution()
        path = persist_proposals(proposals)
        assert path.name == "evo.json"
        loaded = load_proposals()
        assert len(loaded) == 7

    def test_set_proposal_status(self, tmp_path, monkeypatch):
        from scripts.optimizer import evolution as evolution_module

        monkeypatch.setattr(evolution_module, "PROPOSAL_DIR", tmp_path)
        monkeypatch.setattr(evolution_module, "PROPOSALS_PATH", tmp_path / "evo.json")
        proposals = propose_evolution()
        persist_proposals(proposals)
        updated = set_proposal_status("EVO-000001", "approved")
        assert updated is not None
        assert updated.status == "approved"
        assert load_proposals()[0].status == "approved"

    def test_set_proposal_status_invalid(self, tmp_path, monkeypatch):
        from scripts.optimizer import evolution as evolution_module

        monkeypatch.setattr(evolution_module, "PROPOSAL_DIR", tmp_path)
        monkeypatch.setattr(evolution_module, "PROPOSALS_PATH", tmp_path / "evo.json")
        persist_proposals(propose_evolution())
        try:
            set_proposal_status("EVO-000001", "nonsense")
            raise AssertionError("expected ValueError")
        except ValueError:
            pass

    def test_set_proposal_status_missing(self, tmp_path, monkeypatch):
        from scripts.optimizer import evolution as evolution_module

        monkeypatch.setattr(evolution_module, "PROPOSAL_DIR", tmp_path)
        monkeypatch.setattr(evolution_module, "PROPOSALS_PATH", tmp_path / "evo.json")
        persist_proposals(propose_evolution())
        assert set_proposal_status("EVO-999999", "approved") is None

    def test_next_proposal_number_starts_at_one(self, tmp_path, monkeypatch):
        from scripts.optimizer import evolution as evolution_module

        monkeypatch.setattr(evolution_module, "PROPOSAL_DIR", tmp_path)
        monkeypatch.setattr(evolution_module, "PROPOSALS_PATH", tmp_path / "evo.json")
        assert evolution_module._next_proposal_number() == "000001"


class TestQuality:
    def test_runs_six_checks(self, tmp_path, monkeypatch):
        from scripts.optimizer import safe as safe_module

        monkeypatch.setattr(safe_module, "BENCHMARK_DIR", tmp_path)
        monkeypatch.setattr(safe_module, "RUNS_PATH", tmp_path / "runs.json")
        score = run_validation()
        assert len(score.checks) == 6

    def test_score_within_bounds(self, tmp_path, monkeypatch):
        from scripts.optimizer import safe as safe_module

        monkeypatch.setattr(safe_module, "BENCHMARK_DIR", tmp_path)
        monkeypatch.setattr(safe_module, "RUNS_PATH", tmp_path / "runs.json")
        score = run_validation()
        assert 0 <= score.score <= 100

    def test_no_regressions_scored(self, tmp_path, monkeypatch):
        from scripts.optimizer import safe as safe_module

        monkeypatch.setattr(safe_module, "BENCHMARK_DIR", tmp_path)
        monkeypatch.setattr(safe_module, "RUNS_PATH", tmp_path / "runs.json")
        run_optimization("bundle-size", 100.0, 80.0, tests_passed=True)
        score = run_validation()
        assert score.regressions == []
        assert score.verified_runs == 1
        assert score.improved_metrics == 1

    def test_regression_detected(self, tmp_path, monkeypatch):
        from scripts.optimizer import safe as safe_module

        monkeypatch.setattr(safe_module, "BENCHMARK_DIR", tmp_path)
        monkeypatch.setattr(safe_module, "RUNS_PATH", tmp_path / "runs.json")
        run_optimization("api-latency", 100.0, 150.0, tests_passed=True)
        score = run_validation()
        assert len(score.regressions) == 1
        assert score.score < 100

    def test_render_markdown_contains_checks(self, tmp_path, monkeypatch):
        from scripts.optimizer import safe as safe_module

        monkeypatch.setattr(safe_module, "BENCHMARK_DIR", tmp_path)
        monkeypatch.setattr(safe_module, "RUNS_PATH", tmp_path / "runs.json")
        text = render_markdown(run_validation())
        assert "no-functional-regression" in text
        assert "Optimization score" in text

    def test_security_check_fails_when_verified_without_tests(self, tmp_path, monkeypatch):
        from scripts.optimizer import safe as safe_module

        monkeypatch.setattr(safe_module, "BENCHMARK_DIR", tmp_path)
        monkeypatch.setattr(safe_module, "RUNS_PATH", tmp_path / "runs.json")
        run_optimization("disk-usage", 100.0, 80.0, tests_passed=False)
        score = run_validation()
        assert score.checks["security-preserved"] == "pass"

    def test_quality_summary_present(self, tmp_path, monkeypatch):
        from scripts.optimizer import safe as safe_module

        monkeypatch.setattr(safe_module, "BENCHMARK_DIR", tmp_path)
        monkeypatch.setattr(safe_module, "RUNS_PATH", tmp_path / "runs.json")
        score = run_validation()
        assert score.summary
