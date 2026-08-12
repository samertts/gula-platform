from __future__ import annotations

import pytest

from app.kernel.features.capabilities import CapabilityFlagManager
from app.kernel.features.experimental import ExperimentalFeatureManager
from app.kernel.features.flags import FeatureFlag, FeatureFlagManager
from app.kernel.features.kill_switch import EmergencyKillSwitch
from app.kernel.features.regional import RegionalFeatureManager
from app.kernel.features.tenant_features import TenantFeatureManager


class TestFeatureFlags:
    def test_enable_disable(self):
        ffm = FeatureFlagManager()
        flag = FeatureFlag(name="test_feature", enabled=True)
        ffm.register(flag)
        assert ffm.is_enabled("test_feature")
        ffm.disable("test_feature")
        assert not ffm.is_enabled("test_feature")

    def test_dependency_cascading(self):
        ffm = FeatureFlagManager()
        parent = FeatureFlag(name="parent", enabled=True)
        child = FeatureFlag(name="child", enabled=True, dependencies=["parent"])
        ffm.register(parent)
        ffm.register(child)
        assert ffm.is_enabled("child")
        ffm.disable("parent")
        assert not ffm.is_enabled("child")


class TestEmergencyKillSwitch:
    def test_activate_deactivate(self):
        ks = EmergencyKillSwitch()
        assert not ks.is_active
        ks.activate("test emergency")
        assert ks.is_active
        assert ks.reason == "test emergency"
        ks.deactivate()
        assert not ks.is_active


class TestRegionalFeatures:
    def test_region_enabled(self):
        rfm = RegionalFeatureManager()
        rfm.register("IQ", ["national_id", "ehr"])
        assert rfm.is_enabled_in_region("IQ", "national_id")
        assert not rfm.is_enabled_in_region("US", "national_id")


class TestTenantFeatures:
    def test_per_tenant_enable(self):
        tfm = TenantFeatureManager()
        tfm.set_feature("t1", "premium_analytics", True)
        assert tfm.is_enabled("t1", "premium_analytics")
        assert not tfm.is_enabled("t2", "premium_analytics")


class TestExperimentalFeatures:
    def test_enable_disable(self):
        efm = ExperimentalFeatureManager()
        efm.register("ai_insights", enabled=False)
        assert not efm.is_enabled("ai_insights")
        efm.enable("ai_insights")
        assert efm.is_enabled("ai_insights")


class TestCapabilityFlags:
    def test_enable_disable(self):
        cfm = CapabilityFlagManager()
        cfm.register("export_pdf", enabled=True)
        assert cfm.is_enabled("export_pdf")
        cfm.disable("export_pdf")
        assert not cfm.is_enabled("export_pdf")
