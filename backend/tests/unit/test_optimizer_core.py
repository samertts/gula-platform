"""Unit tests for GULA-OPTIMIZER-001 — core constants, enums, dataclasses."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.optimizer.core import (
    ARCHITECTURE_TECHNIQUES,
    AUDIT_COMPONENTS,
    BOTTLENECK_KINDS,
    BOTTLENECK_SEVERITIES,
    DEBT_KINDS,
    DX_DIMENSIONS,
    EVOLUTION_TARGETS,
    PERFORMANCE_METRICS,
    QUALITY_CHECKS,
    RESOURCE_TARGETS,
    ArchitectureRecommendation,
    AuditItem,
    Bottleneck,
    DebtItem,
    DebtStatus,
    DxFinding,
    EvolutionProposal,
    Metric,
    OptimizationRun,
    OptimizationScore,
    OptimizationStatus,
    ProposalStatus,
    ResourceRecommendation,
    ensure_dirs,
    make_id,
    read_json,
    write_json,
)


class TestEngineConstants:
    def test_audit_components_cover_eleven(self):
        assert len(AUDIT_COMPONENTS) == 11
        for component in ("backend", "frontend", "database", "infrastructure",
                          "docker", "knowledge", "deployment", "documentation",
                          "testing", "ci-cd", "developer-environment"):
            assert component in AUDIT_COMPONENTS

    def test_performance_metrics_cover_eleven(self):
        assert len(PERFORMANCE_METRICS) == 11
        for metric in ("api-latency", "database-queries", "memory-usage",
                       "cpu-usage", "disk-usage", "network-traffic",
                       "build-time", "startup-time", "bundle-size",
                       "container-size", "execution-time"):
            assert metric in PERFORMANCE_METRICS

    def test_bottleneck_kinds_cover_twelve(self):
        assert len(BOTTLENECK_KINDS) == 12
        for kind in ("slow-api", "duplicate-queries", "n-plus-one",
                     "unused-code", "dead-code", "large-bundle", "slow-build",
                     "blocking-operation", "large-dependency", "memory-leak",
                     "cpu-hotspot", "storage-waste"):
            assert kind in BOTTLENECK_KINDS

    def test_architecture_techniques_cover_ten(self):
        assert len(ARCHITECTURE_TECHNIQUES) == 10
        for technique in ("module-boundaries", "dependency-reduction",
                          "caching", "indexing", "async-processing",
                          "lazy-loading", "code-splitting", "compression",
                          "queue-optimization", "database-optimization"):
            assert technique in ARCHITECTURE_TECHNIQUES

    def test_resource_targets_cover_ten(self):
        assert len(RESOURCE_TARGETS) == 10
        for target in ("docker-images", "containers", "volumes", "redis",
                       "postgresql", "rabbitmq", "minio", "worker-usage",
                       "background-tasks", "infrastructure-cost"):
            assert target in RESOURCE_TARGETS

    def test_dx_dimensions_cover_eight(self):
        assert len(DX_DIMENSIONS) == 8
        for dimension in ("build-speed", "test-speed", "dev-startup",
                          "repository-navigation", "knowledge-search",
                          "automation", "tooling", "developer-feedback"):
            assert dimension in DX_DIMENSIONS

    def test_debt_kinds_cover_seven(self):
        assert len(DEBT_KINDS) == 7
        for kind in ("duplicated-logic", "deprecated-code", "temporary-fixes",
                     "architecture-drift", "dependency-problems",
                     "configuration-drift", "documentation-drift"):
            assert kind in DEBT_KINDS

    def test_evolution_targets_cover_seven(self):
        assert len(EVOLUTION_TARGETS) == 7
        for target in ("improvement-proposals", "architecture-evolution",
                       "refactoring-candidates", "infrastructure-improvements",
                       "automation-opportunities", "ai-capability-improvements",
                       "knowledge-improvements"):
            assert target in EVOLUTION_TARGETS

    def test_quality_checks_cover_six(self):
        assert len(QUALITY_CHECKS) == 6
        for check in ("no-functional-regression", "performance-improved",
                      "security-preserved", "documentation-updated",
                      "knowledge-updated", "deployment-valid"):
            assert check in QUALITY_CHECKS

    def test_bottleneck_severities(self):
        assert BOTTLENECK_SEVERITIES == ("low", "medium", "high", "critical")


class TestEnums:
    def test_optimization_status_values(self):
        assert OptimizationStatus.PLANNED.value == "planned"
        assert OptimizationStatus.MEASURED.value == "measured"
        assert OptimizationStatus.OPTIMIZED.value == "optimized"
        assert OptimizationStatus.VERIFIED.value == "verified"
        assert OptimizationStatus.REVERTED.value == "reverted"

    def test_debt_status_values(self):
        assert DebtStatus.OPEN.value == "open"
        assert DebtStatus.APPROVED.value == "approved"
        assert DebtStatus.ADDRESSED.value == "addressed"
        assert DebtStatus.WONT_FIX.value == "wont-fix"

    def test_proposal_status_values(self):
        assert ProposalStatus.OPEN.value == "open"
        assert ProposalStatus.APPROVED.value == "approved"
        assert ProposalStatus.REJECTED.value == "rejected"
        assert ProposalStatus.IMPLEMENTED.value == "implemented"


class TestDataclasses:
    def test_audit_item_defaults(self):
        item = AuditItem(item_id="OA-backend", title="backend")
        assert item.status == OptimizationStatus.PLANNED.value
        assert item.confidence == "low"
        assert item.tags == []

    def test_metric_round_trip(self):
        metric = Metric(name="api-latency", value=42.0, unit="routes")
        data = metric.to_dict()
        restored = Metric.from_dict(data)
        assert restored.name == "api-latency"
        assert restored.value == 42.0
        assert restored.unit == "routes"

    def test_metric_from_dict_defaults(self):
        metric = Metric.from_dict({"name": "x"})
        assert metric.value == 0.0
        assert metric.baseline is True

    def test_bottleneck_to_dict(self):
        bottleneck = Bottleneck(bottleneck_id="BOT-000001", kind="slow-api",
                                area="api", severity="high", count=3)
        data = bottleneck.to_dict()
        assert data["count"] == 3
        assert data["recommendation"] == ""

    def test_architecture_recommendation_to_dict(self):
        rec = ArchitectureRecommendation(recommendation_id="ARC-000001",
                                         technique="caching", area="backend")
        data = rec.to_dict()
        assert data["technique"] == "caching"

    def test_resource_recommendation_to_dict(self):
        rec = ResourceRecommendation(resource_id="RES-000001", target="redis",
                                     area="datastore", saving_type="memory")
        data = rec.to_dict()
        assert data["saving_type"] == "memory"

    def test_dx_finding_to_dict(self):
        finding = DxFinding(dx_id="DX-000001", dimension="tooling", score=80)
        data = finding.to_dict()
        assert data["score"] == 80

    def test_debt_item_to_dict(self):
        item = DebtItem(debt_id="DEBT-000001", kind="temporary-fixes",
                        area="code", severity="high")
        data = item.to_dict()
        assert data["status"] == "open"

    def test_optimization_run_delta(self):
        run = OptimizationRun(optimization_id="OPT-000001", target="bundle-size",
                              before_value=100.0, after_value=80.0)
        assert run.delta_pct() == -20.0
        assert run.improved() is True

    def test_optimization_run_positive_delta_not_improved(self):
        run = OptimizationRun(optimization_id="OPT-000002", target="api",
                              before_value=100.0, after_value=120.0)
        assert run.delta_pct() == 20.0
        assert run.improved() is False

    def test_optimization_run_zero_before_delta(self):
        run = OptimizationRun(optimization_id="OPT-000003", target="x",
                              before_value=0.0, after_value=10.0)
        assert run.delta_pct() == 0.0

    def test_evolution_proposal_to_dict(self):
        proposal = EvolutionProposal(proposal_id="EVO-000001",
                                     target="improvement-proposals",
                                     title="Evolve", rationale="why")
        data = proposal.to_dict()
        assert data["status"] == "open"

    def test_optimization_score_defaults(self):
        score = OptimizationScore()
        assert score.score == 100
        assert score.checks == {}
        assert score.regressions == []


class TestHelpers:
    def test_make_id_prefix(self):
        identifier = make_id("OPT")
        assert identifier.startswith("OPT-")
        assert len(identifier) == len("OPT-") + 8

    def test_make_id_unique(self):
        assert make_id("OPT") != make_id("OPT")

    def test_ensure_dirs_creates_state(self, tmp_path, monkeypatch):
        from scripts.optimizer import core as core_module

        monkeypatch.setattr(core_module, "STATE_DIR", tmp_path / "state")
        monkeypatch.setattr(core_module, "BENCHMARK_DIR", tmp_path / "bench")
        monkeypatch.setattr(core_module, "BOTTLENECK_DIR", tmp_path / "bots")
        monkeypatch.setattr(core_module, "DEBT_DIR", tmp_path / "debt")
        monkeypatch.setattr(core_module, "PROPOSAL_DIR", tmp_path / "proposals")
        monkeypatch.setattr(core_module, "HISTORY_DIR", tmp_path / "history")
        ensure_dirs()
        for directory in (tmp_path / "state", tmp_path / "bench",
                          tmp_path / "bots", tmp_path / "debt",
                          tmp_path / "proposals", tmp_path / "history"):
            assert directory.exists()

    def test_write_and_read_json_round_trip(self, tmp_path):
        path = tmp_path / "data.json"
        write_json(path, {"key": "value", "n": 1})
        assert read_json(path) == {"key": "value", "n": 1}

    def test_read_json_missing_returns_empty(self, tmp_path):
        assert read_json(tmp_path / "missing.json") == {}
