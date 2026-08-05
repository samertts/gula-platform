"""Unit tests for GULA-ORCHESTRATOR-001 — Phase 5 Checkpoint Engine."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

import pytest

from scripts.orchestrator import checkpoint as checkpoint_module
from scripts.orchestrator.checkpoint import (
    checkpoint_count,
    latest_checkpoint,
    resume_state,
    save_checkpoint,
    step_progress,
)

TEST_MISSION = "ORN-CKPT-TEST"


@pytest.fixture(autouse=True)
def _isolated_checkpoint_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(checkpoint_module, "CHECKPOINT_DIR", tmp_path)


class TestCheckpoint:
    def test_save_and_latest(self):
        save_checkpoint(TEST_MISSION, "classified", {"type": "feature"}, checkpoint_id="OCK-CK1")
        latest = latest_checkpoint(TEST_MISSION)
        assert latest is not None
        assert latest.step == "classified"
        assert latest.state["type"] == "feature"

    def test_latest_returns_most_recent(self):
        save_checkpoint(TEST_MISSION, "planned", {"tasks": 9}, checkpoint_id="OCK-CK2")
        latest = latest_checkpoint(TEST_MISSION)
        assert latest.step == "planned"

    def test_resume_state_returns_latest(self):
        save_checkpoint(TEST_MISSION, "planned", {"tasks": 9}, checkpoint_id="OCK-CK2")
        state = resume_state(TEST_MISSION)
        assert state.get("tasks") == 9

    def test_checkpoint_count_increments(self):
        save_checkpoint(TEST_MISSION, "a", {}, checkpoint_id="OCK-CKA")
        save_checkpoint(TEST_MISSION, "b", {}, checkpoint_id="OCK-CKB")
        save_checkpoint(TEST_MISSION, "c", {}, checkpoint_id="OCK-CKC")
        assert checkpoint_count(TEST_MISSION) == 3

    def test_step_progress_matches_latest(self):
        save_checkpoint(TEST_MISSION, "routed", {}, checkpoint_id="OCK-CK3")
        assert step_progress(TEST_MISSION, "routed") == "OCK-CK3"

    def test_no_checkpoint_empty(self):
        assert latest_checkpoint("ORN-NONE") is None
        assert resume_state("ORN-NONE") == {}
        assert checkpoint_count("ORN-NONE") == 0
        assert step_progress("ORN-NONE", "x") is None

    def test_checkpoint_id_unique_when_auto(self):
        a = save_checkpoint(TEST_MISSION, "a", {})
        b = save_checkpoint(TEST_MISSION, "b", {})
        assert a.checkpoint_id != b.checkpoint_id

    def test_roundtrip_preserves_state(self):
        save_checkpoint(TEST_MISSION, "verify", {"ok": True, "n": 3}, checkpoint_id="OCK-CK4")
        restored = latest_checkpoint(TEST_MISSION)
        assert restored.state == {"ok": True, "n": 3}
