"""IA-014 / IA-015 — the kernel event bus must actually be the kernel's event bus.

Two independently verified defects are pinned here.

IA-015 (fixed by this change)
    Six served ``app/national/*/api/routes.py`` dependency providers resolved the
    bus with ``kernel.event_bus if hasattr(kernel, "event_bus") else EventBus(kernel)``.
    ``Kernel`` keeps its subsystems in ``self._components`` and hands them out
    through ``get_component()``; it never assigns them as attributes. So the
    ``hasattr`` probe is False for the whole life of the process and the
    preferred branch is dead code: every one of the 115 served operations under
    those six routers built a throwaway ``EventBus`` per request, published into
    it, and dropped it when the request ended.

IA-013a (fixed by this change)
    ``EventStore`` was an unbounded ``dict``. Left unbounded, repairing IA-015
    would convert a per-request throwaway store into a process-lifetime leak on
    115 served endpoints, so the bound is a precondition for that repair, not a
    separate nicety.

IA-013 (NOT fixed — open architectural decision)
    ``publish()`` still never enqueues to ``outbox``, ``inbox``, ``retry_queue``
    or ``dead_letter_queue``, so the served ``/kernel/events/outbox`` and
    ``/kernel/events/dlq`` admin endpoints report zero no matter how many
    handlers fail. ``test_documented_gap_*`` below pins that gap deliberately so
    it cannot be closed silently. Those tests assert the *defect*: when the
    committee decides how the kernel bus should durably deliver, they must be
    inverted or deleted, and IA-013 revisited. They are not an endorsement.
"""
from __future__ import annotations

import ast
import importlib
import pathlib

import pytest
from app.kernel import Kernel
from app.kernel.event_bus.bus import EventBus
from app.kernel.event_bus.events import Event
from app.kernel.event_bus.store import EventStore

_NATIONAL_MODULES = (
    "rules_engine",
    "observability",
    "document_platform",
    "scheduling_platform",
    "background_platform",
    "search_platform",
)

_APP_ROOT = pathlib.Path(__file__).resolve().parents[2] / "app"


@pytest.fixture
def kernel():
    Kernel.reset_instance()
    k = Kernel.get_instance()
    yield k
    Kernel.reset_instance()


# ── IA-015: the root cause, and the repair ───────────────────────────────────


def test_kernel_stores_subsystems_as_components_not_attributes(kernel):
    """The root cause: register_component never creates an attribute.

    This is the kernel's actual contract, so it keeps passing after the fix.
    It is here to make the reason the hasattr probe could never fire explicit.
    """
    bus = EventBus(kernel)
    kernel.register_component("event_bus", bus)

    assert kernel.get_component("event_bus") is bus
    assert not hasattr(kernel, "event_bus"), (
        "Kernel grew an .event_bus attribute. If that is now the contract, the "
        "IA-015 finding and this test must both be revisited."
    )


# The eight modules that still carry the unsatisfiable probe. They are NOT
# repaired, and must not be: their fallback is ``None``, and their services call
# ``event_bus.emit(...)``, which the kernel EventBus does not define. Injecting a
# real bus there converts silent event loss into AttributeError on served
# clinical routes (blood bank, critical care, EMS, public health). See IA-016.
_IA016_EMIT_PROTOCOL_MODULES = (
    "app/biomedical/api/routes.py",
    "app/blood_bank/api/routes.py",
    "app/command_center/api/routes.py",
    "app/critical_care/api/routes.py",
    "app/ems/api/routes.py",
    "app/lifecycle_platform/api/routes.py",
    "app/pilot_platform/api/routes.py",
    "app/public_health/api/routes.py",
)


