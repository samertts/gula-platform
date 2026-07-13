from __future__ import annotations

import pytest

from backend.app.kernel.plugin.version_manager import PluginVersionManager
from backend.app.kernel.types import PluginDescriptor


class TestPluginVersionManager:
    def test_validate_and_register(self):
        pvm = PluginVersionManager()
        desc = PluginDescriptor(name="p1", version="1.0", path="/tmp", entry_point="Plugin")
        pvm.validate(desc)
        pvm.register(desc)
        assert pvm.get_version("p1") == "1.0"
