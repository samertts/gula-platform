from __future__ import annotations

import pytest

from app.kernel.plugin.dependencies import PluginDependencyResolver
from app.kernel.plugin.registry import PluginRegistry
from app.kernel.types import PluginDescriptor


class TestPluginRegistry:
    def test_register_and_unregister(self):
        pr = PluginRegistry()
        desc = PluginDescriptor(name="p1", version="1.0", path="/tmp", entry_point="Plugin")
        pr.register(desc)
        assert pr.has("p1")
        assert pr.get("p1") is not None
        pr.unregister("p1")
        assert not pr.has("p1")


class TestPluginDependencyResolver:
    def test_resolve_order(self):
        resolver = PluginDependencyResolver()
        p1 = PluginDescriptor(name="core", version="1.0", path="/tmp", entry_point="Plugin")
        p2 = PluginDescriptor(name="ext", version="1.0", path="/tmp", entry_point="Plugin", dependencies=["core"])
        ordered = resolver.resolve_order([p2, p1])
        assert ordered[0].name == "core"
        assert ordered[1].name == "ext"

    def test_circular_dependency(self):
        resolver = PluginDependencyResolver()
        p1 = PluginDescriptor(name="a", version="1.0", path="/tmp", entry_point="Plugin", dependencies=["b"])
        p2 = PluginDescriptor(name="b", version="1.0", path="/tmp", entry_point="Plugin", dependencies=["a"])
        with pytest.raises(ValueError, match="Circular dependency"):
            resolver.resolve_order([p1, p2])


class TestPluginDescriptorDefaults:
    def test_defaults(self):
        desc = PluginDescriptor(name="test", version="1.0", path="/tmp", entry_point="Plugin")
        assert desc.enabled
        assert desc.dependencies == []
        assert desc.permissions == []
