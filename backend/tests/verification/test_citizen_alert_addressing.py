"""A critical result alert was addressed to a citizen UUID.

IA-078, and IA-081 recorded beside it because they are two halves of one
broken loop: nothing can write a citizen notification honestly, and the one
served endpoint that reads them has no writer at all.

IA-078. ``CitizenNotificationService.send_notification`` passed
``citizen_id`` straight through as the SMS or email recipient:

```python
if channel != "in_app":
    return self._platform.send_notification(channel=channel, to=citizen_id, ...)
```

Measured against a **working** stub SMS gateway — so this is not a transport
failure — ``AlertService.send_critical_alert`` for a potassium of 7.9 mmol/L
produced:

    result   NotificationResult(success=True, channel='sms', error=None)
    gateway  {"to": "c7f3a1e2-9b44-4d10-8e55-0a1b2c3d4e5f",
              "text": "Potassium 7.9 mmol/L", "sender": null}

An internal identifier where a phone number belongs. The gateway answered
200, so ``raise_for_status()`` passed, so the platform reported delivery.

> **The alert reached nobody, on a fully configured deployment.** This is the
> layer IA-076 cannot help with: there, the transport honestly reported that
> it had sent nothing. Here the transport genuinely succeeded and the address
> was wrong, so every honest signal in the stack said yes.

The repair is not a contact lookup. This class holds no citizen registry, no
session and no contact repository, and choosing *which* address — verified
only? consented? primary? — is a policy this audit must not invent. So the
address is the caller's to supply and a non-in_app channel without one is
refused.

IA-081, measured while establishing IA-078's reachability. ``AlertService``
has **no caller anywhere**: ``citizen_platform/integration.py`` constructs it
and discards the value (``AlertService(notification_service=notifications)``
on a line of its own), and the only other mention in the repository is a name
in ``app/ai/guardrails.py``'s list of tool names. A repository-wide search for
every writer name — ``send_notification``, ``broadcast_notification``,
``send_critical_alert``, ``send_lab_result_alert``, ``send_medication_alert``,
``send_appointment_reminder`` — finds no call outside
``citizen_platform/notifications.py`` itself, in app or tests.

Meanwhile ``GET /citizen-platform/notifications/{citizen_id}`` **is** served
and reads ``self._notifications``, the per-process dict those methods write.
So it answers 200 with ``{"notifications": [], "total": 0, "unread_count": 0}``
and can never answer anything else — and a client cannot tell that from a
citizen who genuinely has no notifications. Same shape as IA-014/IA-015.

IA-081 is recorded, not repaired: deciding whether citizen notifications
should be persisted, and in which table, is a schema and product decision.
These tests pin the measurement so the gap cannot close or widen silently.
"""
from __future__ import annotations

import ast
import json
import pathlib
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

NOTIFICATIONS = (
    pathlib.Path(__file__).resolve().parents[2]
    / "app" / "citizen_platform" / "notifications.py"
)

#: Every method that can append to the citizen alert store. Pinned so a new
#: writer cannot appear without this suite noticing.
WRITER_NAMES = (
    "send_notification",
    "broadcast_notification",
    "send_critical_alert",
    "send_lab_result_alert",
    "send_medication_alert",
    "send_appointment_reminder",
)

#: The channels that leave the process and therefore need a real address.
EXTERNAL_CHANNELS = ("sms", "email", "whatsapp", "push")


class _Gateway(BaseHTTPRequestHandler):
    received: list = []

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length", 0))
        type(self).received.append(json.loads(self.rfile.read(length) or b"{}"))
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"{}")

    def log_message(self, *args):
        return


@pytest.fixture()
def sms_gateway():
    """A gateway that works, so a failure is never about the transport."""
    import shared.notifications.sender as sender_module

    _Gateway.received = []
    server = HTTPServer(("127.0.0.1", 0), _Gateway)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    previous = sender_module._sender
    sender_module._sender = sender_module.NotificationSender(
        sms_api_url=f"http://127.0.0.1:{server.server_port}/send",
    )
    try:
        yield _Gateway.received
    finally:
        sender_module._sender = previous
        server.shutdown()
        server.server_close()


def _alerts():
    from app.citizen_platform.notifications import (
        AlertService,
        CitizenNotificationService,
    )

    return AlertService(CitizenNotificationService())


# --------------------------------------------------------------------------
# IA-078
# --------------------------------------------------------------------------

def test_a_critical_alert_without_a_phone_number_is_refused(sms_gateway):
    with pytest.raises(ValueError) as excinfo:
        _alerts().send_critical_alert(
            citizen_id="c7f3a1e2-9b44-4d10-8e55-0a1b2c3d4e5f",
            title="CRITICAL potassium", title_ar="بوتاسيوم حرج",
            message="Potassium 7.9 mmol/L — act now", message_ar="...",
        )

    assert not sms_gateway, (
        f"the gateway received {sms_gateway}; before the fix this carried the "
        f"citizen UUID as the recipient and reported success"
    )
    assert "internal identifier" in str(excinfo.value)


def test_a_critical_alert_with_a_phone_number_reaches_that_number(sms_gateway):
    """The positive control, and the assertion that would have caught IA-078.

    It checks the address the gateway actually received, not the result flag —
    the result flag was True throughout the defect.
    """
    result = _alerts().send_critical_alert(
        citizen_id="c7f3a1e2-9b44-4d10-8e55-0a1b2c3d4e5f",
        title="CRITICAL potassium", title_ar="بوتاسيوم حرج",
        message="Potassium 7.9 mmol/L — act now", message_ar="...",
        recipient_phone="+9647701234567",
    )

    assert result.success is True
    assert len(sms_gateway) == 1, sms_gateway
    assert sms_gateway[0]["to"] == "+9647701234567", (
        f"the gateway was addressed {sms_gateway[0]['to']!r}"
    )
    assert "c7f3a1e2" not in json.dumps(sms_gateway), (
        "the citizen identifier leaked into the outbound message"
    )


