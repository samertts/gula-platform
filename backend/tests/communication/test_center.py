"""Unit tests: Communication Center orchestration (DI, routing, audit)."""

from __future__ import annotations

from shared.communication import (
    CommunicationCenter,
    OutboundMessage,
    Policy,
    Priority,
)
from shared.communication.model import ContentFormat
from shared.communication.providers import ProviderRegistry

from .fakes import (
    AlertFakeProvider,
    ExplodingProvider,
    FakeProvider,
    InMemoryStateStore,
    MediaFakeProvider,
    RecordingAuditSink,
    RichFakeProvider,
    StatusFakeProvider,
)


def build_center(
    *providers,
    audit=None,
    state_store=None,
    policies=None,
):
    registry = ProviderRegistry()
    for provider in providers:
        registry.register(provider)
    return CommunicationCenter(
        providers=registry,
        audit=audit or RecordingAuditSink(),
        state_store=state_store or InMemoryStateStore(),
        policies=policies,
    )


class TestDispatchBasics:
    def test_delivers_text_message(self):
        provider = FakeProvider()
        center = build_center(provider)
        receipt = center.dispatch(
            "user@example.com",
            content="hello",
            policy=Policy(id="p", required_channels=("email",)),
        )
        assert receipt.state == "delivered"
        assert receipt.attempts[0].success is True
        assert provider.deliveries[0][1].content == "hello"

    def test_requires_recipient(self):
        center = build_center(FakeProvider())
        try:
            center.dispatch("", content="x", policy=Policy(id="p"))
        except ValueError:
            return
        raise AssertionError("empty recipient must raise")

    def test_requires_payload(self):
        center = build_center(FakeProvider())
        try:
            center.dispatch("a@b.c", policy=Policy(id="p"))
        except ValueError:
            return
        raise AssertionError("missing payload must raise")

    def test_no_provider_for_channel_fails_cleanly(self):
        center = build_center()
        receipt = center.dispatch(
            "a@b.c",
            content="x",
            policy=Policy(id="p", required_channels=("email",)),
        )
        assert receipt.state == "failed"
        assert "no provider" in (receipt.error or receipt.attempts[0].error or "")

    def test_exploding_provider_does_not_crash_center(self):
        center = build_center(ExplodingProvider())
        receipt = center.dispatch(
            "a@b.c",
            content="x",
            policy=Policy(id="p", required_channels=("email",)),
        )
        assert receipt.state == "failed"
        assert receipt.attempts[0].success is False

    def test_uses_outbound_message_directly(self):
        provider = FakeProvider()
        center = build_center(provider)
        msg = OutboundMessage(content="direct", format=ContentFormat.PLAIN)
        receipt = center.dispatch("a@b.c", message=msg, policy=Policy(id="p", required_channels=("email",)))
        assert receipt.state == "delivered"
        assert provider.deliveries[0][1].content == "direct"

    def test_unknown_named_policy_raises(self):
        center = build_center(FakeProvider())
        try:
            center.dispatch("a@b.c", content="x", policy="no-such-policy")
        except ValueError:
            return
        raise AssertionError("unknown policy must raise")

    def test_delivery_id_is_unique(self):
        center = build_center(FakeProvider())
        r1 = center.dispatch("a@b.c", content="x", policy=Policy(id="p", required_channels=("email",)))
        r2 = center.dispatch("a@b.c", content="x", policy=Policy(id="p", required_channels=("email",)))
        assert r1.delivery_id != r2.delivery_id


class TestCapabilityRouting:
    def test_rich_content_uses_rich_capability(self):
        provider = RichFakeProvider()
        center = build_center(provider)
        receipt = center.dispatch(
            "@chan",
            content="<b>hi</b>",
            format=ContentFormat.HTML,
            policy=Policy(id="p", required_channels=("chat",)),
        )
        assert receipt.state == "delivered"
        assert provider.calls == ["deliver_rich"]

    def test_plain_content_uses_base_deliver(self):
        provider = RichFakeProvider()
        center = build_center(provider)
        receipt = center.dispatch(
            "@chan",
            content="plain",
            format=ContentFormat.PLAIN,
            policy=Policy(id="p", required_channels=("chat",)),
        )
        assert receipt.state == "delivered"
        assert provider.calls == ["deliver"]

    def test_alert_uses_alert_capability(self):
        provider = AlertFakeProvider()
        center = build_center(provider)
        receipt = center.dispatch(
            "a@b.c",
            content="disk full",
            severity="critical",
            policy=Policy(id="p", required_channels=("email",)),
        )
        assert receipt.state == "delivered"
        assert provider.alert_severities == ["critical"]

    def test_attachments_use_media_capability(self):
        from shared.communication import Attachment

        provider = MediaFakeProvider()
        center = build_center(provider)
        msg = OutboundMessage(content="with file", attachments=(Attachment(reference="file:///tmp/x.pdf"),))
        receipt = center.dispatch(
            "a@b.c",
            message=msg,
            policy=Policy(id="p", required_channels=("email",)),
        )
        assert receipt.state == "delivered"
        assert provider.media_attachments[0][1][0].reference == "file:///tmp/x.pdf"