def _modules_probing_for_an_event_bus_attribute() -> set[str]:
    found: set[str] = set()
    for path in sorted(_APP_ROOT.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not (isinstance(node.func, ast.Name) and node.func.id == "hasattr"):
                continue
            if len(node.args) != 2:
                continue
            probed = node.args[1]
            if isinstance(probed, ast.Constant) and probed.value == "event_bus":
                found.add(str(path.relative_to(_APP_ROOT.parent)))
    return found


def test_the_hasattr_event_bus_probe_has_not_spread():
    """``hasattr(kernel, "event_bus")`` is unsatisfiable; pin where it survives.

    Kernel exposes subsystems through ``get_component()``, never as attributes,
    so every such probe is a dead branch. The six ``app/national/*`` providers
    were repaired to use ``resolve_event_bus()``. The eight listed above were
    deliberately left alone — read IA-016 before touching them, because the
    obvious one-line repair is a regression, not a fix.

    A module appearing here that is not on the list is a new dead branch.
    A module disappearing from the list is either a real repair (update the list
    and IA-016) or an unsafe one (revert it).
    """
    assert _modules_probing_for_an_event_bus_attribute() == set(
        _IA016_EMIT_PROTOCOL_MODULES,
    )


def test_documented_gap_emit_protocol_services_cannot_accept_the_kernel_bus():
    """PINS AN OPEN DEFECT (IA-016) — the two event protocols do not meet.

    The kernel EventBus offers ``publish``/``subscribe``/``unsubscribe``. The
    eight services above call ``emit``. This test asserts the mismatch so that
    anyone who "fixes" the probe in those modules sees, in a failing test, that
    the bus they would inject cannot serve the call they would enable.
    """
    assert not hasattr(EventBus, "emit"), (
        "EventBus grew an emit(); IA-016 can now be closed — repair the eight "
        "modules' probes and update _IA016_EMIT_PROTOCOL_MODULES."
    )


@pytest.mark.parametrize("module_name", _NATIONAL_MODULES)
def test_national_service_provider_reuses_the_registered_kernel_bus(
    kernel, module_name,
):
    """A served national endpoint must publish onto the kernel's own bus.

    Resolves the bus the way the dependency provider does and asserts it is the
    instance the bootloader registered — not a fresh per-request one.
    """
    registered = EventBus(kernel)
    kernel.register_component("event_bus", registered)

    module = importlib.import_module(f"app.national.{module_name}.api.routes")
    resolved = module._resolve_event_bus(kernel)

    assert resolved is registered, (
        f"{module_name} built its own EventBus instead of the kernel's. Every "
        "event it publishes is discarded when the request ends."
    )


def test_bus_resolution_still_falls_back_when_the_kernel_has_no_bus(kernel):
    """enable_event_bus=False, or a pre-boot kernel, must not raise."""
    module = importlib.import_module("app.national.search_platform.api.routes")
    assert kernel.get_component("event_bus") is None

    resolved = module._resolve_event_bus(kernel)
    assert isinstance(resolved, EventBus)


# ── IA-013a: the store must not grow without bound ───────────────────────────


def test_event_store_is_bounded():
    store = EventStore(max_events=50)
    for i in range(500):
        store.save(Event(name="probe", data={"i": i}))
    assert store.count() == 50, (
        f"EventStore held {store.count()} events after 500 saves — unbounded "
        "growth on a process-lifetime singleton."
    )


def test_event_store_evicts_the_oldest_first():
    store = EventStore(max_events=3)
    events = [Event(name="probe", data={"i": i}) for i in range(5)]
    for event in events:
        store.save(event)

    assert store.get(events[0].id) is None
    assert store.get(events[1].id) is None
    for event in events[2:]:
        assert store.get(event.id) is event
    assert [e.data["i"] for e in store.list_all()] == [2, 3, 4]


def test_event_store_resaving_an_event_id_does_not_grow_the_store():
    store = EventStore(max_events=3)
    event = Event(name="probe", data={})
    for _ in range(10):
        store.save(event)
    assert store.count() == 1


def test_event_store_default_bound_is_finite():
    store = EventStore()
    assert store.max_events > 0
    assert store.max_events < 10_000_000


def test_publishing_past_the_bound_keeps_the_bus_usable(kernel):
    bus = EventBus(kernel)
    bus.store = EventStore(max_events=10)
    seen: list[str] = []
    bus.subscribe("probe", lambda event: seen.append(event.id))

    for i in range(100):
        bus.publish(Event(name="probe", data={"i": i}))

    assert len(seen) == 100, "eviction must not interfere with dispatch"
    assert bus.store.count() == 10


# ── IA-013: the open gap, pinned so it cannot close silently ─────────────────


def test_documented_gap_publish_does_not_reach_outbox_or_dlq(kernel):
    """PINS AN OPEN DEFECT (IA-013) — invert or delete when the decision lands.

    ``publish()`` dispatches and returns. A handler that raises is logged by
    EventDispatcher and the event is not retried, not dead-lettered and not
    enqueued. This test asserts that loss so that wiring durable delivery is a
    deliberate, reviewed act rather than an accident.
    """
    bus = EventBus(kernel)

    def exploding_handler(event):
        raise RuntimeError("handler exploded")

    bus.subscribe("probe.fail", exploding_handler)
    for i in range(10):
        bus.publish(Event(name="probe.fail", data={"i": i}))

    assert bus.outbox.list_pending() == []
    assert bus.dead_letter_queue.list_all() == []
    assert bus.retry_queue.dequeue_ready() == []


def test_documented_gap_admin_endpoints_read_components_publish_never_writes(kernel):
    """PINS AN OPEN DEFECT (IA-013) — the admin endpoints cannot report trouble.

    ``/kernel/events/outbox`` returns ``len(eb.outbox.list_pending())`` and
    ``/kernel/events/dlq`` returns ``eb.dead_letter_queue.list_all()``. Because
    publish writes to neither, both are pinned at zero for the life of the
    process. The two components are therefore read-but-never-written: deleting
    them would remove the only operator-facing view of the event pipeline, which
    is why IA-013 is a decision and not a deletion.
    """
    bus = EventBus(kernel)
    assert hasattr(bus, "outbox")
    assert hasattr(bus, "dead_letter_queue")

    for i in range(25):
        bus.publish(Event(name="probe", data={"i": i}))

    assert len(bus.outbox.list_pending()) == 0
    assert len(bus.dead_letter_queue.list_all()) == 0
