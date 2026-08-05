"""Unit tests for GULA-ORCHESTRATOR-001 — core constants and dataclasses."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.orchestrator.core import (
    ENGINES,
    MISSION_TYPE_NAMES,
    MISSION_TYPES,
    SURFACE_ROUTING,
    Checkpoint,
    FailureClass,
    MissionClassification,
    MissionRecord,
    MissionStatus,
    OrchestratedPlan,
    TaskStatus,
    make_id,
)


class TestEngineConstants:
    def test_engines_include_core_six(self):
        assert "kernel" in ENGINES
        assert "builder" in ENGINES
        assert "reviewer" in ENGINES
        assert "deployer" in ENGINES
        assert "learner" in ENGINES
        assert "optimizer" in ENGINES

    def test_surface_routing_covers_primary_surfaces(self):
        for surface in ("backend", "frontend", "database", "deployment", "verification"):
            assert surface in SURFACE_ROUTING

    def test_surface_routing_maps_to_known_engine(self):
        for surface, engine in SURFACE_ROUTING.items():
            assert engine in ENGINES, f"{surface} -> {engine}"

    def test_mission_types_include_all_twelve(self):
        assert len(MISSION_TYPES) == 12
        assert set(MISSION_TYPES) == {
            "feature", "bug", "refactor", "deployment", "security", "performance",
            "architecture", "documentation", "knowledge", "infrastructure",
            "testing", "research",
        }

    def test_mission_type_names_cover_all_types(self):
        assert set(MISSION_TYPE_NAMES) == set(MISSION_TYPES)


class TestStatusEnums:
    def test_mission_status_values_unique(self):
        values = [s.value for s in MissionStatus]
        assert len(values) == len(set(values))

    def test_task_status_has_completed(self):
        assert TaskStatus.COMPLETED.value == "completed"

    def test_failure_class_has_all_taxonomy(self):
        values = [f.value for f in FailureClass]
        assert "temporary" in values
        assert "permanent" in values
        assert "credential" in values
        assert "infrastructure" in values


class TestMakeId:
    def test_make_id_prefix(self):
        assert make_id("ORN").startswith("ORN-")

    def test_make_id_unique_suffix(self):
        assert make_id("ORN") != make_id("ORN")

    def test_make_id_uppercase_hex(self):
        suffix = make_id("ORN").split("-")[1]
        assert len(suffix) == 8
        assert all(c in "0123456789ABCDEF" for c in suffix)


class TestClassificationDataclass:
    def test_defaults(self):
        c = MissionClassification(objective="Build X")
        assert c.mission_type == ""
        assert c.priority == "medium"
        assert c.complexity == "low"
        assert c.risk == "low"

    def test_to_dict_roundtrip(self):
        c = MissionClassification(
            objective="X", mission_type="feature", duration_minutes=20,
            required_specialists=["python", "react"],
        )
        data = c.to_dict()
        assert data["mission_type"] == "feature"
        assert data["required_specialists"] == ["python", "react"]
        assert isinstance(data["required_specialists"], list)


class TestRecordAndPlan:
    def test_plan_all_done_empty(self):
        plan = OrchestratedPlan(plan_id="OPL-1", mission_id="ORN-1", objective="X")
        assert plan.all_done()

    def test_plan_all_done_with_pending(self):
        from scripts.orchestrator.core import AssignedTask

        plan = OrchestratedPlan(plan_id="OPL-1", mission_id="ORN-1", objective="X")
        plan.tasks.append(AssignedTask(task_id="OTASK-1", name="t", engine="builder", surface="backend"))
        assert not plan.all_done()

    def test_record_to_dict_roundtrip(self):
        record = MissionRecord(
            mission_id="ORN-1", objective="X", mission_type="feature",
            timeline=[{"event": "received"}],
        )
        data = record.to_dict()
        assert data["mission_id"] == "ORN-1"
        assert data["timeline"] == [{"event": "received"}]

    def test_checkpoint_to_dict_roundtrip(self):
        cp = Checkpoint(checkpoint_id="OCK-1", mission_id="ORN-1", step="routed", state={"ok": True})
        data = cp.to_dict()
        assert data["state"] == {"ok": True}
