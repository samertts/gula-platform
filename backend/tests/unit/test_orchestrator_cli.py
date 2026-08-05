"""Unit tests for GULA-ORCHESTRATOR-001 — Phase 10 Report + CLI."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.orchestrator.cli import (
    ORCHESTRATOR_COMMANDS,
    run_check,
    run_classify,
    run_mission,
)
from scripts.orchestrator.core import ENGINES
from scripts.orchestrator.report import mission_stats, render, write_report


class TestMissionStats:
    def test_empty_stats(self):
        stats = mission_stats([])
        assert stats["total"] == 0
        assert stats["by_type"] == {}

    def test_stats_aggregate(self):
        records = [
            {"status": "closed", "mission_type": "feature",
             "failure_history": [{}], "recovery_history": [{}],
             "decisions": [{}], "assigned_tasks": 9, "completed_tasks": 9},
            {"status": "failed", "mission_type": "bug",
             "failure_history": [{}], "recovery_history": [],
             "decisions": [], "assigned_tasks": 5, "completed_tasks": 2},
        ]
        stats = mission_stats(records)
        assert stats["total"] == 2
        assert stats["closed"] == 1
        assert stats["failed"] == 1
        assert stats["by_type"] == {"feature": 1, "bug": 1}
        assert stats["failures"] == 2
        assert stats["tasks_assigned"] == 14
        assert stats["tasks_completed"] == 11


class TestReportRender:
    def test_render_contains_engines(self):
        text = render([])
        assert "Orchestrator" in text
        assert "Phase Coverage" in text
        assert "Mission Statistics" in text

    def test_render_lists_all_engines(self):
        text = render([])
        for engine in ENGINES:
            assert engine in text

    def test_write_report_persists(self, tmp_path):
        path = write_report(tmp_path / "ORCHESTRATOR_REPORT.md")
        assert path.exists()
        assert "Orchestrator" in path.read_text(encoding="utf-8")


class TestCliCommands:
    def test_all_commands_registered(self):
        expected = {
            "orchestrator-audit", "orchestrator-mission", "orchestrator-classify",
            "orchestrator-plan", "orchestrator-route", "orchestrator-checkpoint",
            "orchestrator-resume", "orchestrator-status", "orchestrator-history",
            "orchestrator-report", "orchestrator-check",
        }
        assert expected <= set(ORCHESTRATOR_COMMANDS)

    def test_self_check_passes(self):
        assert run_check() == 0

    def test_classify_without_objective_returns_usage(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["kernel", "orchestrator-classify"])
        assert run_classify() == 2

    def test_mission_without_objective_returns_usage(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["kernel", "orchestrator-mission"])
        assert run_mission() == 2

    def test_mission_pipeline_end_to_end(self, monkeypatch, capsys):
        monkeypatch.setattr(
            sys, "argv", ["kernel", "orchestrator-mission", "Build Patient Management"]
        )
        assert run_mission() == 0
        out = capsys.readouterr().out
        assert "MISSION ORN-" in out
        assert "critical path" in out
