"""NR-142 — nothing this repository builds may publish on a wildcard interface.

WHY THIS EXISTS
---------------
``docker-compose.full.yml`` published eight of our own services on every
interface of the host: ``"8001:8000"`` through ``"8006:8000"``, ``"8010:8000"``
and ``"9000:9000"``. None of them authenticates anything. ``GET /patients``
on the patient service takes an optional ``lab_id`` query parameter and, when
it is omitted, returns every patient row in ``labdb`` -- the same database the
monolith serves -- with no caller identity anywhere on the path.

They are not behind the gateway either: ``config/nginx/conf.d/api.conf``
proxies to ``gula_backend`` and ``gula_frontend`` and to nothing else. So the
published port was the entire perimeter, and the platform's own stated rule --
"The backend never exposes a public port itself. All traffic enters through the
gateway." -- was true of the backend and of nothing beside it.

WHAT THIS ASSERTS
-----------------
The rule that was already being followed everywhere it was followed at all:
a service built from this repository binds its published ports to 127.0.0.1.
``build:`` is the discriminator on purpose -- it is what makes a service ours,
it needs no allow-list to maintain, and a service added tomorrow is covered by
it without anyone remembering to come back here.

This is containment, not authorization. It narrows who can reach an
unauthenticated clinical surface; it does not give that surface a caller.
The control itself is the subject of
``docs/adr/ADR-028-services-tree-disposition.md``.

NR-143 WIDENED IT
-----------------
The same file published the third-party stack the same way: ``vault`` on 8200,
``keycloak`` on 8081, ``clickhouse``, ``kafka``, ``minio``, ``ollama``,
``node-exporter``, and the whole observability group. That was not a judgement
call either -- ``docker-compose.yml`` states the rule for the same services:

    MONITORING (Prometheus + Alertmanager + Grafana)
    Internal only -- no external port exposure. Access via SSH tunnel:
      ssh -L 9090:localhost:9090 -L 9093:localhost:9093 -L 3000:localhost:3000 user@server

and gives Prometheus ``expose: "9090"`` with no host publish. That tunnel
forwards to localhost ON THE REMOTE HOST, which is exactly what a loopback
binding serves, so ``full.yml`` was drifting from a rule the repository
already had.

NR-145 is the last one: HAProxy's stats page in ``docker-compose.scale.yml``
was annotated "internal only in production" on the very line that published it
on every interface, and the page behind it carries
``stats auth admin:${HAPROXY_STATS_PASS:-gulaadmin}`` -- a default credential.
Its binding now matches its comment. The default credential is recorded, not
changed: removing the fallback yields an empty password rather than a closed
door, and that needs a person.
"""
from __future__ import annotations

import pathlib

import pytest
import yaml

REPO = pathlib.Path(__file__).resolve().parents[2]
COMPOSE_FILES = sorted(REPO.glob("docker-compose*.yml"))

#: A published port may bind here, and nowhere else.
LOOPBACK = "127.0.0.1"


def _published(spec: dict) -> list[str]:
    """The `ports:` entries of a service, as written."""
    ports = spec.get("ports") or []
    return [p for p in ports if isinstance(p, str)]


def _built_services(path: pathlib.Path):
    """(name, spec) for every service this repository builds from source."""
    document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    services = document.get("services") or {}
    for name, spec in services.items():
        if isinstance(spec, dict) and "build" in spec:
            yield name, spec


def test_compose_files_are_present():
    """A guard that silently matches nothing guards nothing."""
    assert COMPOSE_FILES, "no docker-compose*.yml found at the repository root"


@pytest.mark.parametrize("path", COMPOSE_FILES, ids=lambda p: p.name)
def test_built_services_publish_only_on_loopback(path: pathlib.Path):
    offenders = [
        (name, port)
        for name, spec in _built_services(path)
        for port in _published(spec)
        if not port.startswith(f"{LOOPBACK}:")
    ]
    assert not offenders, (
        f"{path.name}: these services are built from this repository and "
        f"publish on every interface of the host, outside the gateway: "
        f"{offenders}. Bind them to {LOOPBACK} (see NR-142)."
    )


