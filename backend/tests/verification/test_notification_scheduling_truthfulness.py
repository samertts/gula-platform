"""A notification "scheduled" for next week was delivered at once.

IA-079 and IA-080 — the same defect at two layers, with one root cause.

**The root cause.** ``app/tasks/schema.py::TaskPayload`` carries
``task_id, type, payload, retry_count, max_retries, timeout_s, enqueued_at``
and nothing else: no ``delay``, no ``run_at``, no ``eta``.
``TaskQueue.enqueue(task)`` takes the payload alone. So nothing in this
platform can hold a task until a future time.

**IA-079, ``app/platform/notifications.py``.** ``schedule_notification``
accepted ``schedule_at`` and ignored it:

```python
def schedule_notification(self, channel, to, subject="", body="", schedule_at=None):
    result = self._service.send(channel=channel, to=to, subject=subject, body=body)
    return NotificationResult(success=result.success, ...)
```

Measured against a stub SMS gateway with ``schedule_at=2027-01-01 09:00``:
one immediate POST of ``{"to": ..., "text": "refill reminder"}``, no trace of
the date anywhere, ``success=True``. And ``PlatformRegistry`` advertised the
method as *"Schedule a notification for later delivery"*.

**IA-080, ``app/national/notification_platform``.** The same thing, with a
twist that makes it harder to see:

```python
delay_s = max(0, (scheduled_at - _now()).total_seconds())
await task_queue.enqueue(TaskPayload(..., timeout_s=int(delay_s) + 60))
```

The delay *is* computed — and then spent as the task's **timeout**, which is
how long the task may run, not when it may start. So the delivery task was
enqueued for immediate execution with an inflated timeout, a
``NotificationSchedule`` row was persisted saying otherwise, and the route
answered **201** echoing the future date back to the caller.

Nor would a poller have rescued it. The only reader of ``NotificationSchedule``
is the ``GET /schedules`` listing; ``find_due_schedules`` belongs to
``background_platform`` and a different repository.

**The repair is refusal, not a scheduler.** Building the missing primitive
means choosing retry, visibility and recurrence semantics for a clinical
notification path — a medication reminder, an appointment, a result. That is
not a decision to make while passing through. A future or recurring schedule
is refused and the gap is named; an immediate send still works.
"""
from __future__ import annotations

import ast
import json
import pathlib
import threading
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from app._compat import UTC

TASK_SCHEMA = (
    pathlib.Path(__file__).resolve().parents[2] / "app" / "tasks" / "schema.py"
)

#: Field names that would let a task be held until a future time. Pinned so
#: that if one is ever added, these tests fail and demand the refusals be
#: replaced with a real schedule rather than left in place.
DELAY_FIELD_NAMES = {"delay", "delay_s", "run_at", "eta", "not_before", "visible_at"}


# --------------------------------------------------------------------------
# the root cause, asserted directly
# --------------------------------------------------------------------------

def test_the_task_payload_has_no_way_to_express_a_delay():
    """The fact every refusal below rests on.

    Ratchets both ways. The day a delay field is added, this fails — and the
    refusals become wrong and must be replaced with a real schedule.
    """
    from app.tasks.schema import TaskPayload

    fields = set(TaskPayload.model_fields)
    assert fields, "positive control: the model has fields at all"
    overlap = fields & DELAY_FIELD_NAMES
    assert not overlap, (
        f"TaskPayload now has {sorted(overlap)}. A delay primitive exists, so "
        f"IA-079 and IA-080 should be re-fixed by honouring the schedule "
        f"instead of refusing it."
    )
    # the field that was mistaken for one
    assert "timeout_s" in fields


def test_enqueue_accepts_no_schedule_argument():
    import inspect

    from app.tasks import queue as queue_module

    implementations = [
        getattr(queue_module, n) for n in dir(queue_module)
        if n.endswith("Queue") and isinstance(getattr(queue_module, n), type)
    ]
    assert implementations, "positive control: at least one queue exists"

    for impl in implementations:
        params = set(inspect.signature(impl.enqueue).parameters) - {"self"}
        assert params == {"task"}, (
            f"{impl.__name__}.enqueue now takes {sorted(params)}; if one of "
            f"them defers execution, the IA-079/IA-080 refusals are obsolete."
        )


# --------------------------------------------------------------------------
# IA-079 — the platform wrapper
# --------------------------------------------------------------------------

class _Gateway(BaseHTTPRequestHandler):
    received: list = []

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length", 0))
        type(self).received.append(json.loads(self.rfile.read(length) or b"{}"))
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"{}")

    def log_message(self, *args):  # silence
        return


