"""Unit tests for GULA-KERNEL-EXT-001 Phase 4 — Migration Framework."""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.kernel.ext.migration import (
    MIGRATION_STATES,
    MIGRATION_TARGETS,
    MigrationEngine,
    MigrationError,
    MigrationPlan,
    MigrationStep,
    _demo_plan,
)


def _plan(**overrides) -> MigrationPlan:
    calls = []

    def forward() -> None:
        calls.append("forward")

    def backward() -> None:
        calls.append("backward")

    base = {
        "id": "MIGR-100001",
        "title": "test migration",
        "target": "policy",
        "from_version": "1.0.0",
        "to_version": "1.0.1",
        "steps": [MigrationStep("forward", forward)],
        "rollback_steps": [MigrationStep("backward", backward)],
    }
    base.update(overrides)
    return MigrationPlan(**base)


class TestPlan:
    def test_valid_plan(self):
        plan = _plan()
        assert plan.state == "planned"

    def test_bad_id(self):
        with pytest.raises(MigrationError):
            _plan(id="BAD-1")

    def test_bad_target(self):
        with pytest.raises(MigrationError):
            _plan(target="nope")

    def test_bad_state(self):
        with pytest.raises(MigrationError):
            _plan(state="bogus")

    def test_all_targets_and_states_valid(self):
        for target in MIGRATION_TARGETS:
            for state in MIGRATION_STATES:
                plan = _plan(target=target, state=state)
                assert plan.target == target
                assert plan.state == state


class TestEngine:
    def test_register_and_get(self):
        engine = MigrationEngine()
        plan = engine.register(_plan())
        assert engine.get("MIGR-100001") is plan

    def test_duplicate_register_raises(self):
        engine = MigrationEngine()
        engine.register(_plan())
        with pytest.raises(MigrationError):
            engine.register(_plan())

    def test_execute(self):
        engine = MigrationEngine()
        plan = engine.register(_plan())
        engine.execute(plan.id)
        assert plan.state == "executed"
        assert plan.executed_at

    def test_execute_sets_history(self):
        engine = MigrationEngine()
        plan = engine.register(_plan())
        engine.execute(plan.id)
        events = [h["event"] for h in engine.snapshot()["history"]]
        assert "registered" in events and "executed" in events

    def test_execute_twice_raises(self):
        engine = MigrationEngine()
        plan = engine.register(_plan())
        engine.execute(plan.id)
        with pytest.raises(MigrationError):
            engine.execute(plan.id)

    def test_failure_triggers_rollback(self):
        engine = MigrationEngine()

        def explode() -> None:
            raise RuntimeError("boom")

        plan = engine.register(_plan(steps=[MigrationStep("explode", explode)]))
        with pytest.raises(MigrationError):
            engine.execute(plan.id)
        assert plan.state == "rolled_back"
        events = [h["event"] for h in engine.snapshot()["history"]]
        assert "failed" in events and "rolled_back" in events

    def test_rollback_without_steps_raises(self):
        engine = MigrationEngine()
        plan = engine.register(_plan(rollback_steps=[]))
        engine.execute(plan.id)
        with pytest.raises(MigrationError):
            engine.rollback(plan.id)

    def test_precheck_failure_rolls_back(self):
        engine = MigrationEngine()

        def bad_precheck() -> None:
            raise ValueError("precheck failed")

        plan = engine.register(_plan(precheck=bad_precheck))
        with pytest.raises(MigrationError):
            engine.execute(plan.id)
        assert plan.state == "rolled_back"

    def test_is_breaking(self):
        engine = MigrationEngine()
        engine.register(_plan(from_version="1.0.0", to_version="2.0.0"))
        assert engine.is_breaking("MIGR-100001")
        engine.register(_plan(id="MIGR-100002", from_version="1.0.0", to_version="1.1.0"))
        assert not engine.is_breaking("MIGR-100002")

    def test_plans_by_state(self):
        engine = MigrationEngine()
        engine.register(_plan())
        engine.register(_plan(id="MIGR-100002"))
        engine.execute("MIGR-100001")
        assert len(engine.plans("executed")) == 1
        assert len(engine.plans("planned")) == 1

    def test_snapshot_persists_metadata(self, tmp_path):
        engine = MigrationEngine()
        plan = engine.register(_plan())
        engine.execute(plan.id)
        path = engine.save(tmp_path / "migrations.json")
        data = path.read_text(encoding="utf-8")
        assert "MIGR-100001" in data
        assert "executed" in data

    def test_unknown_plan_raises(self):
        engine = MigrationEngine()
        with pytest.raises(MigrationError):
            engine.get("MIGR-000000")


class TestDemo:
    def test_demo_plan_valid_and_executable(self):
        engine = MigrationEngine()
        plan = engine.register(_demo_plan())
        engine.execute(plan.id)
        assert plan.state == "executed"
        assert plan.id == "MIGR-000001"
        assert plan.target == "policy"
