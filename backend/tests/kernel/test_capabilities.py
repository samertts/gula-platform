from __future__ import annotations

import pytest
from app.kernel.runtime.capability_registry import CapabilityRegistry
from app.kernel.types import CapabilityDescriptor


class TestCapabilityRegistry:
    def test_list_and_enable(self):
        cr = CapabilityRegistry()
        cr.register(CapabilityDescriptor(name="a", version="1.0", description="a"))
        cr.register(CapabilityDescriptor(name="b", version="1.0", description="b"))
        assert len(cr.list_capabilities()) == 2
        assert len(cr.list_enabled()) == 2
        cr.disable("a")
        assert len(cr.list_enabled()) == 1

    def test_check_dependencies(self):
        cr = CapabilityRegistry()
        cr.register(CapabilityDescriptor(name="base", version="1.0", description="base"))
        cr.register(
            CapabilityDescriptor(
                name="ext", version="1.0", description="ext", dependencies=["base"]
            )
        )
        assert cr.check_dependencies("ext")
        assert not cr.check_dependencies("nonexistent")

    def test_not_found(self):
        cr = CapabilityRegistry()
        assert cr.get("nonexistent") is None
        assert not cr.has("nonexistent")
        assert not cr.is_enabled("nonexistent")
