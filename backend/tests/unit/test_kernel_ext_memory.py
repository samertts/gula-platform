"""Unit tests for GULA-KERNEL-EXT-001 Phase 9 — Enterprise AI Memory."""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.kernel.ext.memory import (
    ARCHIVE_ACCESS_THRESHOLD,
    PROMOTION_ACCESSES,
    TIERS,
    MemoryEntry,
    MemoryError,
    MemoryStore,
)


class TestEntry:
    def test_valid_entry(self):
        entry = MemoryEntry("MEM-100001", "working", "content")
        assert entry.access_count == 0
        assert not entry.archived

    def test_bad_id(self):
        with pytest.raises(MemoryError):
            MemoryEntry("BAD-1", "working", "content")

    def test_bad_tier(self):
        with pytest.raises(MemoryError):
            MemoryEntry("MEM-100001", "nope", "content")

    def test_empty_content(self):
        with pytest.raises(MemoryError):
            MemoryEntry("MEM-100001", "working", "   ")

    def test_negative_access_count(self):
        with pytest.raises(MemoryError):
            MemoryEntry("MEM-100001", "working", "content", access_count=-1)

    def test_all_tiers_valid(self):
        for tier in TIERS:
            assert MemoryEntry("MEM-100001", tier, "content").tier == tier


class TestStore:
    def test_remember_generates_id(self):
        store = MemoryStore()
        entry = store.remember("working", "hello")
        assert entry.id.startswith("MEM-")
        assert len(store.entries()) == 1

    def test_remember_tier_scoping(self):
        store = MemoryStore()
        store.remember("working", "w")
        store.remember("failure", "f")
        assert len(store.entries("working")) == 1
        assert len(store.entries("failure")) == 1
        assert len(store.entries()) == 2

    def test_recall_content_match(self):
        store = MemoryStore()
        store.remember("working", "the outbox publishes events", tags=["event"])
        store.remember("working", "use redis cache", tags=["cache"])
        assert len(store.recall("outbox")) == 1
        assert len(store.recall("cache")) == 1

    def test_recall_tag_match(self):
        store = MemoryStore()
        store.remember("working", "topic A", tags=["astm"])
        store.remember("working", "topic B", tags=["hl7"])
        assert len(store.recall("astm")) == 1

    def test_recall_tier_filter(self):
        store = MemoryStore()
        store.remember("working", "outbox note", tags=[])
        store.remember("failure", "outbox timeout", tags=[])
        assert len(store.recall("outbox")) == 2
        assert len(store.recall("outbox", tier="failure")) == 1

    def test_recall_excludes_archived(self):
        store = MemoryStore()
        entry = store.remember("working", "outbox note", tags=[])
        store.archive(entry.id)
        assert store.recall("outbox") == []

    def test_recall_top_k(self):
        store = MemoryStore()
        for i in range(6):
            store.remember("working", f"cache strategy {i}", tags=[])
        assert len(store.recall("cache", top_k=3)) == 3

    def test_touch_increments(self):
        store = MemoryStore()
        entry = store.remember("working", "x")
        store.touch(entry.id)
        assert entry.access_count == 1
        assert entry.last_accessed_at

    def test_touch_unknown(self):
        store = MemoryStore()
        with pytest.raises(MemoryError):
            store.touch("MEM-000000")

    def test_promote(self):
        store = MemoryStore()
        entry = store.remember("working", "x")
        for _ in range(PROMOTION_ACCESSES):
            store.touch(entry.id)
        store.promote(entry.id)
        assert entry.tier == "long_term"

    def test_promote_non_working(self):
        store = MemoryStore()
        entry = store.remember("failure", "x")
        with pytest.raises(MemoryError):
            store.promote(entry.id)

    def test_promote_too_soon(self):
        store = MemoryStore()
        entry = store.remember("working", "x")
        store.touch(entry.id)
        with pytest.raises(MemoryError):
            store.promote(entry.id)

    def test_archive_and_double_archive(self):
        store = MemoryStore()
        entry = store.remember("working", "x")
        store.archive(entry.id)
        assert entry.archived
        with pytest.raises(MemoryError):
            store.archive(entry.id)

    def test_archive_unaccessed(self):
        store = MemoryStore()
        store.remember("working", "never touched")
        touched = store.remember("working", "touched")
        store.touch(touched.id)
        archived = store.archive_unaccessed()
        assert archived == 1
        assert store.entries("working")[0].archived
        assert not store.entries("working")[1].archived

    def test_archive_threshold_constant(self):
        assert ARCHIVE_ACCESS_THRESHOLD == 0

    def test_history_recorded(self):
        store = MemoryStore()
        entry = store.remember("working", "x")
        store.touch(entry.id)
        events = [h["event"] for h in store.snapshot()["history"]]
        assert "remembered" in events and "accessed" in events

    def test_snapshot_and_save(self, tmp_path):
        store = MemoryStore()
        store.remember("working", "x")
        path = store.save(tmp_path / "memory.json")
        data = path.read_text(encoding="utf-8")
        assert "working" in data
        assert "MEM-" in data
