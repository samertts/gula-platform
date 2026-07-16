from __future__ import annotations

import pytest

from app.kernel import Kernel
from app.kernel.plugin.manager import PluginManager
from app.kernel.types import PluginDescriptor


class TestPluginManager:
    def test_init(self, kernel: Kernel):
        pm = PluginManager(kernel)
        assert pm.registry is not None
        assert pm.loader is not None
        assert pm.sandbox is not None
        assert pm.permissions is not None
        assert pm.dependency_resolver is not None
        assert pm.version_manager is not None
        assert pm.marketplace is not None
        assert pm.hot_reloader is not None
