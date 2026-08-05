"""Unit tests for GULA-ORCHESTRATOR-001 — Phase 9 Mission History."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.orchestrator.core import MissionRecord
from scripts.orchestrator.history import (
    add_decision,
    add_event,
    add_failure,
    add_recovery,
    close_mission,
    completion_report,
    load_record,
    persist_record,
)


class TestRecordEvents:
    def test_add_event_appends_timeline(self):
        record = MissionRecord(mission_id="ORN-H1", objective="X")
        add_event(record, "mission received")
        assert len(record.timeline) == 1
        assert record.timeline[0]["event"] == "mission received"

    def test_add_decision_appends_decision_log(self):
        record = MissionRecord(mission_id="ORN-H1", objective="X")
        add_decision(record, "use shared core", "avoid import cycles")
        assert record.decisions[0]["decision"] == "use shared core"
        assert record.decisions[0]["rationale"] == "avoid import cycles"

    def test_add_failure_appends_history(self):
        record = MissionRecord(mission_id="ORN-H1", objective="X")
        add_failure(record, "OTASK-1", "timeout", "temporary")
        assert record.failure_history[0]["failure_class"] == "temporary"

    def test_add_recovery_appends_history(self):
        record = MissionRecord(mission_id="ORN-H1", objective="X")
        add_recovery(record, "OTASK-1", "retried")
        assert record.recovery_history[0]["action"] == "retried"

    def test_close_mission_sets_closed(self):
        record = MissionRecord(mission_id="ORN-H1", objective="X")
        close_mission(record, verdict="completed")
        assert record.status == "closed"
        assert record.closed_at
        assert record.timeline[-1]["event"] == "mission closed"

    def test_close_mission_failed(self):
        record = MissionRecord(mission_id="ORN-H1", objective="X")
        close_mission(record, verdict="failed")
        assert record.status == "failed"


class TestPersistence:
    def test_persist_and_load_roundtrip(self):
        record = MissionRecord(
            mission_id="ORN-H2", objective="Build X", mission_type="feature",
            status="executing",
        )
        add_event(record, "mission received")
        persist_record(record)
        loaded = load_record("ORN-H2")
        assert loaded.objective == "Build X"
        assert loaded.mission_type == "feature"
        assert len(loaded.timeline) == 1

    def test_load_missing_returns_default(self):
        loaded = load_record("ORN-NOPE")
        assert loaded.mission_id == "ORN-NOPE"
        assert loaded.status == "received"

    def test_to_dict_preserves_lists(self):
        record = MissionRecord(mission_id="ORN-H3", objective="X")
        add_decision(record, "d1")
        data = record.to_dict()
        assert data["decisions"] == [{"decision": "d1", "rationale": ""}]


class TestCompletionReport:
    def test_report_contains_mission_id(self):
        record = MissionRecord(mission_id="ORN-H4", objective="Build X")
        text = completion_report(record)
        assert "ORN-H4" in text
        assert "Build X" in text

    def test_report_lists_timeline(self):
        record = MissionRecord(mission_id="ORN-H4", objective="X")
        add_event(record, "received")
        assert "received" in completion_report(record)