class TestRetries:
    def test_retryable_failure_retries_up_to_limit(self):
        provider = FakeProvider(name="f", channel="email", fail_on={"deliver"}, fail_retryable=True)
        center = build_center(provider)
        receipt = center.dispatch(
            "a@b.c",
            content="x",
            policy=Policy(id="p", required_channels=("email",), max_retries=3),
        )
        assert receipt.state == "failed"
        assert len(provider.calls) == 3  # initial + 2 retries (max_retries=3 → attempts capped)

    def test_non_retryable_failure_no_retry(self):
        provider = FakeProvider(name="f", channel="email", fail_on={"deliver"}, fail_retryable=False)
        center = build_center(provider)
        receipt = center.dispatch(
            "a@b.c",
            content="x",
            policy=Policy(id="p", required_channels=("email",), max_retries=5),
        )
        assert receipt.state == "failed"
        assert len(provider.calls) == 1

    def test_retry_then_success(self):
        class Flaky(FakeProvider):
            def deliver(self, recipient, message, options=None):
                self.calls.append("deliver")
                if len(self.calls) < 2:
                    return self._make_result(False, retryable=True)
                return self._make_result(True)

        provider = Flaky(name="flaky", channel="email")
        center = build_center(provider)
        receipt = center.dispatch(
            "a@b.c",
            content="x",
            policy=Policy(id="p", required_channels=("email",), max_retries=3),
        )
        assert receipt.state == "delivered"
        assert len(provider.calls) == 2


class TestFallbackAndEscalation:
    def test_fallback_channel_used_when_primary_fails(self):
        primary = FakeProvider(name="primary", channel="email", fail_on={"always"}, fail_retryable=False)
        backup = FakeProvider(name="backup", channel="sms")
        center = build_center(primary, backup)
        receipt = center.dispatch(
            "555",
            content="x",
            policy=Policy(
                id="p",
                required_channels=("email",),
                fallback_channels=("sms",),
            ),
        )
        assert receipt.state == "delivered"
        assert backup.deliveries

    def test_escalation_channels_tried_after_all_fail(self):
        primary = FakeProvider(name="primary", channel="email", fail_on={"always"}, fail_retryable=False)
        esc = FakeProvider(name="esc", channel="sms")
        center = build_center(primary, esc)
        receipt = center.dispatch(
            "555",
            content="x",
            policy=Policy(
                id="p",
                required_channels=("email",),
                escalation_channels=("sms",),
            ),
        )
        assert receipt.state == "delivered"
        assert esc.deliveries

    def test_no_escalation_when_delivered(self):
        primary = FakeProvider(name="primary", channel="email")
        esc = FakeProvider(name="esc", channel="sms")
        center = build_center(primary, esc)
        receipt = center.dispatch(
            "a@b.c",
            content="x",
            policy=Policy(
                id="p",
                required_channels=("email",),
                escalation_channels=("sms",),
            ),
        )
        assert receipt.state == "delivered"
        assert not esc.deliveries


class TestAudit:
    def test_dispatch_records_audit_events(self):
        audit = RecordingAuditSink()
        center = build_center(FakeProvider(), audit=audit)
        center.dispatch("a@b.c", content="x", policy=Policy(id="p", required_channels=("email",)))
        assert audit.count("communication.dispatch.created") >= 1
        assert audit.count("communication.policy.decision") >= 1
        assert audit.count("communication.provider.attempt") >= 1
        assert audit.count("communication.state.transition") >= 1

    def test_state_transitions_persisted(self):
        store = InMemoryStateStore()
        center = build_center(FakeProvider(), state_store=store)
        receipt = center.dispatch("a@b.c", content="x", policy=Policy(id="p", required_channels=("email",)))
        record = store.get(receipt.delivery_id)
        assert record is not None
        assert record.state.value == "delivered"

    def test_provider_down_is_skipped(self):
        from shared.communication.providers import ProviderHealth

        down = FakeProvider(name="down", channel="email", health=ProviderHealth.DOWN)
        up = FakeProvider(name="up", channel="email")
        center = build_center(down, up)
        receipt = center.dispatch(
            "a@b.c",
            content="x",
            policy=Policy(id="p", required_channels=("email",)),
        )
        assert receipt.state == "delivered"
        assert up.deliveries


class TestStatusCallback:
    def test_status_forwarded_to_capable_provider(self):
        provider = StatusFakeProvider(name="statusy", channel="sms")
        center = build_center(provider)
        center.on_status_change("statusy", "ref-1", "read")
        assert provider.status_changes == [("ref-1", "read")]

    def test_status_ignored_for_incapable_provider(self):
        provider = FakeProvider(name="plain", channel="email")
        center = build_center(provider)
        center.on_status_change("plain", "ref-1", "read")  # must not raise


class TestHealth:
    def test_health_snapshot(self):
        center = build_center(FakeProvider(name="a", channel="email"), RichFakeProvider(name="b"))
        health = center.health()
        assert health["channel_count"] == 2
        names = {p["name"] for p in health["providers"]}
        assert names == {"a", "b"}
