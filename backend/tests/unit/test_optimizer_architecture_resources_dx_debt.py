"""Unit tests for GULA-OPTIMIZER-001 — architecture, resources, dx, debt."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.optimizer.architecture import (
    load_architecture,
    persist_architecture,
    recommend_architecture,
)
from scripts.optimizer.debt import (
    detect_debt,
    load_debt,
    persist_debt,
    set_debt_status,
)
from scripts.optimizer.developer_experience import (
    assess_dx,
    average_score,
    load_dx,
    persist_dx,
)
from scripts.optimizer.resources import (
    load_resources,
    persist_resources,
    recommend_resources,
)


class TestArchitecture:
    def test_recommends_all_ten_techniques(self):
        recommendations = recommend_architecture()
        assert len(recommendations) == 10
        assert len({r.technique for r in recommendations}) == 10

    def test_ids_are_sequential(self):
        recommendations = recommend_architecture()
        assert [r.recommendation_id for r in recommendations] == [
            f"ARC-{i + 1:06d}" for i in range(10)
        ]

    def test_each_recommendation_has_rationale_and_impact(self):
        for recommendation in recommend_architecture():
            assert recommendation.rationale
            assert recommendation.expected_impact

    def test_areas_respected(self):
        recommendations = recommend_architecture(["frontend"])
        assert all(r.area == "frontend" for r in recommendations)

    def test_default_area_for_techniques(self):
        mapping = {
            recommendation.technique: recommendation.area
            for recommendation in recommend_architecture()
        }
        assert mapping["caching"] == "backend"
        assert mapping["indexing"] == "database"
        assert mapping["code-splitting"] == "frontend"
        assert mapping["queue-optimization"] == "infrastructure"

    def test_persist_and_load_round_trip(self, tmp_path, monkeypatch):
        from scripts.optimizer import architecture as arch_module

        monkeypatch.setattr(arch_module, "ARCH_PATH", tmp_path / "arch.json")
        recommendations = recommend_architecture()
        path = persist_architecture(recommendations)
        assert path.name == "arch.json"
        loaded = load_architecture()
        assert len(loaded) == 10
        assert loaded[0].technique == "module-boundaries"

    def test_load_architecture_missing_returns_empty(self, tmp_path, monkeypatch):
        from scripts.optimizer import architecture as arch_module

        monkeypatch.setattr(arch_module, "ARCH_PATH", tmp_path / "missing.json")
        assert load_architecture() == []


class TestResources:
    def test_recommends_all_ten_targets(self):
        recommendations = recommend_resources()
        assert len(recommendations) == 10
        assert len({r.target for r in recommendations}) == 10

    def test_ids_are_sequential(self):
        recommendations = recommend_resources()
        assert [r.resource_id for r in recommendations] == [
            f"RES-{i + 1:06d}" for i in range(10)
        ]

    def test_each_recommendation_has_saving_type(self):
        for recommendation in recommend_resources():
            assert recommendation.saving_type

    def test_filters_unknown_targets(self):
        recommendations = recommend_resources(["redis", "nonsense-target"])
        assert len(recommendations) == 1
        assert recommendations[0].target == "redis"

    def test_areas_mapped(self):
        mapping = {
            recommendation.target: recommendation.area
            for recommendation in recommend_resources()
        }
        assert mapping["redis"] == "datastore"
        assert mapping["docker-images"] == "docker"
        assert mapping["worker-usage"] == "backend"

    def test_persist_and_load_round_trip(self, tmp_path, monkeypatch):
        from scripts.optimizer import resources as resources_module

        monkeypatch.setattr(resources_module, "RESOURCES_PATH", tmp_path / "res.json")
        recommendations = recommend_resources()
        path = persist_resources(recommendations)
        assert path.name == "res.json"
        loaded = load_resources()
        assert len(loaded) == 10
        assert loaded[0].target == "docker-images"


class TestDeveloperExperience:
    def test_assesses_eight_dimensions(self):
        findings = assess_dx()
        assert len(findings) == 8

    def test_scores_within_bounds(self):
        for finding in assess_dx():
            assert 0 <= finding.score <= 100

    def test_dx_ids_sequential(self):
        findings = assess_dx()
        assert [f.dx_id for f in findings] == [
            f"DX-{i + 1:06d}" for i in range(8)
        ]

    def test_each_finding_has_recommendation(self):
        for finding in assess_dx():
            assert finding.recommendation

    def test_empty_repo_scores_low(self, tmp_path):
        findings = assess_dx(root=tmp_path)
        assert all(f.score < 60 for f in findings)

    def test_full_tooling_scores_high(self, tmp_path):
        (tmp_path / "backend").mkdir(parents=True)
        (tmp_path / "backend" / "pyproject.toml").write_text("", encoding="utf-8")
        (tmp_path / "frontend-v3").mkdir()
        (tmp_path / "frontend-v3" / "package.json").write_text("{}", encoding="utf-8")
        (tmp_path / "frontend-v3" / "vite.config.ts").write_text("", encoding="utf-8")
        (tmp_path / ".github" / "workflows").mkdir(parents=True)
        (tmp_path / "backend" / "tests").mkdir()
        findings = {f.dimension: f for f in assess_dx(root=tmp_path)}
        assert findings["build-speed"].score == 100
        assert findings["test-speed"].score >= 66

    def test_persist_and_load_round_trip(self, tmp_path, monkeypatch):
        from scripts.optimizer import developer_experience as dx_module

        monkeypatch.setattr(dx_module, "DX_PATH", tmp_path / "dx.json")
        findings = assess_dx()
        path = persist_dx(findings)
        assert path.name == "dx.json"
        loaded = load_dx()
        assert len(loaded) == 8

    def test_average_score(self):
        findings = assess_dx()
        avg = average_score(findings)
        assert 0 <= avg <= 100

    def test_average_score_empty(self, tmp_path, monkeypatch):
        from scripts.optimizer import developer_experience as dx_module

        monkeypatch.setattr(dx_module, "DX_PATH", tmp_path / "missing.json")
        assert average_score([]) == 0.0


class TestDebt:
    def test_detect_debt_returns_records(self):
        items = detect_debt()
        assert isinstance(items, list)

    def test_detected_records_have_fields(self):
        for item in detect_debt():
            assert item.debt_id.startswith("DEBT-")
            assert item.kind in {
                "duplicated-logic", "deprecated-code", "temporary-fixes",
                "architecture-drift", "dependency-problems",
                "configuration-drift", "documentation-drift",
            }
            assert item.status == "open"
            assert item.impact
            assert item.recommendation

    def test_detect_in_tmp_repo(self, tmp_path):
        (tmp_path / "backend" / "app").mkdir(parents=True)
        (tmp_path / "backend" / "app" / "x.py").write_text(
            "# HACK\n", encoding="utf-8"
        )
        items = detect_debt(root=tmp_path)
        assert any(item.kind == "temporary-fixes" for item in items)

    def test_no_debt_in_empty_repo(self, tmp_path):
        assert detect_debt(root=tmp_path) == []

    def test_persist_and_load_round_trip(self, tmp_path, monkeypatch):
        from scripts.optimizer import debt as debt_module

        monkeypatch.setattr(debt_module, "DEBT_PATH", tmp_path / "debt.json")
        items = detect_debt()
        path = persist_debt(items)
        assert path.name == "debt.json"
        loaded = load_debt()
        assert len(loaded) == len(items)

    def test_set_debt_status(self, tmp_path, monkeypatch):
        from scripts.optimizer import debt as debt_module

        monkeypatch.setattr(debt_module, "DEBT_PATH", tmp_path / "debt.json")
        items = detect_debt()
        persist_debt(items)
        if not items:
            return
        updated = set_debt_status(items[0].debt_id, "addressed")
        assert updated is not None
        assert updated.status == "addressed"
        assert load_debt()[0].status == "addressed"

    def test_set_debt_status_invalid(self, tmp_path, monkeypatch):
        from scripts.optimizer import debt as debt_module

        monkeypatch.setattr(debt_module, "DEBT_PATH", tmp_path / "debt.json")
        persist_debt(detect_debt())
        try:
            set_debt_status("DEBT-000001", "nonsense")
            raise AssertionError("expected ValueError")
        except ValueError:
            pass

    def test_set_debt_status_missing_id(self, tmp_path, monkeypatch):
        from scripts.optimizer import debt as debt_module

        monkeypatch.setattr(debt_module, "DEBT_PATH", tmp_path / "debt.json")
        persist_debt(detect_debt())
        assert set_debt_status("DEBT-999999", "addressed") is None
