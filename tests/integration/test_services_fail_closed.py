"""NR-142 — the `services/` tree refuses every request it cannot attribute.

ADR-028 classified this tree DORMANT. Dormant describes maintenance, not safety:
the eight services performed **no authentication and no authorization of any
kind** while issuing raw asyncpg INSERT and SELECT against `labdb` -- the same
database the monolith serves. NR-143 moved their published ports to loopback,
and that is containment, not a fix; a bound port is a deployment property that
the next compose file undoes.

`services/fail_closed.py` closes the safety half without prejudging the
disposition. This proves it by driving the real apps.

WHY A POSITIVE CONTROL IS NOT OPTIONAL HERE
-------------------------------------------
A perimeter that refuses *everything* would satisfy every denial assertion below
while breaking the container lifecycle -- Docker's HEALTHCHECK polls `/health`,
so a service that refuses it never becomes healthy and the failure reads as an
outage rather than a deliberate refusal. `test_liveness_still_answers` is the
control that tells those two apart.
"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest

SERVICES_ROOT = Path(__file__).resolve().parents[2] / "services"

#: Each service, and one data route that reaches `labdb` in its handler. These
#: are the paths that had no caller, no tenant and no audit.
DATA_ROUTES: dict[str, tuple[str, str]] = {
    "lab": ("GET", "/laboratories"),
    "patient": ("GET", "/patients"),
    "order": ("GET", "/orders"),
    "result": ("GET", "/results"),
    "sample": ("GET", "/samples"),
}


_APPS: dict[str, object] = {}


def _require_service_runtime() -> None:
    """Skip -- visibly -- where a service's own runtime dependencies are absent.

    The eight `main.py` modules import `asyncpg` and `prometheus_client` at module
    scope. Neither is in any requirements file in this repository; both come from
    the `pip install` line in each service Dockerfile, so a checkout that has not
    installed them cannot import the apps at all.

    A skip here is a SKIP, not a pass. Where these are missing, the behavioural
    half of NR-142 is unproven and only `test_d` -- which reads source and needs
    no import -- still runs. That is stated rather than papered over, because a
    silently-degraded suite is how a perimeter stops being checked.
    """
    pytest.importorskip("fastapi")
    pytest.importorskip("asyncpg", reason="service runtime dependency (see Dockerfile)")
    pytest.importorskip(
        "prometheus_client", reason="service runtime dependency (see Dockerfile)",
    )


def _load_service_app(name: str):
    """Import a service's FastAPI app the way its container does, once.

    Memoised because each `main.py` registers its Prometheus counters on the
    process-global default `CollectorRegistry`; importing the same service a
    second time raises `DuplicateTimeseries`. That is a property of the services,
    not of the perimeter, so the harness works around it rather than the
    middleware being blamed for it.

    The Dockerfile copies `<name>/main.py` and `fail_closed.py` side by side into
    /app and runs `uvicorn main:app`, so both resolve as top-level modules. That
    layout is reproduced here rather than imported as a package.

    `fail_closed.py` is deliberately flat rather than living in
    `services/shared/`. The Dockerfile does `COPY shared /app/shared`, so inside
    the container `import shared` resolves to that shim -- whose `audit.py` then
    does `from shared.audit import AuditService, ...`, i.e. itself, and raises
    `ImportError: cannot import name 'AuditService' from partially initialized
    module 'shared.audit'`. Measured, not assumed: the same sys.path reproduces
    it here. A perimeter reached through that package would fail closed by
    crashing at container start, which is not the same thing as refusing.
    """
    # These modules read DATABASE_URL at import time. It is pointed at a port
    # nothing listens on, deliberately: if the perimeter ever let a request
    # through to a handler, the connection attempt would fail loudly instead of
    # quietly succeeding. Nothing here ever opens it, which is the point.
    # `DATABASE_URL` and `RABBITMQ_URL` are the only two (measured across all
    # eight `main.py`). Both point at a port nothing listens on.
    os.environ.setdefault(
        "DATABASE_URL", "postgresql://nr142-probe@127.0.0.1:1/unreachable",
    )
    os.environ.setdefault("RABBITMQ_URL", "amqp://nr142-probe@127.0.0.1:1//")

    if name in _APPS:
        return _APPS[name]

    added = [str(SERVICES_ROOT), str(SERVICES_ROOT / name)]
    for path in added:
        if path not in sys.path:
            sys.path.insert(0, path)
    for module in ("main", "fail_closed"):
        sys.modules.pop(module, None)
    try:
        _APPS[name] = importlib.import_module("main").app
        return _APPS[name]
    finally:
        sys.modules.pop("main", None)
        for path in added:
            if path in sys.path:
                sys.path.remove(path)


@pytest.mark.parametrize("service", sorted(DATA_ROUTES))
def test_a_data_routes_are_refused_without_a_caller(service):
    """The finding. Every one of these reached labdb with no identity at all."""
    _require_service_runtime()
    from fastapi.testclient import TestClient

    method, path = DATA_ROUTES[service]
    client = TestClient(_load_service_app(service), raise_server_exceptions=False)

    response = client.request(method, path)
    assert response.status_code == 503, (
        f"{service} served {method} {path} with status {response.status_code} to a "
        "caller it cannot identify; this route reaches labdb (NR-142)"
    )
    assert response.json()["code"] == "SERVICE_HAS_NO_CALLER_IDENTITY"


@pytest.mark.parametrize("service", sorted(DATA_ROUTES))
def test_b_liveness_still_answers(service):
    """The positive control.

    Without this, a middleware that refused `/health` too would pass every
    assertion above while making the services undeployable. `/health` returns a
    fixed string and touches no database, no tenant and no patient.
    """
    _require_service_runtime()
    from fastapi.testclient import TestClient

    client = TestClient(_load_service_app(service), raise_server_exceptions=False)
    response = client.get("/health")

    assert response.status_code == 200, (
        f"{service} refuses its own liveness probe, so Docker's HEALTHCHECK can "
        "never pass and the refusal reads as an outage"
    )
    assert response.json()["status"] == "healthy"


def test_c_a_write_is_refused_before_it_reaches_the_database():
    """The sharpest instance, stated separately because it is the reason.

    `POST /patients` took a body and INSERTed it into labdb under no caller. A
    read leaking is bad; an unattributable clinical write is worse, because the
    row survives and nothing records who made it.
    """
    _require_service_runtime()
    from fastapi.testclient import TestClient

    client = TestClient(_load_service_app("patient"), raise_server_exceptions=False)
    response = client.post(
        "/patients",
        json={"full_name": "NR-142 probe", "phone": "07700000000", "gender": "M"},
    )

    # 503 and not 422: the refusal must happen before the body is even validated,
    # or the service is still telling an anonymous caller about its schema.
    assert response.status_code == 503, (
        f"POST /patients answered {response.status_code}; an unauthenticated write "
        "path to labdb is the whole of NR-142"
    )
    assert response.json()["code"] == "SERVICE_HAS_NO_CALLER_IDENTITY"


def test_d_every_service_carries_the_perimeter():
    """The ratchet.

    The five services above are the ones with a data route this test can drive.
    All eight ship the middleware, and a ninth service added without it would be
    the defect returning. Read from source, so a service that cannot even import
    is still covered.
    """
    expected = {
        "lab", "patient", "order", "result",
        "sample", "notification", "ai", "autonomous_manager",
    }
    def _live_lines(text: str) -> list[str]:
        """Non-comment lines only.

        A substring search would accept `# app.add_middleware(FailClosedMiddleware)`
        -- commenting the attachment out left this test green while the service
        served data again, which the negative proof caught. The comment marker is
        exactly the kind of thing that makes a ratchet look like a control while
        being none.
        """
        return [ln for ln in text.splitlines() if not ln.lstrip().startswith("#")]

    missing_attach, missing_ship = [], []
    for name in sorted(expected):
        main = _live_lines((SERVICES_ROOT / name / "main.py").read_text(encoding="utf-8"))
        dockerfile = _live_lines((SERVICES_ROOT / name / "Dockerfile").read_text(encoding="utf-8"))
        if not any("app.add_middleware(FailClosedMiddleware)" in ln for ln in main):
            missing_attach.append(name)
        if not any("COPY fail_closed.py ." in ln for ln in dockerfile):
            missing_ship.append(name)

    assert not missing_attach, f"these services do not attach the perimeter: {missing_attach}"
    assert not missing_ship, (
        f"these Dockerfiles do not ship fail_closed.py, so the import fails at "
        f"container start rather than refusing deliberately: {missing_ship}"
    )
