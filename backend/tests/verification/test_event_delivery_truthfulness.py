"""Every event this platform emits is delivered to nobody, and said so as success.

IA-043 (P1 for the clinical half, which is NEEDS_DECISION; the observability half
is fixed here).

MEASURED at runtime, after `import app.main` has imported every route module:

    app.core.events.events._handlers        {}          (zero handlers)
    emit("result.critical", {})             -> 0        delivered to nobody
    emit("order.validated", {})             -> 0
    emit("order.created", {})                -> 0
    emit("order.cancelled", {})              -> 0
    emit("patient.created", {})              -> 0

`@events.on` occurs exactly once in the whole repository, inside the usage
example in app/core/events.py's docstring. Six production modules emit onto this
bus -- order_service, test_results, outbox_service, data_platform_service, and
the national citizen and family services.

Two claims were resting on that bus:

  1. app/models/outbox.py: "This guarantees at-least-once delivery". The
     transactional hand-off is real -- the row is committed with the business
     operation and the worker will retry until it is dispatched. But
     `OutboxWorker.run_once` marked a row "done" and logged
     `dispatched_to=0 handlers` at INFO, so an event acted upon by nobody was
     recorded exactly like one that was.

  2. app/routes/test_results.py: "Fire critical-value event for downstream
     notifications", immediately before emitting result.critical for a value the
     platform has flagged critical. No notification is sent: the event has no
     subscriber, and a sweep of backend/app/routes and backend/app/services finds
     exactly one caller of any notification-sending method in the whole platform
     -- routes/verification.py sending an OTP SMS. No clinical path notifies
     anyone of anything.

     A critical value is therefore *recorded* and *discoverable* -- it is stored
     with its flag, and GET /critical-alerts lists it -- but nothing pushes it to
     a clinician. That is a pull model, which is a legitimate design; the defect
     is that the code claimed a push and nothing in the running system said
     otherwise.

FIXED HERE (observability only):
  * EventBus.emit logs a WARNING the first time a given event name is emitted
    with no subscriber, so the gap appears in the logs of any process that emits.
    Once per name per process, so it cannot flood.
  * OutboxWorker.run_once logs a zero-handler dispatch at WARNING and counts it
    in summary["undelivered"]. The row still reaches "done": the event *was*
    handed to the dispatcher, and re-queueing would retry forever against a bus
    with no subscribers, while a new terminal status would also escape
    purge_old_events (which deletes only 'done' and 'failed') and grow the table
    without bound.
  * The two docstrings and the one comment now state the scope of the guarantee
    instead of overstating it.

NOT DONE, and why: implementing critical-value notification means authoring
clinical escalation policy -- who is notified, through which channel, with what
retry, and with what documented read-back, which ISO 15189 requires. Inventing
that to close a finding would be worse than the finding. It is raised as
NEEDS_DECISION.
"""
from __future__ import annotations

import logging
import pathlib
import re

import pytest

_REPO = pathlib.Path(__file__).resolve().parents[3]
_BACKEND_APP = _REPO / "backend" / "app"

_CLINICAL_EVENTS = [
    "result.critical",
    "order.created",
    "order.validated",
    "order.cancelled",
    "sample.rejected",
    "patient.created",
]


def _python_sources(root: pathlib.Path) -> list[pathlib.Path]:
    return [p for p in root.rglob("*.py") if "__pycache__" not in p.parts]


# ── the measurement ─────────────────────────────────────────────────────────


def test_the_canonical_bus_has_no_handlers_after_the_app_is_imported():
    """`import app.main` is what a served process does, so this is the real
    handler table, not a fresh bus."""
    import app.main  # noqa: F401  — imports every route module
    from app.core.events import events

    registered = {name: len(hs) for name, hs in events._handlers.items() if hs}
    assert registered == {}, (
        f"the canonical EventBus now has handlers: {registered} -- IA-043's "
        "zero-subscriber measurement is stale, re-check what acts on them"
    )


@pytest.mark.parametrize("event_name", _CLINICAL_EVENTS)
def test_emitting_a_clinical_event_reaches_nobody(event_name):
    import app.main  # noqa: F401
    from app.core.events import events

    assert events.emit(event_name, {}) == 0


def test_the_only_events_on_registration_is_in_a_docstring():
    """A ratchet on the root cause. `@events.on` in executable code would mean a
    real subscriber exists and this whole finding needs re-measuring."""
    import ast

    hits = []
    for path in _python_sources(_BACKEND_APP) + _python_sources(_REPO / "shared"):
        text = path.read_text(errors="replace")
        if "events.on(" not in text:
            continue
        try:
            tree = ast.parse(text)
        except SyntaxError:  # pragma: no cover
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if (
                isinstance(func, ast.Attribute)
                and func.attr == "on"
                and isinstance(func.value, ast.Name)
                and func.value.id == "events"
            ):
                hits.append(f"{path.relative_to(_REPO).as_posix()}:{node.lineno}")
    assert hits == [], (
        f"a real events.on registration now exists at {hits}; re-measure IA-043"
    )


def test_no_clinical_path_sends_a_notification():
    """The claim in test_results.py is that a notification follows a critical
    value. Nothing in routes/ or services/ calls a sender except the OTP path."""
    senders = re.compile(r"\b(send_sms|send_whatsapp|send_email|send_push|send_template)\s*\(")
    callers = sorted(
        {
            path.relative_to(_REPO).as_posix()
            for root in (_BACKEND_APP / "routes", _BACKEND_APP / "services")
            for path in _python_sources(root)
            if senders.search(path.read_text(errors="replace"))
        },
    )
    assert callers == ["backend/app/routes/verification.py"], (
        "the notification call sites changed; if a clinical path now notifies, "
        f"IA-043's second half may be closed: {callers}"
    )