def test_the_eight_services_that_caused_this_are_bound():
    """The specific regression, named, so a revert cannot pass quietly."""
    full = REPO / "docker-compose.full.yml"
    if not full.exists():                      # pragma: no cover - file is tracked
        pytest.skip("docker-compose.full.yml is not present")

    expected = {
        "lab-service": "127.0.0.1:8001:8000",
        "patient-service": "127.0.0.1:8002:8000",
        "order-service": "127.0.0.1:8003:8000",
        "result-service": "127.0.0.1:8004:8000",
        "sample-service": "127.0.0.1:8005:8000",
        "notification-service": "127.0.0.1:8006:8000",
        "autonomous-manager": "127.0.0.1:8010:8000",
        "ai-service": "127.0.0.1:9000:9000",
    }
    document = yaml.safe_load(full.read_text(encoding="utf-8")) or {}
    services = document.get("services") or {}

    missing = sorted(set(expected) - set(services))
    assert not missing, f"services disappeared from the compose file: {missing}"

    for name, binding in expected.items():
        assert binding in _published(services[name]), (
            f"{name} no longer publishes {binding}; it serves patient data "
            f"with no authentication and must not leave loopback (NR-142)"
        )


def test_the_gateway_still_fronts_only_the_backend_and_frontend():
    """The premise of the fix: these services have no gateway in front of them.

    If a reverse-proxy route to one of them is ever added, the loopback binding
    stops being the perimeter and this finding needs reopening -- so the
    premise is asserted rather than assumed.
    """
    conf = REPO / "config" / "nginx" / "conf.d" / "api.conf"
    if not conf.exists():                      # pragma: no cover - file is tracked
        pytest.skip("gateway configuration is not present")

    text = conf.read_text(encoding="utf-8")
    for service in ("lab-service", "patient-service", "order-service",
                    "result-service", "sample-service", "notification-service",
                    "autonomous-manager", "ai-service"):
        assert service not in text, (
            f"{service} is now proxied by the gateway; loopback binding is no "
            f"longer the perimeter and NR-142 must be re-assessed"
        )


# ─── NR-143 / NR-145: the rule beyond the services we build ─────────────────

#: The one published port that is meant to face the world, and why.
#: HAProxy is the load balancer; the listener it fronts is the whole point of
#: the scale deployment, and LB_PORT is deliberately configurable. Every other
#: published port in this repository is an internal surface.
PUBLIC_BY_DESIGN = {("docker-compose.scale.yml", "haproxy", "${LB_PORT:-8080}:80")}


@pytest.mark.parametrize("path", COMPOSE_FILES, ids=lambda p: p.name)
def test_every_published_port_is_loopback_or_public_by_design(path: pathlib.Path):
    """Not just the services we build -- vault and the stats page counted too."""
    document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    offenders = [
        (name, port)
        for name, spec in (document.get("services") or {}).items()
        if isinstance(spec, dict)
        for port in _published(spec)
        if not port.startswith(f"{LOOPBACK}:")
        and (path.name, name, port) not in PUBLIC_BY_DESIGN
    ]
    assert not offenders, (
        f"{path.name}: published on every interface of the host: {offenders}. "
        f"Bind to {LOOPBACK}, or add to PUBLIC_BY_DESIGN with the reason "
        f"(see NR-143)."
    )


def test_the_public_exception_is_still_the_only_one():
    """An allow-list nobody checks is an allow-list that grows.

    If HAProxy's front door is ever bound or removed, this fails rather than
    letting a stale exemption sit there covering something else later.
    """
    found = {
        (path.name, name, port)
        for path in COMPOSE_FILES
        for name, spec in ((yaml.safe_load(path.read_text(encoding="utf-8")) or {})
                           .get("services") or {}).items()
        if isinstance(spec, dict)
        for port in _published(spec)
        if not port.startswith(f"{LOOPBACK}:")
    }
    assert found == PUBLIC_BY_DESIGN, (
        f"the set of world-facing published ports changed: "
        f"added {sorted(found - PUBLIC_BY_DESIGN)}, "
        f"removed {sorted(PUBLIC_BY_DESIGN - found)}"
    )


def test_the_haproxy_stats_page_stays_on_loopback():
    """NR-145, named. It is an admin surface with a default credential."""
    scale = REPO / "docker-compose.scale.yml"
    if not scale.exists():                     # pragma: no cover - file is tracked
        pytest.skip("docker-compose.scale.yml is not present")

    document = yaml.safe_load(scale.read_text(encoding="utf-8")) or {}
    haproxy = (document.get("services") or {}).get("haproxy")
    assert haproxy is not None, "the haproxy service disappeared from the scale file"
    assert "127.0.0.1:8404:8404" in _published(haproxy), (
        "the HAProxy stats page is published off loopback; it is reachable with "
        "`stats auth admin:${HAPROXY_STATS_PASS:-gulaadmin}` (NR-145)"
    )
