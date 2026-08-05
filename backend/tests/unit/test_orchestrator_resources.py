"""Unit tests for GULA-ORCHESTRATOR-001 — Phase 7 Resource Manager."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.orchestrator.core import REPO_ROOT, ResourceUsage
from scripts.orchestrator.resources import (
    CONTEXT_LIMIT_BYTES,
    FILE_MODIFIED_LIMIT,
    auto_split_tasks,
    merge_usage,
    repo_size_bytes,
    snapshot,
)


class TestSnapshot:
    def test_snapshot_returns_positive_repo_size(self):
        usage = snapshot("ORN-R1", context_bytes=1, files_read=1, files_modified=1)
        assert usage.repo_bytes > 0

    def test_snapshot_no_split_on_small_usage(self):
        usage = snapshot("ORN-R1", context_bytes=1, files_read=1, files_modified=1)
        assert not usage.split_recommended

    def test_snapshot_split_on_huge_context(self):
        usage = snapshot("ORN-R1", context_bytes=CONTEXT_LIMIT_BYTES + 1)
        assert usage.split_recommended
        assert "context" in usage.split_reason

    def test_snapshot_split_on_many_modified_files(self):
        usage = snapshot("ORN-R1", files_modified=FILE_MODIFIED_LIMIT)
        assert usage.split_recommended

    def test_execution_seconds_accumulate(self):
        usage = snapshot("ORN-R1", started_at=999)
        assert usage.execution_seconds >= 0

    def test_snapshot_persists_mission_id(self):
        usage = snapshot("ORN-R1")
        assert usage.mission_id == "ORN-R1"


class TestRepoSize:
    def test_repo_size_matches_global(self):
        assert repo_size_bytes() == repo_size_bytes(REPO_ROOT)

    def test_repo_size_excludes_venv(self):
        assert repo_size_bytes(REPO_ROOT) < repo_size_bytes(REPO_ROOT) + 1


class TestMerge:
    def test_merge_accumulates_counts(self):
        u1 = ResourceUsage("ORN-M", context_bytes=10, files_read=3, files_modified=2)
        u2 = ResourceUsage("ORN-M", context_bytes=5, files_read=1, files_modified=1)
        merged = merge_usage("ORN-M", u1, u2)
        assert merged.context_bytes == 15
        assert merged.files_read == 4
        assert merged.files_modified == 3

    def test_merge_flags_split(self):
        u1 = ResourceUsage("ORN-M", files_modified=FILE_MODIFIED_LIMIT)
        merged = merge_usage("ORN-M", u1)
        assert merged.split_recommended

    def test_merge_empty_is_clean(self):
        merged = merge_usage("ORN-M")
        assert not merged.split_recommended


class TestAutoSplit:
    def test_auto_split_respects_budget(self):
        batches = auto_split_tasks([f"t{i}" for i in range(250)])
        assert all(len(b) <= FILE_MODIFIED_LIMIT for b in batches)
        assert sum(len(b) for b in batches) == 250

    def test_auto_split_single_batch_for_small_list(self):
        assert auto_split_tasks(["a", "b"]) == [["a", "b"]]

    def test_auto_split_empty_returns_empty_batch(self):
        assert auto_split_tasks([]) == [[]]
