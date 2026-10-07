"""The served event contract advertises 27 channels and a broker that do not exist.

IA-042 (P1, partially fixed; the rest is NEEDS_DECISION). `GET /contracts/asyncapi.json`
is unauthenticated and serves an AsyncAPI 2.6 document generated from
`EVENT_REGISTRY`. Measured against the rest of the repository:

    channels declared                                        27
    declared event names referenced anywhere outside
      backend/app/contracts/                                  0
    MQTT services in any docker-compose file or k8s manifest   0
    occurrences of "events.gula-platform.org" in the whole
      repository                                               1  (the spec itself)

Each channel carries a `subscribe` operation and a summary reading "Emitted when
...", and the document names a production broker at
`mqtts://events.gula-platform.org:8883`. An integrator -- a ministry, a partner
hospital, another vendor -- who builds against this document connects to a host
that is not deployed and subscribes to channels nothing publishes. The channel
list includes `gula.critical-alert-triggered`: a consumer that subscribes
successfully and receives nothing cannot distinguish "no critical alert occurred"
from "this platform never publishes critical alerts".

The platform's real event mechanism is elsewhere and shares no vocabulary with
this document: `emit_to_outbox()` writes rows to `outbox_events` and
`outbox_service` dispatches them in-process. Its concrete event types are
`claim_submitted`, `data_platform.golden_record.created` and
`data_platform.merge.completed`, plus whatever a caller posts to the
/national-streaming routes. None of them appears in EVENT_REGISTRY, and none of
EVENT_REGISTRY's 27 appears there.

Separately measured, and consistent with IA-013a/IA-014/IA-015 which are closed:
the in-process `kernel.event_bus.EventBus` has publishers (six national
application services, the plugin runtime SDK) and zero production subscribers;
`app/identity/events.py` defines a second bus whose three registration helpers
have no callers at all, so it has neither publisher nor subscriber. There is no
broker, so no process boundary is crossed by any event today.

What this commit changes: the document now states its own status. `info.description`
says plainly that no channel is published and neither broker is deployed, each
server carries `x-implementation-status: not-deployed`, and the info block carries
`x-implementation-status: specification-only`. Nothing was removed and no field
changed type, so a consumer's parser still sees the same document shape.

What it deliberately does NOT do, and why:
  * It does not emit the 27 events. That would mean authoring an event-driven
    architecture -- which events fire on which transition, with what payload and
    what delivery guarantee -- and inventing it to close a finding is worse than
    the finding.
  * It does not delete `servers` or the endpoint. Both are response-shape changes
    to a served contract that partner documentation may already reference, and
    choosing between "retire the claim" and "build the capability" belongs to the
    platform owner.
"""
from __future__ import annotations

import ast
import pathlib
import re

import pytest
from app.contracts.events import EVENT_REGISTRY, get_asyncapi_spec

_REPO = pathlib.Path(__file__).resolve().parents[3]
_BACKEND_APP = _REPO / "backend" / "app"
_CONTRACTS = _BACKEND_APP / "contracts"


def _python_sources_outside_contracts() -> list[pathlib.Path]:
    return [
        path
        for path in _BACKEND_APP.rglob("*.py")
        if _CONTRACTS not in path.parents and "__pycache__" not in path.parts
    ]


# ── the measurement, pinned so the gap cannot widen unnoticed ────────────────

def _string_literals_excluding_reexports(path: pathlib.Path) -> set[str]:
    """Every string constant in the module except the members of `__all__`.

    A name in `__all__` is a re-export, not an emission. The one declared name
    that occurs outside the contracts package -- "PatientMerged" -- is in the
    `__all__` of backend/app/national/events/__init__.py, re-exporting a
    same-named dataclass belonging to a different, also in-process mechanism.
    Counting that as evidence the event is published would be the mirror of a
    ratchet passing on a commented-out line, so it is excluded by structure
    rather than by name.

    A class *definition* named after an event is likewise not an emission: only
    string constants are collected, and a ClassDef's name is not one.
    """
    try:
        tree = ast.parse(path.read_text(errors="replace"))
    except SyntaxError:  # pragma: no cover - a file that cannot emit anything
        return set()

    reexported: set[int] = set()
    for node in ast.walk(tree):
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AugAssign):
            targets = [node.target]
        if any(isinstance(t, ast.Name) and t.id == "__all__" for t in targets):
            for inner in ast.walk(node):
                if isinstance(inner, ast.Constant) and isinstance(inner.value, str):
                    reexported.add(id(inner))

    return {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in reexported
    }




def test_not_one_declared_event_is_emitted_anywhere():
    """The headline measurement. If a declared event ever starts being emitted,
    this fails and whoever did it should move that name out of the unimplemented
    list below."""
    assert len(EVENT_REGISTRY) == 27, "the registry changed; re-measure the gap"

    emitted: dict[str, list[str]] = {}
    for path in _python_sources_outside_contracts():
        for literal in _string_literals_excluding_reexports(path):
            if literal in EVENT_REGISTRY:
                emitted.setdefault(literal, []).append(path.relative_to(_REPO).as_posix())

    assert emitted == {}, (
        "an event name declared in the served AsyncAPI contract now appears as a "
        f"string literal in platform code: {emitted}"
    )


