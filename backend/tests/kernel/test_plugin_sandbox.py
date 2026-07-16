from __future__ import annotations

import pytest

from app.kernel.plugin.sandbox import PluginSandbox


class TestPluginSandbox:
    def test_allowed_modules(self):
        sandbox = PluginSandbox()
        assert sandbox.is_module_allowed("json")
        assert sandbox.is_module_allowed("logging")
        assert not sandbox.is_module_allowed("os")
        assert not sandbox.is_module_allowed("subprocess")
        assert not sandbox.is_module_allowed("socket")
