from __future__ import annotations

import json
import os
import tempfile

import pytest

from backend.app.kernel.module.compatibility import ModuleVersionCompatibility
from backend.app.kernel.module.discovery import ModuleDiscovery
from backend.app.kernel.module.metadata import ModuleMetadataParser
from backend.app.kernel.module.registry import ModuleRegistry
from backend.app.kernel.module.resolver import ModuleDependencyResolver
from backend.app.kernel.types import ModuleDescriptor


class TestModuleRegistry:
    def test_register_and_unregister(self):
        mr = ModuleRegistry()
        desc = ModuleDescriptor(name="m1", version="1.0", path="/tmp")
        mr.register(desc)
        assert mr.has("m1")
        assert mr.get("m1") is not None
        mr.unregister("m1")
        assert not mr.has("m1")


class TestModuleDependencyResolver:
    def test_resolve_order(self):
        resolver = ModuleDependencyResolver()
        m1 = ModuleDescriptor(name="base", version="1.0", path="/tmp")
        m2 = ModuleDescriptor(name="extended", version="1.0", path="/tmp", dependencies={"base": "1.0"})
        ordered = resolver.resolve_order([m2, m1])
        assert ordered[0].name == "base"
        assert ordered[1].name == "extended"

    def test_circular_dependency(self):
        resolver = ModuleDependencyResolver()
        m1 = ModuleDescriptor(name="a", version="1.0", path="/tmp", dependencies={"b": "1.0"})
        m2 = ModuleDescriptor(name="b", version="1.0", path="/tmp", dependencies={"a": "1.0"})
        with pytest.raises(ValueError, match="Circular dependency"):
            resolver.resolve_order([m1, m2])


class TestModuleVersionCompatibility:
    def test_compatible_versions(self):
        mvc = ModuleVersionCompatibility()
        assert mvc.is_compatible("1.0.0", "1.0.0")
        assert mvc.is_compatible("1.0.0", "1.0.1")
        assert not mvc.is_compatible("1.0.0", "0.9.0")
        assert not mvc.is_compatible("2.0.0", "1.9.9")


class TestModuleMetadata:
    def test_parse(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mod_dir = os.path.join(tmpdir, "test_mod")
            os.makedirs(mod_dir)
            with open(os.path.join(mod_dir, "module.json"), "w") as f:
                json.dump({"name": "test_mod", "version": "3.0.0", "dependencies": {"base": "1.0"}}, f)
            parser = ModuleMetadataParser()
            desc = parser.parse(mod_dir)
            assert desc.name == "test_mod"
            assert desc.version == "3.0.0"
            assert "base" in desc.dependencies


class TestModuleDiscovery:
    def test_discover(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            discovery = ModuleDiscovery()
            discovery.add_search_path(tmpdir)
            mod_dir = os.path.join(tmpdir, "found_module")
            os.makedirs(mod_dir)
            with open(os.path.join(mod_dir, "module.json"), "w") as f:
                json.dump({"name": "found_module"}, f)
            discovered = discovery.discover()
            assert len(discovered) == 1

    def test_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            discovery = ModuleDiscovery()
            discovery.add_search_path(tmpdir)
            discovered = discovery.discover()
            assert len(discovered) == 0


class TestModuleDescriptorDefaults:
    def test_defaults(self):
        desc = ModuleDescriptor(name="test", version="1.0", path="/tmp")
        assert desc.enabled
        assert desc.dependencies == {}
        assert desc.entry_points == []
