"""Unit tests for GULA-BUILDER-001 Phase 5 — Failure Recovery."""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.builder.core import Checkpoint
from scripts.builder.recovery import (
    MAX_RETRIES,
    FailureAnalysis,
    analyze_failure,
    backoff_for,
    checkpoint_age_seconds,
    checkpoint_path,
    classify_failure,
    clear_checkpoint,
    create_checkpoint,
    is_stale,
    list_checkpoints,
    load_checkpoint,
    resume_step,
    retry,
)


class TestClassify:
    def test_transient_markers(self):
        assert classify_failure(TimeoutError("connection timeout")) == "transient"
        assert classify_failure(RuntimeError("temporarily unavailable")) == "transient"

    def test_validation_markers(self):
        assert classify_failure(ValueError("invalid schema")) == "validation"

    def test_permanent(self):
        assert classify_failure(RuntimeError("boom")) == "permanent"

    def test_none_detail(self):
        assert classify_failure(None) == "permanent"


class TestAnalyze:
    def test_transient_retries(self):
        analysis = analyze_failure("MSN-1", "execute", TimeoutError("timeout"), retries_used=1)
        assert analysis.classification == "transient"
        assert analysis.action == "retry"
        assert analysis.retries_left == MAX_RETRIES - 1

    def test_transient_exhausted_resumes(self):
        analysis = analyze_failure("MSN-1", "execute", TimeoutError("timeout"), retries_used=MAX_RETRIES)
        assert analysis.action == "resume"

    def test_permanent_aborts(self):
        analysis = analyze_failure("MSN-1", "execute", RuntimeError("boom"))
        assert analysis.action == "abort"

    def test_validation_resumes(self):
        analysis = analyze_failure("MSN-1", "execute", ValueError("invalid input"))
        assert analysis.action == "resume"

    def test_to_dict(self):
        analysis = analyze_failure("MSN-1", "test", RuntimeError("boom"))
        data = analysis.to_dict()
        assert data["mission_id"] == "MSN-1"
        assert data["action"] == "abort"


class TestCheckpoint:
    def test_create_and_load(self):
        mission = "MSN-CHK"
        clear_checkpoint(mission)
        checkpoint = create_checkpoint(mission, "execute", {"tests": []})
        assert checkpoint.checkpoint_id.startswith("CHK-")
        loaded = load_checkpoint(mission)
        assert loaded is not None
        assert loaded.step == "execute"
        assert loaded.state == {"tests": []}
        clear_checkpoint(mission)

    def test_load_missing(self):
        clear_checkpoint("MSN-MISSING")
        assert load_checkpoint("MSN-MISSING") is None

    def test_list_checkpoints(self):
        mission = "MSN-LIST"
        clear_checkpoint(mission)
        create_checkpoint(mission, "analyze")
        checkpoints = list_checkpoints()
        assert any(c.mission_id == mission for c in checkpoints)
        clear_checkpoint(mission)

    def test_clear(self):
        mission = "MSN-CLEAR"
        create_checkpoint(mission, "plan")
        assert load_checkpoint(mission) is not None
        clear_checkpoint(mission)
        assert load_checkpoint(mission) is None

    def test_checkpoint_path_under_checkpoint_dir(self):
        path = checkpoint_path("MSN-X")
        assert path.name == "MSN-X.json"

    def test_resume_step(self):
        mission = "MSN-RESUME"
        clear_checkpoint(mission)
        create_checkpoint(mission, "validate")
        assert resume_step(mission) == "execute"
        clear_checkpoint(mission)

    def test_resume_none_when_missing(self):
        clear_checkpoint("MSN-NOCHK")
        assert resume_step("MSN-NOCHK") is None

    def test_resume_last_step_none(self):
        mission = "MSN-LAST"
        clear_checkpoint(mission)
        create_checkpoint(mission, "continue")
        assert resume_step(mission) is None
        clear_checkpoint(mission)


class TestRetry:
    def test_succeeds_after_retries(self):
        calls = {"n": 0}

        def flaky():
            calls["n"] += 1
            if calls["n"] < 3:
                raise TimeoutError("timeout")
            return "ok"

        assert retry(flaky) == "ok"
        assert calls["n"] == 3

    def test_raises_after_max_retries(self):
        def always():
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError):
            retry(always)

    def test_no_retry_needed(self):
        assert retry(lambda: 42) == 42

    def test_backoff_sequence(self):
        assert backoff_for(1) == 1
        assert backoff_for(2) == 2
        assert backoff_for(3) == 4
        assert backoff_for(99) == 4


class TestAge:
    def test_parse_time_failure(self):
        checkpoint = Checkpoint("CHK-1", "MSN-1", "execute", created_at="not-a-date")
        assert checkpoint_age_seconds(checkpoint) == 0

    def test_is_stale_old_date(self):
        checkpoint = Checkpoint("CHK-1", "MSN-1", "execute", created_at="2000-01-01T00:00:00+00:00")
        assert is_stale(checkpoint, max_age_seconds=10)

    def test_not_stale_fresh(self):
        from scripts.builder.core import utcnow

        checkpoint = Checkpoint("CHK-1", "MSN-1", "execute", created_at=utcnow())
        assert not is_stale(checkpoint, max_age_seconds=3600)


class TestFailureAnalysisDataclass:
    def test_defaults(self):
        analysis = FailureAnalysis(mission_id="MSN-1", step="test", classification="transient", retries_left=2, action="retry")
        assert analysis.analyzed_at
