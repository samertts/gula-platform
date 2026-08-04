"""Plugin system tests: registration, lifecycle, capability negotiation,
discovery, and Core isolation from provider implementations."""

from __future__ import annotations

from shared.communication import CommunicationCenter, Policy
from shared.communication.plugins import (
    ENTRY_POINT_GROUP,
    PluginManager,
)
from shared.communication.providers import (
    ChannelCapability,
    ProviderHealth,
    ProviderRegistry,
)

from .fakes import FakePlugin, FakeProvider, RichFakeProvider


class TestPluginLifecycle:
    def test_register_creates_provider(self):
        manager = PluginManager()
        plugin = FakePlugin("p1", FakeProvider(name="f1", channel="email"))
        state = manager.register(plugin)
        assert state.provider.name == "f1"
        assert state.active is False

    def test_duplicate_plugin_rejected(self):
        manager = PluginManager()
        manager.register(FakePlugin("p1", FakeProvider(name="f1", channel="email")))
        try:
            manager.register(FakePlugin("p1", FakeProvider(name="f2", channel="sms")))
        except ValueError:
            return
        raise AssertionError("duplicate plugin id must raise")

    def test_non_plugin_rejected(self):
        manager = PluginManager()
        try:
            manager.register("not-a-plugin")  # type: ignore[arg-type]
        except TypeError:
            return
        raise AssertionError("non-plugin registration must raise")

    def test_activate_runs_hook_and_flags_active(self):
        manager = PluginManager()
        plugin = FakePlugin("p1", FakeProvider(name="f1", channel="email"))
        manager.register(plugin)
        assert manager.activate("p1") is True
        assert plugin.activation_count == 1
        assert manager.get_state("p1").active is True

    def test_activate_is_idempotent(self):
        manager = PluginManager()
        plugin = FakePlugin("p1", FakeProvider(name="f1", channel="email"))
        manager.register(plugin)
        manager.activate("p1")
        manager.activate("p1")
        assert plugin.activation_count == 1

    def test_activation_failure_recorded(self):
        manager = PluginManager()
        plugin = FakePlugin("p1", FakeProvider(name="f1", channel="email"), fail_activation=True)
        manager.register(plugin)
        assert manager.activate("p1") is False
        state = manager.get_state("p1")
        assert state.active is False
        assert "activation boom" in (state.activation_error or "")

    def test_deactivate_runs_hook(self):
        manager = PluginManager()
        plugin = FakePlugin("p1", FakeProvider(name="f1", channel="email"))
        manager.register(plugin)
        manager.activate("p1")
        assert manager.deactivate("p1") is True
        assert plugin.deactivation_count == 1
        assert manager.get_state("p1").active is False

    def test_unknown_plugin_activation_raises(self):
        manager = PluginManager()
        try:
            manager.activate("ghost")
        except KeyError:
            return
        raise AssertionError("unknown plugin activation must raise")

    def test_providers_only_active(self):
        manager = PluginManager()
        manager.register(FakePlugin("p1", FakeProvider(name="f1", channel="email")))
        manager.register(FakePlugin("p2", FakeProvider(name="f2", channel="sms")))
        manager.activate("p1")
        assert {p.name for p in manager.providers()} == {"f1"}
        assert manager.provider_count() == 1


class TestCapabilityNegotiation:
    def test_registry_detects_capabilities(self):
        registry = ProviderRegistry()
        registry.register(FakeProvider(name="plain", channel="email"))
        registry.register(RichFakeProvider(name="rich", channel="telegram"))
        assert registry.supports(registry.get("rich"), ChannelCapability.RICH_TEXT) is True
        assert registry.supports(registry.get("plain"), ChannelCapability.RICH_TEXT) is False
        assert registry.supports(registry.get("plain"), ChannelCapability.TEXT) is True

    def test_describe_reports_capabilities_and_health(self):
        registry = ProviderRegistry()
        registry.register(RichFakeProvider(name="rich", channel="telegram"))
        registry.register(
            FakeProvider(name="down", channel="email", health=ProviderHealth.DOWN),
        )
        description = registry.describe()
        by_name = {d["name"]: d for d in description}
        assert "rich_text" in by_name["rich"]["capabilities"]
        assert by_name["down"]["health"] == "down"


class TestPluginDrivenDelivery:
    def test_plugin_registration_enables_delivery(self):
        manager = PluginManager()
        manager.register(FakePlugin("p1", FakeProvider(name="f1", channel="email")))
        manager.activate("p1")

        center = CommunicationCenter()
        provider = manager.get_state("p1").provider
        center.providers.register(provider)
        receipt = center.dispatch(
            "a@b.c",
            content="via plugin",
            policy=Policy(id="p", required_channels=("email",)),
        )
        assert receipt.state == "delivered"


class TestDiscovery:
    def test_entry_point_group_constant(self):
        assert ENTRY_POINT_GROUP == "gula.communication.providers"

    def test_discover_with_no_entry_points(self):
        manager = PluginManager()
        found = manager.discover(entry_point_group="gula.communication.does-not-exist")
        assert found == []
