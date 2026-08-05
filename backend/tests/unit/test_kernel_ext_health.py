"""Unit tests for GULA-KERNEL-EXT-001 Phase 10 — Health Engine."""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.kernel.ext.health import (
    ComponentHealth,
    HealthError,
    HealthReport,
    extension_health,
    is_ready,
    score_components,
)


def _components(**overrides) -> list[ComponentHealth]:
    base = [
        ComponentHealth("plugin_sdk", "pass", weight=2.0, critical=True),
        ComponentHealth("policy_engine", "pass", weight=2.0, critical=True),
        ComponentHealth("compatibility", "pass", weight=2.0, critical=True),
        ComponentHealth("migration", "pass", weight=1.0, critical=True),
        ComponentHealth("event_bus", "pass", weight=1.0, critical=True),
        ComponentHealth("workflow", "pass", weight=1.0, critical=True),
    ]
    for key, value in overrides.items():
        idx = {"plugin_sdk": 0, "policy_engine": 1, "compatibility": 2,
               "migration": 3, "event_bus": 4, "workflow": 5}[key]
        base[idx] = value
    return base


class TestComponent:
    def test_valid_component(self):
        component = ComponentHealth("x", "pass")
        assert component.weight == 1.0
        assert not component.critical

    def test_bad_status(self):
        with pytest.raises(HealthError):
            ComponentHealth("x", "maybe")

    def test_bad_weight(self):
        with pytest.raises(HealthError):
            ComponentHealth("x", "pass", weight=0)


class TestScoring:
    def test_all_pass(self):
        report = score_components(_components())
        assert report.health == 100.0
        assert report.risk == 0.0
        assert report.readiness == 100.0

    def test_weighted_partial(self):
        report = score_components(_components(compatibility=ComponentHealth("compatibility", "fail", weight=2.0, critical=True)))
        assert report.health == pytest.approx(77.8)
        assert report.risk == pytest.approx(22.2)

    def test_critical_fail_halves_readiness(self):
        report = score_components(_components(workflow=ComponentHealth("workflow", "fail", weight=1.0, critical=True)))
        assert report.health == pytest.approx(88.9)
        assert report.readiness == pytest.approx(44.5)

    def test_non_critical_fail_keeps_readiness(self):
        report = score_components([ComponentHealth("a", "pass", weight=1.0),
                                   ComponentHealth("b", "fail", weight=1.0, critical=False)])
        assert report.health == 50.0
        assert report.readiness == 50.0

    def test_empty_raises(self):
        with pytest.raises(HealthError):
            score_components([])

    def test_report_dict(self):
        report = score_components(_components())
        data = report.to_dict()
        assert data["health"] == 100.0
        assert "components" in data


class TestReadiness:
    def test_is_ready(self):
        report = score_components(_components())
        assert is_ready(report)
        assert not is_ready(report, threshold=150.0)


class TestExtensionHealth:
    def test_live_scores(self):
        report = extension_health()
        assert 0.0 <= report.health <= 100.0
        assert 0.0 <= report.risk <= 100.0
        assert 0.0 <= report.readiness <= 100.0
        assert report.components

    def test_live_all_pass(self):
        report = extension_health()
        assert all(c.status == "pass" for c in report.components)
        assert report.health == 100.0
        assert report.readiness == 100.0
