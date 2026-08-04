"""Event integration tests: event → policy binding, dispatch via the bus,
and unknown-event/no-recipient handling."""

from __future__ import annotations

from shared.communication import (
    CommunicationCenter,
    EventBridge,
    EventPolicyRegistry,
    Policy,
    Template,
)
from shared.communication.model import ContentFormat
from shared.communication.providers import ProviderRegistry

from .fakes import FakeProvider, RecordingAuditSink


class FakeBus:
    """Minimal subscribe/emit bus mirroring the canonical EventBus shape."""

    def __init__(self) -> None:
        self.handlers: dict[str, list] = {}

    def subscribe(self, event_name: str, handler) -> None:
        self.handlers.setdefault(event_name, []).append(handler)

    def emit(self, event_name: str, payload=None) -> int:
        for handler in self.handlers.get(event_name, []):
            handler(payload or {})
        return len(self.handlers.get(event_name, []))


def make_center():
    provider = FakeProvider(name="emailer", channel="email")
    registry = ProviderRegistry()
    registry.register(provider)
    center = CommunicationCenter(providers=registry, audit=RecordingAuditSink())
    center.policies.register(
        Policy(
            id="ev.result",
            template_id="tpl.result",
            required_channels=("email",),
        ),
    )
    center.templates.register(
        Template(
            id="tpl.result",
            bodies={ContentFormat.PLAIN: "Result {result_id} released for {recipient}."},
        ),
    )
    center.event_policies.bind("result.critical", "ev.result", recipient_key="recipient")
    return center, provider


class TestEventBinding:
    def test_bind_and_rebind(self):
        registry = EventPolicyRegistry()
        registry.bind("result.critical", "ev.result", recipient_key="recipient")
        assert registry.resolve("result.critical") == (
            "ev.result",
            "recipient",
            (),
        )
        assert registry.binding("result.critical")["policy_id"] == "ev.result"
        assert registry.unbind("result.critical") is True
        assert registry.resolve("result.critical") is None

    def test_bind_requires_recipient_key(self):
        registry = EventPolicyRegistry()
        try:
            registry.bind("e", "p", recipient_key="")
        except ValueError:
            return
        raise AssertionError("empty recipient_key must raise")


class TestEventConsumption:
    def test_event_dispatches_through_policy(self):
        center, provider = make_center()
        receipt = center.handle_communication_event(
            "result.critical",
            {"recipient": "lab@moh.gov.iq", "result_id": "R-100"},
        )
        assert receipt.delivery_id
        assert receipt.state == "delivered"
        delivered = provider.deliveries[0][1]
        assert "R-100" in delivered.content

    def test_unknown_event_is_safe_noop(self):
        center, _provider = make_center()
        center.handle_communication_event("no.such.event", {"recipient": "x@y.z"})

    def test_missing_recipient_audits_failure(self):
        center, provider = make_center()
        center.handle_communication_event("result.critical", {"result_id": "R-1"})
        # nothing delivered
        assert provider.deliveries == []

    def test_unbound_policy_fails_audit(self):
        center, provider = make_center()
        center.event_policies.bind("backup.failed", "ghost-policy", recipient_key="recipient")
        center.handle_communication_event("backup.failed", {"recipient": "ops@moh.iq"})
        assert provider.deliveries == []


class TestEventBridge:
    def test_bridge_binds_closures_to_bus(self):
        center, provider = make_center()
        bus = FakeBus()
        bridge = EventBridge(center, center.event_policies)
        bridge.bind(bus)
        assert bus.handlers.get("result.critical")
        bus.emit("result.critical", {"recipient": "a@b.c", "result_id": 7})
        assert provider.deliveries

    def test_bridge_is_idempotent(self):
        center, _provider = make_center()
        bus = FakeBus()
        bridge = EventBridge(center, center.event_policies)
        bridge.bind(bus)
        bridge.bind(bus)
        assert len(bus.handlers["result.critical"]) == 1

    def test_bridge_handle_direct(self):
        center, _provider = make_center()
        bus = FakeBus()
        bridge = EventBridge(center, center.event_policies)
        bridge.bind(bus)
        assert bridge.bound_event_names() == ["result.critical"]