def test_a_critical_value_is_still_recorded_and_discoverable():
    """Positive control, and the reason this is NEEDS_DECISION rather than a
    data-loss finding: the value itself is not lost. It is stored with its flag
    and listed by the pull endpoint."""
    from app.services.critical_alerts import check_critical, get_critical_alerts

    assert callable(get_critical_alerts)

    alert = check_critical("Potassium", 7.5)
    assert alert is not None, "a critically high potassium no longer evaluates as critical"
    # Asserted against the value the function really returns. The first draft of
    # this test allowed `severity in {"critical", "high"} or "message" in alert`,
    # which passed on the `or` branch while the severity assertion was wrong --
    # a weak assertion dressed as a strong one.
    assert alert["severity"] == "critical_high"
    assert alert["threshold"] == 6.5
    assert "Immediate medical attention required" in alert["message"]
    assert alert["message_ar"], "the Arabic message is the one a local clinician reads"

    # Negative control: the evaluation is discriminating, not always-critical.
    assert check_critical("Potassium", 4.0) is None


# ── the fix: the silence is now audible ─────────────────────────────────────


def test_an_unsubscribed_emission_warns_once_per_event_name(caplog):
    from app.core.events import EventBus

    bus = EventBus()
    with caplog.at_level(logging.WARNING, logger="gula.events"):
        assert bus.emit("some.unheard.event", {"a": 1}) == 0
        assert bus.emit("some.unheard.event", {"a": 2}) == 0
        assert bus.emit("another.unheard.event", {}) == 0

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 2, (
        "expected one warning per event name, not per emission: "
        f"{[r.getMessage() for r in warnings]}"
    )
    assert "no subscriber" in warnings[0].getMessage()
    assert "some.unheard.event" in warnings[0].getMessage()


def test_a_subscribed_emission_does_not_warn(caplog):
    """The control that keeps the warning from being noise once a subscriber
    exists, and proves the warning is conditional rather than unconditional."""
    from app.core.events import EventBus

    bus = EventBus()
    received = []
    bus.subscribe("heard.event", received.append)
    with caplog.at_level(logging.WARNING, logger="gula.events"):
        assert bus.emit("heard.event", {"x": 1}) == 1

    assert received == [{"x": 1}]
    assert [r for r in caplog.records if r.levelno == logging.WARNING] == []


def test_the_outbox_counts_a_zero_handler_dispatch_as_undelivered(caplog):
    """End to end through the real worker against a real row."""
    import json

    from app.core.events import EventBus
    from app.models.outbox import OutboxEvent
    from app.services.outbox_service import OutboxWorker

    from unittest.mock import patch

    import app.database as database
    from app.national.base import NationalBase
    from app.orm_topology import own_tables
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    import app.models.outbox  # noqa: F401
    import app.national.domain  # noqa: F401

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    NationalBase.metadata.create_all(engine, tables=own_tables(NationalBase))
    database.Base.metadata.create_all(engine, tables=own_tables(database.Base))
    session = sessionmaker(bind=engine)()
    try:
        session.add(
            OutboxEvent(
                event_type="result.critical",
                aggregate_type="result",
                aggregate_id=1,
                payload=json.dumps({"result_id": 1}),
                status="pending",
                attempts=0,
            ),
        )
        session.commit()

        with patch("app.services.outbox_service.events", EventBus()):
            with caplog.at_level(logging.WARNING, logger="gula.outbox"):
                summary = OutboxWorker.run_once(session)

        assert summary["undelivered"] == 1
        assert summary["processed"] == 1  # it was dispatched; nobody listened
        assert summary["failed"] == 0

        row = session.query(OutboxEvent).one()
        assert row.status == "done", (
            "a zero-handler dispatch must not be re-queued: there is nothing to "
            "retry against, and a new terminal status would escape "
            "purge_old_events and grow the table without bound"
        )

        messages = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
        assert any("reached 0 " in m and "nothing acted on it" in m for m in messages), messages
    finally:
        session.close()


def test_purge_still_reaches_every_terminal_row():
    """The reason the status was left alone, asserted rather than assumed: the
    purge deletes only 'done' and 'failed', so any new terminal value would
    accumulate for ever."""
    import inspect

    from app.services.outbox_service import purge_old_events

    source = inspect.getsource(purge_old_events)
    assert "status IN ('done', 'failed')" in source
    terminal_statuses = {"done", "failed"}
    worker_source = inspect.getsource(
        __import__("app.services.outbox_service", fromlist=["OutboxWorker"]).OutboxWorker,
    )
    assigned = set(re.findall(r'event\.status = "([a-z_]+)"', worker_source))
    assert assigned - {"processing"} <= terminal_statuses, (
        f"the worker now assigns {sorted(assigned)} but the purge only removes "
        f"{sorted(terminal_statuses)}"
    )


# ── the overstated claims, now stated in scope ──────────────────────────────


def test_the_docstrings_no_longer_promise_delivery_the_platform_cannot_make():
    outbox_service = (_BACKEND_APP / "services" / "outbox_service.py").read_text()
    outbox_model = (_BACKEND_APP / "models" / "outbox.py").read_text()
    results_route = (_BACKEND_APP / "routes" / "test_results.py").read_text()

    assert "zero** subscribers" in outbox_service or "zero subscribers" in outbox_service
    assert 'summary["undelivered"]' in outbox_service
    assert "at-least-once *hand-off to the in-process EventBus*" in outbox_model
    assert "It does not guarantee that anything acts on the event" in outbox_model
    assert "this event currently has no subscriber" in results_route
    assert "clinical policy and is deliberately not invented here" in results_route
