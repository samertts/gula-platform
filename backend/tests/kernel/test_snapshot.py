from __future__ import annotations

import pytest
from app.kernel.event_bus.events import Event
from app.kernel.event_bus.snapshot import Snapshot, SnapshotEngine


class TestSnapshotEngine:
    def test_save_and_load_latest(self):
        engine = SnapshotEngine()
        snap = Snapshot(aggregate_type="order", aggregate_id="ord-1", state={"status": "pending"})
        engine.save(snap)
        loaded = engine.load_latest("order", "ord-1")
        assert loaded is not None
        assert loaded.state["status"] == "pending"

    def test_load_at_version(self):
        engine = SnapshotEngine()
        snap1 = Snapshot(aggregate_type="order", aggregate_id="ord-1", state={"v": 1}, version=1)
        snap2 = Snapshot(aggregate_type="order", aggregate_id="ord-1", state={"v": 2}, version=2)
        engine.save(snap1)
        engine.save(snap2)
        assert engine.load_at_version("order", "ord-1", 1).state["v"] == 1
        assert engine.load_at_version("order", "ord-1", 2).state["v"] == 2

    def test_rebuild_from_events(self):
        engine = SnapshotEngine()
        events = [
            Event(name="item.added", data={"item": "test"}),
            Event(name="item.updated", data={"item": "updated"}),
        ]

        def apply_fn(state, event):
            s = dict(state)
            s.update(event.data)
            return s

        snap = engine.rebuild_from_events("cart", "cart-1", events, apply_fn, {"initial": True})
        assert snap.state["initial"] is True
        assert snap.state["item"] == "updated"
        assert snap.last_event_name == "item.updated"

    def test_list_versions(self):
        engine = SnapshotEngine()
        engine.save(Snapshot(aggregate_type="a", aggregate_id="1", version=1))
        engine.save(Snapshot(aggregate_type="a", aggregate_id="1", version=2))
        versions = engine.list_versions("a", "1")
        assert len(versions) == 2

    def test_purge(self):
        engine = SnapshotEngine()
        engine.save(Snapshot(aggregate_type="a", aggregate_id="1"))
        assert engine.count() == 1
        engine.purge("a", "1")
        assert engine.count() == 0