@pytest.fixture()
def sms_gateway(monkeypatch):
    """A working SMS gateway, so a failure here is never a transport failure."""
    import shared.notifications.sender as sender_module

    _Gateway.received = []
    server = HTTPServer(("127.0.0.1", 0), _Gateway)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

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


def test_a_future_schedule_is_refused_not_sent_now(sms_gateway):
    from app.platform.notifications import (
        NotificationSchedulingUnavailable,
        NotificationService,
    )

    future = datetime.now(UTC) + timedelta(days=90)
    with pytest.raises(NotificationSchedulingUnavailable) as excinfo:
        NotificationService().schedule_notification(
            channel="sms", to="+9647700000000", body="refill reminder",
            schedule_at=future,
        )

    assert not sms_gateway, (
        f"the gateway received {sms_gateway} — a notification dated "
        f"{future.isoformat()} was delivered now"
    )
    assert "no deferred-execution primitive" in str(excinfo.value)


def test_an_immediate_send_still_works(sms_gateway):
    """The positive control: the repair is not 'refuse everything'."""
    from app.platform.notifications import NotificationService

    result = NotificationService().schedule_notification(
        channel="sms", to="+9647700000000", body="now", schedule_at=None,
    )
    assert result.success is True
    assert len(sms_gateway) == 1, sms_gateway
    assert sms_gateway[0]["text"] == "now"


def test_the_capability_listing_no_longer_advertises_scheduling():
    """The registry entry is read as a statement about what the platform does."""
    from app.platform import PlatformRegistry

    import app.platform.notifications  # noqa: F401  (registers the module)

    capabilities = PlatformRegistry.get_capabilities()
    assert capabilities, "positive control: the registry has capabilities"

    entry = next(
        (
            c for c in capabilities
            if c.get("name") == "schedule_notification"
            and c.get("module") == "notifications"
        ),
        None,
    )
    assert entry is not None, "the capability vanished rather than being marked"
    assert entry.get("available") is False, (
        f"still advertised as available: {entry}. It cannot defer delivery."
    )
    assert entry.get("unavailable_reason"), "unavailable without a reason"
    assert "later delivery" not in entry.get("description", ""), entry


# --------------------------------------------------------------------------
# IA-080 — the national service
# --------------------------------------------------------------------------

def test_the_national_service_no_longer_spends_the_delay_as_a_timeout():
    """AST: ``delay_s`` must not reach ``timeout_s``.

    This is the shape that made the defect hard to see — the delay was
    computed, which reads like it was honoured.
    """
    service = (
        pathlib.Path(__file__).resolve().parents[2]
        / "app" / "national" / "notification_platform" / "application" / "service.py"
    )
    source = service.read_text()
    tree = ast.parse(source)

    schedule = next(
        n for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        and n.name == "schedule_notification"
    )
    body = ast.get_source_segment(source, schedule) or ""
    assert body, "positive control: the method was found"

    assert "timeout_s=int(delay_s)" not in body, (
        "the computed delay is still being passed as the task timeout, which "
        "is how long the task may run, not when it may start"
    )
    assert "NotificationSchedulingUnavailable" in body, (
        "a future schedule is no longer refused"
    )


def test_the_national_route_reports_the_gap_as_501():
    routes = (
        pathlib.Path(__file__).resolve().parents[2]
        / "app" / "national" / "notification_platform" / "api" / "routes.py"
    )
    tree = ast.parse(routes.read_text())

    handler = next(
        n for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        and n.name == "schedule_notification"
    )

    handled = {
        h.type.id if isinstance(h.type, ast.Name) else getattr(h.type, "attr", "")
        for try_node in ast.walk(handler) if isinstance(try_node, ast.Try)
        for h in try_node.handlers
        if h.type is not None
    }
    assert "NotificationSchedulingUnavailable" in handled, (
        f"the refusal would surface as a 500; handlers are {sorted(handled)}"
    )

    source = ast.get_source_segment(routes.read_text(), handler) or ""
    assert "HTTP_501_NOT_IMPLEMENTED" in source, (
        "the response must say the capability is absent, not that the request "
        "was bad or that the server broke"
    )


def test_the_reason_is_stated_once_for_both_layers():
    """Two refusals that drift apart are worse than one.

    Each layer names its own gap, but both must describe the same missing
    primitive, so a reader of either finds the same fact.
    """
    from app.national.notification_platform.exceptions import (
        SCHEDULING_UNAVAILABLE_REASON as national,
    )
    from app.platform.notifications import (
        SCHEDULING_UNAVAILABLE_REASON as platform,
    )

    for reason in (national, platform):
        assert "TaskPayload" in reason
        assert "delay" in reason
    assert "find_due_schedules" in national, (
        "the national reason must also record that nothing polls the rows it "
        "persists, which the platform wrapper does not have to care about"
    )
