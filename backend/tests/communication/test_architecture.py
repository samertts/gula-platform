"""Architecture / contract / dependency tests for the Communication Core.

Enforces the PROGRAM-COMM-001 invariants:

  1. The Core is provider-independent — it never imports a provider module
     or any external HTTP library (dependency test).
  2. Provider contracts — third-party providers implementing the interfaces
     work through the Center without touching it (contract test).
  3. The Core stays stdlib-only (dependency test).
"""

from __future__ import annotations

import ast
from pathlib import Path

from shared.communication.audit import AuditEvent, AuditSink
from shared.communication.model import (
    OutboundMessage,
    ProviderDeliveryResult,
    Recipient,
)
from shared.communication.providers import (
    ChannelProvider,
    ProviderOptions,
    ProviderRegistry,
)
from shared.communication.queue import DeliveryQueue
from shared.communication.state import StateStore

CORE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "shared" / "communication"

FORBIDDEN_TOP_LEVEL_MODULES = {
    "httpx",
    "requests",
    "aiohttp",
    "urllib3",
    "resend",
    "discord",
    "slack",
    "telegram",
    "twilio",
    "firebase_admin",
    "boto3",
}

FORBIDDEN_TOKEN_WORDS = {
    "resend",
    "telegram",
    "discord",
    "slack",
    "teams",
    "whatsapp",
    "twilio",
    "sendgrid",
    "fcm",
    "apns",
}

PROVIDER_PACKAGE_HINTS = ("notifications", "gateways", "platform")


class TestDependencyInvariants:
    def test_core_is_stdlib_only(self):
        for pyfile in CORE_DIR.rglob("*.py"):
            tree = ast.parse(pyfile.read_text(), filename=str(pyfile))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        root = alias.name.split(".")[0]
                        assert root not in FORBIDDEN_TOP_LEVEL_MODULES, (
                            f"{pyfile.name} imports forbidden module: {alias.name}"
                        )
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    root = (node.module or "").split(".")[0]
                    assert root not in FORBIDDEN_TOP_LEVEL_MODULES, (
                        f"{pyfile.name} imports forbidden module: {node.module}"
                    )

    def test_core_never_mentions_providers(self):
        for pyfile in CORE_DIR.rglob("*.py"):
            if pyfile.name == "__init__.py":
                continue
            lower = pyfile.read_text().lower()
            for word in FORBIDDEN_TOKEN_WORDS:
                assert word not in lower, (
                    f"{pyfile.name} contains provider token: {word}"
                )

    def test_core_has_no_relative_imports_outside_package(self):
        for pyfile in CORE_DIR.glob("*.py"):
            tree = ast.parse(pyfile.read_text(), filename=str(pyfile))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.level > 1:
                    raise AssertionError(
                        f"{pyfile.name} escapes the package with relative import depth {node.level}",
                    )


class TestProviderContract:
    """A third-party provider written against the interfaces must work."""

    def test_third_party_provider_delivers(self):
        from shared.communication import CommunicationCenter, Policy

        class OpsProvider(ChannelProvider):
            name = "ops_webhook"
            channel = "webhook"

            def __init__(self) -> None:
                self.received: list[str] = []

            def deliver(
                self,
                recipient: Recipient,
                message: OutboundMessage,
                options: ProviderOptions | None = None,
            ) -> ProviderDeliveryResult:
                self.received.append(message.content)
                return ProviderDeliveryResult(
                    success=True,
                    channel=self.channel,
                    provider=self.name,
                    delivery_ref="wh-1",
                )

        provider = OpsProvider()
        registry = ProviderRegistry()
        registry.register(provider)
        center = CommunicationCenter(providers=registry)
        receipt = center.dispatch(
            "https://ops.example.com/hook",
            content="hello webhook",
            policy=Policy(id="p", required_channels=("webhook",)),
        )
        assert receipt.state == "delivered"
        assert provider.received == ["hello webhook"]

    def test_provider_contract_shape(self):
        """Audit/queue/state interfaces remain structural (protocol-like)."""
        import inspect

        for iface in (AuditSink, DeliveryQueue, StateStore):
            members = [m for m in inspect.getmembers(iface) if not m[0].startswith("_")]
            assert members, f"{iface.__name__} must define members"

    def test_audit_event_serialisable(self):
        event = AuditEvent(action="communication.dispatch.created", delivery_id="d1")
        payload = event.to_dict()
        assert payload["action"] == "communication.dispatch.created"
        assert payload["delivery_id"] == "d1"


class TestPluginContract:
    def test_plugin_extension_without_core_change(self):
        """A new provider registers through the plugin path and the Core
        routes to it without any Core modification."""
        from shared.communication import CommunicationCenter, Policy
        from shared.communication.plugins import PluginManager

        from .fakes import FakePlugin, FakeProvider

        manager = PluginManager()
        manager.register(FakePlugin("sms-gateway", FakeProvider(name="smsgw", channel="sms")))
        manager.activate("sms-gateway")

        center = CommunicationCenter()
        center.providers.register(manager.get_state("sms-gateway").provider)
        receipt = center.dispatch(
            "07701234567",
            content="hello",
            policy=Policy(id="p", required_channels=("sms",)),
        )
        assert receipt.state == "delivered"

    def test_adding_second_provider_same_channel(self):
        """Two providers for one channel — registry keeps both, routing
        prefers the first healthy one; removing one never breaks the other."""
        from shared.communication.providers import ProviderHealth

        from .fakes import FakeProvider

        registry = ProviderRegistry()
        first = FakeProvider(name="first", channel="email", health=ProviderHealth.DOWN)
        second = FakeProvider(name="second", channel="email")
        registry.register(first)
        registry.register(second)
        assert len(registry.providers_for("email")) == 2
        assert registry.unregister("first") is True
        assert len(registry.providers_for("email")) == 1
        assert registry.get("second") is second


class TestPackageShape:
    def test_public_exports_complete(self):
        import shared.communication as comm

        for name in (
            "CommunicationCenter",
            "ChannelProvider",
            "ProviderPlugin",
            "PluginManager",
            "PolicyEngine",
            "Policy",
            "TemplateEngine",
            "DeliveryStateMachine",
            "StateStore",
            "DeliveryQueue",
            "AuditSink",
            "EventBridge",
            "EventPolicyRegistry",
            "build_communication_center",
        ):
            assert hasattr(comm, name), f"missing public export: {name}"

    def test_public_api_has_no_provider_names(self):
        import shared.communication as comm

        lower = str(sorted(comm.__all__)).lower()
        for word in FORBIDDEN_TOKEN_WORDS:
            assert word not in lower, f"public API leaks provider token: {word}"
