"""Unit tests for GULA-OPTIMIZER-001 — audit, analyze, bottleneck phases."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.optimizer.analyze import (
    METRIC_EVIDENCE,
    measure_baseline,
    measure_metric,
)
from scripts.optimizer.audit import (
    AUDIT_PATTERNS,
    audit_system,
    render_markdown,
)
from scripts.optimizer.bottlenecks import (
    detect_bottlenecks,
    load_bottlenecks,
    persist_bottlenecks,
)


class TestAudit:
    def test_audit_patterns_cover_all_components(self):
        from scripts.optimizer.core import AUDIT_COMPONENTS

        for component in AUDIT_COMPONENTS:
            assert component in AUDIT_PATTERNS

    def test_audit_system_returns_eleven_items(self):
        items = audit_system()
        assert len(items) == 11
        assert all(item.item_id.startswith("OA-") for item in items)

    def test_audit_detects_backend(self):
        items = {item.title: item for item in audit_system()}
        assert items["backend"].status == "measured"
        assert "backend/app" in items["backend"].body

    def test_audit_render_contains_verdict(self):
        text = render_markdown(audit_system())
        assert "AUDIT COMPLETE" in text
        assert "optimization areas present" in text


class TestAnalyze:
    def test_metric_evidence_cover_eleven(self):
        assert len(METRIC_EVIDENCE) == 11

    def test_measure_metric_deterministic(self, tmp_path):
        (tmp_path / "backend" / "app" / "routes").mkdir(parents=True)
        (tmp_path / "backend" / "app" / "routes" / "a.py").write_text("x", encoding="utf-8")
        (tmp_path / "backend" / "app" / "routes" / "b.py").write_text("y", encoding="utf-8")
        metric = measure_metric("api-latency", root=tmp_path)
        assert metric.value == 2
        assert metric.unit == "routes"
        assert metric.baseline is True

    def test_measure_metric_missing_evidence_zero(self, tmp_path):
        metric = measure_metric("api-latency", root=tmp_path)
        assert metric.value == 0

    def test_measure_metric_bytes_units(self, tmp_path):
        (tmp_path / "backend" / "app").mkdir(parents=True)
        (tmp_path / "backend" / "app" / "m.py").write_text("abcd", encoding="utf-8")
        metric = measure_metric("disk-usage", root=tmp_path)
        assert metric.unit == "bytes"
        assert metric.value >= 4

    def test_measure_baseline_round_trip(self, tmp_path, monkeypatch):
        from scripts.optimizer import analyze as analyze_module

        monkeypatch.setattr(analyze_module, "BENCHMARK_PATH",
                            tmp_path / "bench.json")
        metrics = measure_baseline(root=tmp_path)
        assert len(metrics) == 11
        assert (tmp_path / "bench.json").exists()


class TestBottlenecks:
    def test_detects_duplicate_queries_from_evidence(self):
        found = detect_bottlenecks([
            ("database", "duplicate queries same query twice"),
            ("database", "duplicate queries same query twice"),
        ])
        assert any(b.kind == "duplicate-queries" for b in found)

    def test_detects_large_bundle(self):
        found = detect_bottlenecks([
            ("frontend", "large bundle bundle size grows"),
            ("frontend", "large bundle bundle size grows"),
        ])
        assert any(b.kind == "large-bundle" for b in found)

    def test_detects_slow_api(self):
        found = detect_bottlenecks([
            ("api", "slow endpoint latency p99 timeout"),
            ("api", "slow endpoint latency p99 timeout"),
        ])
        assert any(b.kind == "slow-api" for b in found)

    def test_single_evidence_does_not_cross_threshold(self):
        found = detect_bottlenecks([
            ("database", "duplicate queries same query twice"),
        ])
        assert not any(b.kind == "duplicate-queries" for b in found)

    def test_severity_scales_with_count(self):
        found = detect_bottlenecks([
            ("api", "slow endpoint latency p99 timeout"),
            ("api", "slow endpoint latency p99 timeout"),
            ("api", "slow endpoint latency p99 timeout"),
        ])
        slow = next(b for b in found if b.kind == "slow-api")
        assert slow.severity == "high"
        assert slow.count == 3

    def test_critical_severity_for_memory_leak(self):
        found = detect_bottlenecks([
            ("memory", "memory leak retained growth"),
            ("memory", "memory leak retained growth"),
        ])
        assert any(b.severity == "high" for b in found)

    def test_ids_are_sequential(self):
        found = detect_bottlenecks([
            ("api", "slow endpoint latency p99 timeout"),
            ("api", "slow endpoint latency p99 timeout"),
            ("database", "duplicate queries same query twice"),
            ("database", "duplicate queries same query twice"),
        ])
        assert [b.bottleneck_id for b in found] == ["BOT-000001", "BOT-000002"]

    def test_recommendation_present(self):
        found = detect_bottlenecks([
            ("database", "duplicate queries same query twice"),
            ("database", "duplicate queries same query twice"),
        ])
        duplicate = next(b for b in found if b.kind == "duplicate-queries")
        assert "single prepared statement" in duplicate.recommendation

    def test_unknown_kind_ignored(self):
        found = detect_bottlenecks([
            ("api", "this is not a bottleneck text"),
            ("api", "this is not a bottleneck text"),
        ])
        assert found == []

    def test_persist_and_load_round_trip(self, tmp_path, monkeypatch):
        from scripts.optimizer import bottlenecks as bottlenecks_module

        monkeypatch.setattr(bottlenecks_module, "BOTTLENECK_DIR", tmp_path)
        found = detect_bottlenecks([
            ("database", "duplicate queries same query twice"),
            ("database", "duplicate queries same query twice"),
        ])
        path = persist_bottlenecks(found)
        assert path.name == "bottlenecks.json"
        loaded = load_bottlenecks()
        assert len(loaded) == len(found)
        assert loaded[0].kind == "duplicate-queries"
