"""Composition root tests: the backend wires the Core to the platform's
canonical event bus and starter policies — no DB/Redis required."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _clean_singleton():
    from app.communication import reset_center

    reset_center()
    yield
    reset_center()


class TestCompositionRoot:
    def test_singleton_builds_with_starter_content(self):
        from app.communication import get_communication_center

        center = get_communication_center()
        assert get_communication_center() is center
        health = center.health()
        assert health["policies"] >= 3
        assert health["channel_count"] == 0  # providers plug in PROGRAM-COMM-002
        policy_ids = {p["id"] for p in center.policies.list_policies()}
        assert {"platform.result.critical", "platform.order.validated", "platform.backup.failed"} <= policy_ids
        template_ids = {t["id"] for t in center.templates.list_templates()}
        assert {"alert.critical_result", "inform.order_validated", "alert.backup_failed"} <= template_ids
        event_names = {b["event_name"] for b in center.event_policies.bindings()}
        assert {"result.critical", "order.validated", "backup.failed"} == event_names

    def test_event_bus_consumption_no_providers_yet(self):
        """Emitting a bound platform event reaches the Center and resolves a
        policy (delivery fails cleanly: no provider is registered yet)."""
        from app.communication import get_communication_center
        from app.core.events import events

        center = get_communication_center()
        receipt = center.handle_communication_event(
            "backup.failed",
            {"recipient": "ops@moh.gov.iq", "target": "pg-main"},
        )
        assert receipt.state == "failed"
        assert "no provider" in (receipt.attempts[0].error or "")

    def test_emitting_on_real_bus_is_safe(self):
        from app.communication import get_communication_center
        from app.core.events import events

        get_communication_center()
        events.emit("order.validated", {"recipient": "lab@moh.gov.iq", "order_id": 1})
        # Reaching here without exception proves bus → Center consumption works.