def test_neither_declared_broker_is_deployed():
    """`servers` names two MQTT brokers. Nothing in the deployment configuration
    starts an MQTT broker, and the production hostname exists nowhere else in the
    repository."""
    compose_and_manifests = list(_REPO.glob("docker-compose*.yml"))
    k8s = _REPO / "k8s"
    if k8s.is_dir():
        compose_and_manifests += list(k8s.rglob("*.yaml")) + list(k8s.rglob("*.yml"))
    assert compose_and_manifests, "no deployment configuration found to check against"

    broker_mentions = [
        path.relative_to(_REPO).as_posix()
        for path in compose_and_manifests
        if re.search(r"mosquitto|mqtt", path.read_text(errors="replace"), re.IGNORECASE)
    ]
    assert broker_mentions == [], (
        f"an MQTT broker is now deployed ({broker_mentions}); re-check IA-042 -- "
        "the spec may no longer be specification-only"
    )


def test_the_real_event_vocabulary_shares_nothing_with_the_contract():
    """Two event systems, no common name. This is what makes the contract
    actively misleading rather than merely aspirational."""
    outbox_emitters = sorted(
        set(
            re.findall(
                r'emit_to_outbox\([^)]*?event_type="([^"]+)"',
                "\n".join(
                    path.read_text(errors="replace")
                    for path in _python_sources_outside_contracts()
                ),
                re.DOTALL,
            ),
        ),
    )
    assert outbox_emitters, "no outbox emitter found; the measurement is stale"
    assert set(outbox_emitters).isdisjoint(set(EVENT_REGISTRY))


# ── the fix: the document states its own status ──────────────────────────────


def test_the_spec_declares_itself_specification_only():
    spec = get_asyncapi_spec()
    assert spec["info"]["x-implementation-status"] == "specification-only"
    description = spec["info"]["description"]
    assert "SPECIFICATION ONLY" in description
    assert "outbox_events" in description, (
        "the description must point a reader at the mechanism that does work"
    )


@pytest.mark.parametrize("server", ["production", "development"])
def test_every_declared_broker_is_marked_not_deployed(server):
    spec = get_asyncapi_spec()
    entry = spec["servers"][server]
    assert entry["x-implementation-status"] == "not-deployed"
    assert "NOT DEPLOYED" in entry["description"]


def test_the_document_shape_is_unchanged():
    """Positive control: the annotation must not have broken the contract for a
    consumer that already parses it. Same top-level keys, same channel count,
    same server keys, same urls, every channel still has its subscribe operation
    and payload.
    """
    spec = get_asyncapi_spec()
    assert set(spec) == {"asyncapi", "info", "servers", "defaultContentType", "channels"}
    assert spec["asyncapi"] == "2.6.0"
    assert spec["defaultContentType"] == "application/json"
    assert set(spec["servers"]) == {"production", "development"}
    assert spec["servers"]["production"]["url"] == "mqtts://events.gula-platform.org:8883"
    assert spec["servers"]["development"]["url"] == "mqtt://localhost:1883"
    assert len(spec["channels"]) == len(EVENT_REGISTRY) == 27
    assert "gula.critical-alert-triggered" in spec["channels"]
    for name, channel in spec["channels"].items():
        assert "subscribe" in channel, name
        assert channel["subscribe"]["message"]["payload"]["type"] == "object", name


def test_the_endpoint_still_serves_it(client):
    """It is served unauthenticated, which is part of why the claim matters."""
    response = client.get("/contracts/asyncapi.json")
    assert response.status_code == 200
    body = response.json()
    assert body["info"]["x-implementation-status"] == "specification-only"
    assert len(body["channels"]) == 27


# ── the two in-process buses, measured and recorded ──────────────────────────


def test_the_identity_event_bus_has_neither_publisher_nor_subscriber():
    """`app/identity/events.py` is a complete pub/sub implementation that nothing
    imports. Recorded, not removed: deleting a module is not this finding's
    scope, and a reader who finds it should know it is inert."""
    importers = [
        path.relative_to(_REPO).as_posix()
        for path in _BACKEND_APP.rglob("*.py")
        if "__pycache__" not in path.parts
        and path != _BACKEND_APP / "identity" / "events.py"
        and ("app.identity.events" in path.read_text(errors="replace")
             or "IdentityEventBus" in path.read_text(errors="replace"))
    ]
    assert importers == [], f"IdentityEventBus is now used by {importers}; re-audit it"


def test_the_kernel_bus_has_publishers_and_no_production_subscribers():
    """Consistent with IA-014, which is closed. Pinned so a subscriber appearing
    is a deliberate, visible event rather than a silent one."""
    subscribers = []
    for path in _BACKEND_APP.rglob("*.py"):
        if "__pycache__" in path.parts or path.parts[-2:] == ("identity", "events.py"):
            continue
        text = path.read_text(errors="replace")
        if ".subscribe(" not in text:
            continue
        relative = path.relative_to(_REPO).as_posix()
        if "identity/events.py" in relative:
            continue
        subscribers.append(relative)

    # EventBusSource in the health-data streaming pipeline is the only class that
    # subscribes to the kernel bus, and nothing constructs it; mqtt_gateway and
    # messaging_connector subscribe to external brokers, not to this bus.
    expected = {
        "backend/app/health_data/streaming/pipeline.py",
        "backend/app/integration/gateway/mqtt_gateway.py",
        "backend/app/national/ecosystem/connectors/messaging_connector.py",
        "backend/app/integration/api_management/portal.py",
        "backend/app/integration/government/government_bus.py",
        "backend/app/integration/connectors/push.py",
    }
    unexpected = set(subscribers) - expected
    assert unexpected == set(), (
        f"a new .subscribe() call site appeared: {sorted(unexpected)} -- if it "
        "subscribes to the kernel EventBus, the zero-subscriber finding is stale"
    )
