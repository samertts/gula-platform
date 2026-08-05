"""Unit tests for GULA-BUILDER-001 Phase 4 — Execution Engine."""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.builder.executor import (
    ExecutionError,
    execute_mission,
    make_mission_id,
    resume_from,
)
from scripts.builder.planner import EXECUTION_ORDER


def _ok_handlers():
    return {step: lambda step=step, ctx=None: {"ok": True, "step": step} for step in EXECUTION_ORDER}


class TestExecuteMission:
    def test_completes_all_steps(self):
        result = execute_mission("MSN-TEST", handlers=_ok_handlers())
        assert result.status == "completed"
        assert result.completed_steps == list(EXECUTION_ORDER)
        assert result.failed_step == ""
        assert not result.error

    def test_default_handlers_pass(self):
        result = execute_mission("MSN-TEST")
        assert result.status == "completed"
        assert len(result.completed_steps) == 10

    def test_failure_stops(self):
        def failing(step, ctx):
            if step == "test":
                raise RuntimeError("boom")
            return {"ok": True}

        result = execute_mission("MSN-TEST", handlers={"test": failing})
        assert result.status == "failed"
        assert result.failed_step == "test"
        assert result.error == "boom"
        assert result.completed_steps == ["analyze", "plan", "validate", "execute"]

    def test_handler_not_ok_fails(self):
        def bad(step, ctx):
            return {"ok": False, "error": "nope"}

        result = execute_mission("MSN-TEST", handlers={"execute": bad})
        assert result.status == "failed"
        assert result.failed_step == "execute"
        assert result.error == "nope"

    def test_unknown_start_step(self):
        with pytest.raises(ExecutionError):
            execute_mission("MSN-TEST", start_from="bogus")

    def test_resume_from_start(self):
        result = execute_mission("MSN-TEST", handlers=_ok_handlers(), start_from="validate")
        assert result.status == "completed"
        assert result.completed_steps[:2] == ["analyze", "plan"]
        assert result.completed_steps[2:] == list(EXECUTION_ORDER[2:])

    def test_checkpoint_callback_invoked(self):
        seen = []

        def cb(step, ctx):
            seen.append(step)

        execute_mission("MSN-TEST", handlers=_ok_handlers(), checkpoint_callback=cb)
        assert seen == list(EXECUTION_ORDER)

    def test_context_collects_step_results(self):
        captured = {}

        def cb(step, ctx):
            captured.update(ctx.get("steps", {}))

        execute_mission("MSN-TEST", handlers=_ok_handlers(), checkpoint_callback=cb)
        assert set(captured) == set(EXECUTION_ORDER)


class TestResume:
    def test_completed_returns_none(self):
        result = execute_mission("MSN-TEST", handlers=_ok_handlers())
        assert resume_from(result) is None

    def test_failed_returns_next_step(self):
        def failing(step, ctx):
            if step == "test":
                raise RuntimeError("boom")
            return {"ok": True}

        result = execute_mission("MSN-TEST", handlers={"test": failing})
        assert resume_from(result) == "test"

    def test_empty_returns_first(self):
        result = execute_mission("MSN-TEST", handlers={"analyze": lambda s, c: {"ok": False}})
        assert resume_from(result) == "analyze"

    def test_mid_failure_resume(self):
        def failing(step, ctx):
            if step == "document":
                raise RuntimeError("boom")
            return {"ok": True}

        result = execute_mission("MSN-TEST", handlers={"document": failing})
        assert resume_from(result) == "document"


class TestMissionId:
    def test_unique(self):
        assert make_mission_id() != make_mission_id()

    def test_prefix(self):
        assert make_mission_id("MSN").startswith("MSN-")
