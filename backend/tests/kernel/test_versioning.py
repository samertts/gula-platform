from __future__ import annotations

import pytest
from app.kernel.config.versioned import ConfigVersion, VersionedConfiguration
from app.kernel.event_bus.events import Event
from app.kernel.event_bus.versioning import EventVersioning


class TestEventVersioning:
    def test_register_and_get_schema(self):
        ev = EventVersioning()
        ev.register_schema("test.event", 1, {"type": "object"})
        schema = ev.get_schema("test.event", 1)
        assert schema is not None

    def test_migrate(self):
        ev = EventVersioning()
        event = Event(name="test", data={"k": "v"}, version=1)
        migrated = ev.migrate(event, 2)
        assert migrated.version == 2
        assert migrated.data == {"k": "v"}


class TestConfigVersioning:
    def test_snapshot_and_retrieve(self):
        vc = VersionedConfiguration()
        v1 = vc.snapshot({"key": "value1"}, "first")
        v2 = vc.snapshot({"key": "value2"}, "second")
        assert v1 == 1
        assert v2 == 2
        assert vc.get_version(1).config["key"] == "value1"
        assert vc.get_version(2).config["key"] == "value2"

    def test_config_version_defaults(self):
        cv = ConfigVersion(version=1, config={"k": "v"})
        assert cv.created_at > 0
        assert cv.comment == ""
