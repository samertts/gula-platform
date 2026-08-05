"""Unit tests for GULA-KERNEL-EXT-001 Phase 5 — Enterprise Event Bus."""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.kernel.ext.event_bus import (
    EVENT_KINDS,
    EVENT_PRIORITIES,
    Delivery,
    Event,
    EventBus,
    EventBusError,
)


def _event(**overrides) -> Event:
    base = {
        "id": "EVT-100001",
        "name": "migration.executed",
        "publisher": "test",
        "payload": {"plan": "MIGR-000001"},
    }
    base.update(overrides)
    return Event(**base)


class TestEvent:
    def test_valid_event(self):
        event = _event()
        assert event.kind == "system"
        assert event.priority == "normal"

    def test_bad_id(self):
        with pytest.raises(EventBusError):
            _event(id="BAD-1")

    def test_empty_name(self):
        with pytest.raises(EventBusError):
            _event(name="")

    def test_bad_kind(self):
        with pytest.raises(EventBusError):
            _event(kind="nope")

    def test_bad_priority(self):
        with pytest.raises(EventBusError):
            _event(priority="urgent")

    def test_kinds_and_priorities_valid(self):
        for kind in EVENT_KINDS:
            for priority in EVENT_PRIORITIES:
                event = _event(kind=kind, priority=priority)
                assert event.kind == kind
                assert event.priority == priority

    def test_to_dict(self):
        data = _event().to_dict()
        assert data["id"] == "EVT-100001"
        assert "emitted_at" in data


class TestBus:
    def test_subscribe_and_publish(self):
        bus = EventBus()
        seen: list[str] = []
        bus.subscribe("migration.executed", "governor", lambda ev: seen.append(ev["name"]))
        bus.publish(_event())
        assert seen == ["migration.executed"]

    def test_wildcard_subscriber(self):
        bus = EventBus()
        seen: list[str] = []
        bus.subscribe("*", "audit", lambda ev: seen.append(ev["id"]))
        bus.publish(_event(id="EVT-100001"))
        bus.publish(_event(id="EVT-100002"))
        assert len(seen) == 2

    def test_non_matching_handler_skipped(self):
        bus = EventBus()
        seen: list[str] = []
        bus.subscribe("other.event", "governor", lambda ev: seen.append(ev["name"]))
        bus.publish(_event())
        assert seen == []

    def test_deliveries_recorded(self):
        bus = EventBus()
        bus.subscribe("migration.executed", "governor", lambda _ev: None)
        deliveries = bus.publish(_event())
        assert len(deliveries) == 1
        assert deliveries[0].status == "delivered"
        assert len(bus.deliveries()) == 1

    def test_idempotent_delivery(self):
        bus = EventBus()
        seen: list[str] = []
        bus.subscribe("migration.executed", "governor", lambda ev: seen.append(ev["id"]))
        event = _event()
        bus.publish(event)
        bus.publish(event)
        assert len(seen) == 1

    def test_failed_handler_recorded_and_others_run(self):
        bus = EventBus()

        def boom(_ev: dict) -> None:
            raise RuntimeError("handler failed")

        seen: list[str] = []
        bus.subscribe("migration.executed", "bad", boom)
        bus.subscribe("migration.executed", "good", lambda ev: seen.append(ev["id"]))
        bus.publish(_event())
        assert seen == ["EVT-100001"]
        assert len(bus.failures()) == 1
        assert bus.failures()[0].handler == "bad"

    def test_replay_redelivers(self):
        bus = EventBus()
        seen: list[str] = []
        bus.subscribe("migration.executed", "governor", lambda ev: seen.append(ev["id"]))
        bus.publish(_event())
        bus.replay()
        assert len(seen) == 2

    def test_replay_filter_by_name(self):
        bus = EventBus()
        seen: list[str] = []
        bus.subscribe("*", "audit", lambda ev: seen.append(ev["name"]))
        bus.publish(_event(id="EVT-100001", name="a.b"))
        bus.publish(_event(id="EVT-100002", name="x.y"))
        bus.replay(name="a.b")
        assert seen.count("a.b") == 2
        assert seen.count("x.y") == 1

    def test_events_filter(self):
        bus = EventBus()
        bus.publish(_event(id="EVT-100001", name="a"))
        bus.publish(_event(id="EVT-100002", name="b"))
        assert len(bus.events(name="a")) == 1
        assert len(bus.events()) == 2

    def test_deliveries_filter(self):
        bus = EventBus()
        bus.subscribe("*", "audit", lambda _ev: None)
        bus.publish(_event(id="EVT-100001"))
        bus.publish(_event(id="EVT-100002"))
        assert len(bus.deliveries("EVT-100001")) == 1

    def test_snapshot_and_save(self, tmp_path):
        bus = EventBus()
        bus.subscribe("migration.executed", "governor", lambda _ev: None)
        bus.publish(_event())
        path = bus.save(tmp_path / "events.json")
        data = path.read_text(encoding="utf-8")
        assert "EVT-100001" in data
        assert "delivered" in data
