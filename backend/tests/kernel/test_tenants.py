from __future__ import annotations

import pytest
from app.kernel.tenant.config import TenantConfiguration
from app.kernel.tenant.isolation import TenantIsolation
from app.kernel.tenant.quotas import TenantQuotaManager
from app.kernel.tenant.registry import TenantRegistry
from app.kernel.tenant.resolver import TenantResolver
from app.kernel.types import TenantDescriptor


class TestTenantRegistry:
    def test_register_and_get(self):
        tr = TenantRegistry()
        desc = TenantDescriptor(
            id="tenant_1",
            name="Test Lab",
            slug="test-lab",
            plan="professional",
        )
        tr.register(desc)
        assert tr.has("tenant_1")
        assert tr.get("tenant_1") is not None

    def test_list(self):
        tr = TenantRegistry()
        tr.register(TenantDescriptor(id="t1", name="T1", slug="t1"))
        tr.register(TenantDescriptor(id="t2", name="T2", slug="t2"))
        assert len(tr.list_tenants()) == 2


class TestTenantResolver:
    def test_resolve_by_slug_and_id(self):
        tr = TenantRegistry()
        desc = TenantDescriptor(id="t1", name="Lab 1", slug="lab-1")
        tr.register(desc)
        assert tr.resolver.resolve_by_slug("lab-1") == "t1"
        assert tr.resolver.resolve_by_id("t1") == "t1"
        assert tr.resolver.resolve_by_slug("nonexistent") is None
        assert tr.resolver.resolve_by_id("nonexistent") is None


class TestTenantIsolation:
    def test_isolate_deisolate(self):
        ti = TenantIsolation()
        ti.isolate("t1")
        assert ti.is_isolated("t1")
        ti.deisolate("t1")
        assert not ti.is_isolated("t1")


class TestTenantQuotas:
    def test_check_quota(self):
        tqm = TenantQuotaManager()
        tqm.set_quota("tenant_1", "patients", 100)
        assert tqm.check_quota("tenant_1", "patients")
        for _ in range(100):
            tqm.increment_usage("tenant_1", "patients")
        assert not tqm.check_quota("tenant_1", "patients")

    def test_no_limit(self):
        tqm = TenantQuotaManager()
        assert tqm.check_quota("t1", "unlimited_resource")

    def test_get_quota(self):
        tqm = TenantQuotaManager()
        tqm.set_quota("t1", "storage", 100)
        assert tqm.get_quota("t1", "storage") == 100
        assert tqm.get_quota("t1", "nonexistent") == 0


class TestTenantConfiguration:
    def test_set_and_get(self):
        tc = TenantConfiguration()
        tc.set("t1", "theme", "dark")
        assert tc.get("t1", "theme") == "dark"
        assert tc.get("t1", "nonexistent", "default") == "default"

    def test_get_all(self):
        tc = TenantConfiguration()
        tc.set("t1", "theme", "dark")
        tc.set("t1", "locale", "ar")
        config = tc.get_all("t1")
        assert config["theme"] == "dark"
        assert config["locale"] == "ar"
        assert tc.get_all("nonexistent") == {}

    def test_descriptor_defaults(self):
        desc = TenantDescriptor(id="t1", name="Test", slug="test")
        assert desc.plan == "free"
        assert desc.active
        assert desc.features == {}
        assert desc.quotas == {}
        assert desc.config == {}
