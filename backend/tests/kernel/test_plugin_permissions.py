from __future__ import annotations

import pytest
from app.kernel.plugin.permissions import PluginPermissionManager
from app.kernel.types import PluginDescriptor


class TestPluginPermissions:
    def test_check_and_has_permission(self):
        ppm = PluginPermissionManager()
        desc = PluginDescriptor(
            name="test_plugin",
            version="1.0",
            path="/tmp",
            entry_point="Plugin",
            permissions=["config.read", "event.publish"],
        )
        ppm.check(desc)
        assert ppm.has_permission("test_plugin", "config.read")
        assert ppm.has_permission("test_plugin", "event.publish")
        assert not ppm.has_permission("test_plugin", "db.write")
