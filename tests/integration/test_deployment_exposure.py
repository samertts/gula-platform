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