@pytest.mark.parametrize("channel", EXTERNAL_CHANNELS)
def test_no_external_channel_accepts_an_identifier_as_an_address(channel, sms_gateway):
    """Covers the shape, not just the two methods that use sms today."""
    from app.citizen_platform.enums import CitizenNotificationType
    from app.citizen_platform.notifications import CitizenNotificationService

    service = CitizenNotificationService()
    with pytest.raises(ValueError):
        service.send_notification(
            citizen_id="c7f3a1e2-9b44-4d10-8e55-0a1b2c3d4e5f",
            notification_type=CitizenNotificationType.EMERGENCY_ALERT,
            title="t", title_ar="t", message="m", message_ar="m",
            channel=channel,
        )
    assert not sms_gateway


def test_the_in_app_channel_is_unchanged():
    """The repair must not make the default path require an address."""
    result = _alerts().send_lab_result_alert(
        citizen_id="c7f3a1e2-9b44-4d10-8e55-0a1b2c3d4e5f",
        lab_name="Baghdad Central", result_summary="Glucose 5.4 mmol/L",
    )
    assert result.success is True
    assert result.channel == "in_app"


def test_no_writer_passes_the_citizen_id_as_the_recipient():
    """AST ratchet over the module: ``to=citizen_id`` must not come back."""
    source = NOTIFICATIONS.read_text()
    tree = ast.parse(source)

    offenders: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for kw in node.keywords:
            # ``recipient`` on NotificationResult is a report field, not a
            # delivery address, and for an in-app alert the citizen id is the
            # right value there. Only the arguments that actually address a
            # transport are checked.
            if kw.arg not in {"to", "recipient_address"}:
                continue
            if isinstance(kw.value, ast.Name) and kw.value.id == "citizen_id":
                offenders.append(f"line {node.lineno}: {kw.arg}=citizen_id")

    assert not offenders, (
        f"an internal identifier is being used as a delivery address again: "
        f"{offenders}"
    )


# --------------------------------------------------------------------------
# IA-081 — the served read path has no writer
# --------------------------------------------------------------------------

def test_the_citizen_alert_store_is_still_per_process_memory():
    """Recorded, not repaired. Pinned so it cannot change unnoticed.

    Whether citizen notifications should be persisted, and in which table, is
    a schema and product decision this audit does not take. What is measurable
    is that the store is a dict on the instance, so an alert written by one
    gunicorn worker is invisible to a request served by another and gone on
    restart.
    """
    from app.citizen_platform.notifications import CitizenNotificationService

    service = _alerts()._notification_service
    assert isinstance(service._notifications, dict), (
        "the store changed shape — if it is now persistent, this finding is "
        "stale and IA-081 should be re-read"
    )

    alerts = _alerts()
    service = alerts._notification_service
    other = CitizenNotificationService()
    alerts.send_lab_result_alert(
        citizen_id="cit-1", lab_name="L", result_summary="x",
    )
    assert service.get_notifications("cit-1"), "positive control: the write landed"
    assert not other.get_notifications("cit-1"), (
        "two instances now share state, so this is no longer per-process "
        "memory — re-read IA-081"
    )


def test_the_served_read_endpoint_has_no_writer_anywhere():
    """GET /citizen-platform/notifications/{citizen_id} can only return [].

    Searched across app/ and tests/ for every writer name. The only calls are
    inside notifications.py itself, where AlertService delegates to
    CitizenNotificationService — and AlertService has no caller.
    """
    root = pathlib.Path(__file__).resolve().parents[2]
    searched = list((root / "app").rglob("*.py")) + list(
        (root / "tests").rglob("*.py")
    )
    assert len(searched) > 500, (
        f"positive control: only {len(searched)} files searched, the corpus "
        f"cannot be that small"
    )

    callers: dict[str, list[str]] = {}
    for path in searched:
        if path == NOTIFICATIONS or path.resolve() == pathlib.Path(__file__).resolve():
            continue
        try:
            tree = ast.parse(path.read_text(errors="replace"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = (
                node.func.attr if isinstance(node.func, ast.Attribute)
                else node.func.id if isinstance(node.func, ast.Name)
                else None
            )
            if name in WRITER_NAMES:
                callers.setdefault(name, []).append(
                    f"{path.relative_to(root)}:{node.lineno}"
                )

    # send_notification is also the name on the national and platform
    # services, which are unrelated; only the citizen store matters here.
    citizen_writers = {
        name: sites for name, sites in callers.items()
        if name != "send_notification"
    }
    assert not citizen_writers, (
        f"a writer appeared, so GET /citizen-platform/notifications can now "
        f"return something: {citizen_writers}. IA-081 is no longer accurate "
        f"and the endpoint's behaviour must be re-measured."
    )


def test_the_alert_service_is_constructed_and_discarded():
    """How a whole service came to have no caller.

    ``integration.py`` builds it on a line of its own and keeps nothing, so
    the object is garbage immediately. Pinned because the fix — binding it and
    wiring a caller — must be a deliberate change, not a silent one.
    """
    integration = (
        pathlib.Path(__file__).resolve().parents[2]
        / "app" / "citizen_platform" / "integration.py"
    )
    source = integration.read_text()
    tree = ast.parse(source)

    discarded = [
        node.lineno for node in ast.walk(tree)
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "AlertService"
    ]
    assert discarded, (
        "AlertService is no longer constructed-and-discarded in integration.py "
        "— if it is now bound and used, re-read IA-081 and IA-078's "
        "reachability, which was assessed as latent on this basis"
    )
