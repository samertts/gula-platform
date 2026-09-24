"""NR-127/NR-128. The whole served surface is behind one trusted context.

This is the regression test for the trust boundary itself, not for any one
endpoint. It enumerates what the app actually serves and asserts two things
about every operation on it:

  * without a server-established caller identity it is refused, and
  * headers a client controls do not change that answer.

The surface is read from ``app.openapi()`` rather than by walking router
objects. ``include_router`` leaves wrapper entries in ``app.routes`` whose
``path`` and ``methods`` are ``None``; enumerating those yields a phantom
surface that agrees with whatever you assert about it. The OpenAPI document is
built from what is actually mounted and served.
"""
from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# The app opens its database at import time. Point it somewhere disposable so
# importing it here never leaves a stray nhop.db in the working tree.
os.environ.setdefault(
    "NHOP_DATABASE_URL",
    "sqlite:///" + tempfile.mkdtemp(prefix="nhop-trust-boundary-") + "/probe.db",
)

# These two imports must stay BELOW the line above: importing app.main opens
# the database, so the URL has to be set first. Do not hoist them.
from app.core.trusted_context import _UNAVAILABLE_DETAIL
from app.main import app

#: A path-parameter value that is acceptable to every parameter type in use
#: (all of them are strings or UUIDs today). If a future route takes an int
#: path parameter this placeholder stops matching and the operation answers
#: 422 instead of 503 -- which fails the sweep loudly rather than silently
#: skipping that route.
_PLACEHOLDER = "00000000-0000-0000-0000-000000000000"

#: Floor on the served surface. The sweep tests below are vacuously true over
#: an empty list, so an enumeration that silently stops working would look
#: like a pass. This is the positive control for the enumeration itself.
_MINIMUM_V1_OPERATIONS = 14

#: Headers that used to be the entire authority model: whoever sent them was
#: whoever they claimed to be. They must now be inert.
_FORGED = {
    "X-Role": "MINISTRY",
    "X-Actor-Role": "MINISTRY",
    "X-Actor-Id": "attacker",
    "X-User-Id": "attacker",
    "X-Lab-Id": _PLACEHOLDER,
}

_HEADER_SOURCES = re.compile(
    r"""Header\s*\(|request\.headers|headers\.get\s*\(\s*["']x-""",
    re.IGNORECASE,
)

_APP_ROOT = Path(__file__).resolve().parent.parent / "app"


def _v1_operations() -> list[tuple[str, str]]:
    """Every (method, path) the app serves under /v1, as served."""
    return sorted(
        (method.upper(), path)
        for path, operations in app.openapi()["paths"].items()
        if path.startswith("/v1")
        for method in operations
    )


def _call(client: TestClient, method: str, path: str, **kwargs):
    url = re.sub(r"\{[^}]+\}", _PLACEHOLDER, path)
    # A body is sent on every write so that body parsing, which happens before
    # dependencies are solved, cannot be what rejects the request. The refusal
    # has to come from the trust boundary.
    if method in {"POST", "PUT", "PATCH"}:
        kwargs.setdefault("json", {})
    return client.request(method, url, **kwargs)


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_the_sweep_actually_sees_the_served_surface():
    operations = _v1_operations()
    assert len(operations) >= _MINIMUM_V1_OPERATIONS, (
        "The /v1 surface enumeration returned "
        f"{len(operations)} operations, fewer than the {_MINIMUM_V1_OPERATIONS} "
        "known to be mounted. Either routes were removed -- lower this floor "
        "deliberately -- or the enumeration broke, in which case the sweeps "
        "below are passing over nothing."
    )


def test_health_is_still_served(client: TestClient):
    """Positive control: a dead app refuses everything and looks contained."""
    response = client.get("/health")
    assert response.status_code == 200, response.text
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize(("method", "path"), _v1_operations())
def test_no_v1_operation_is_served_without_a_trusted_context(
    client: TestClient, method: str, path: str
):
    response = _call(client, method, path)
    assert response.status_code == 503, (
        f"{method} {path} answered {response.status_code}, not 503. Every route "
        "that acts on a caller's behalf must be refused while NHOP has no "
        "federated identity provider."
    )
    assert response.json()["detail"] == _UNAVAILABLE_DETAIL


@pytest.mark.parametrize(("method", "path"), _v1_operations())
def test_forged_identity_headers_change_nothing(
    client: TestClient, method: str, path: str
):
    """The old authority model, replayed against the new boundary."""
    plain = _call(client, method, path)
    forged = _call(client, method, path, headers=_FORGED)
    assert forged.status_code == plain.status_code == 503
    assert forged.json() == plain.json(), (
        f"{method} {path} answered differently when the caller supplied "
        f"identity headers. Those headers must carry no authority."
    )


def test_no_module_derives_identity_from_the_request_headers():
    """The defect class, not one instance of it.

    NR-127 was six separate reads of client-supplied identity across five
    modules. Containment at the router keeps those reads from being reachable,
    but a future handler could reintroduce one and quietly re-open the hole
    for its own route. Nothing under app/ may read identity off the wire; the
    only source is app.core.trusted_context.
    """
    offenders = {
        str(source.relative_to(_APP_ROOT)): [
            line.strip()
            for line in source.read_text(encoding="utf-8").splitlines()
            if _HEADER_SOURCES.search(line)
        ]
        for source in sorted(_APP_ROOT.rglob("*.py"))
    }
    offenders = {name: lines for name, lines in offenders.items() if lines}
    assert offenders == {}, (
        "These modules read identity off the wire again. Authority comes from "
        f"app.core.trusted_context.current_context() and nowhere else: {offenders}"
    )


def test_the_header_scan_can_actually_find_a_header_read(tmp_path: Path):
    """Positive control: a matcher that matches nothing reports a clean repo."""
    planted = tmp_path / "regression.py"
    planted.write_text(
        'def handler(x_role: str = Header(None)):\n'
        '    return request.headers.get("x-actor-id")\n',
        encoding="utf-8",
    )
    hits = [
        line
        for line in planted.read_text(encoding="utf-8").splitlines()
        if _HEADER_SOURCES.search(line)
    ]
    assert len(hits) == 2, hits
