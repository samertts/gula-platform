"""No route may reach its handler without authentication unless it is declared public.

Measured, not assumed: every route's resolved FastAPI dependency tree was walked and
then every parameter-free mutating route was called with no credentials. 46 were
correctly refused; 35 reached past authentication. Most of those are public by
design — login, logout, registration, password reset, SAML ACS, a disabled webhook
— and ``POST /niam/accounts/`` correctly answers 410 Gone.

The rest were defects:

* ``POST /niam/persons/`` created a national identity record (national_id_hash,
  health_id, birth date, email, phone) for any caller, and ``GET /niam/persons/{uuid}``
  read one back. Both now use ``get_current_niam_actor``, the dependency the rest of
  the NIAM API already uses.
* 28 routes in ``app/governance/routes/governance_routes.py`` had no guard, including
  ``POST /audit-events`` — unauthenticated injection into the national security audit
  trail — and ``GET /health-numbers/{health_number}`` and its history, an
  unauthenticated national health-number lookup. The module already defined
  ``admin_dep`` and ``elevated_dep`` and applied them across each family: every write
  was guarded and every read had been left open. The gaps were closed with the guard
  its own family already used, so no new authorization tier was invented.

``GET /governance/health`` is deliberately left public: it is a health check.

The first test is the executed proof. The second is the durable guard: it fails if a
route in the governance module is added without a guard and without being declared
public here, because this is a gap that is invisible in review.
"""

from __future__ import annotations

import ast
import pathlib

import pytest
from fastapi.testclient import TestClient

GOVERNANCE_ROUTES = (
    pathlib.Path(__file__).resolve().parents[2]
    / "app" / "governance" / "routes" / "governance_routes.py"
)

# Deliberately reachable without credentials, with the reason.
PUBLIC_BY_DESIGN = {
    "/health": "liveness probe",
}

# Routes proven to reach past authentication before the repair. Each must now refuse.
MUST_REFUSE = [
    ("POST", "/niam/persons/"),
    ("POST", "/governance/audit-events"),
    ("GET", "/governance/audit-events"),
    ("GET", "/governance/national-tests"),
    ("GET", "/governance/clinical-policies"),
    ("GET", "/governance/interop-protocols"),
    ("GET", "/governance/terminology-mappings"),
    ("GET", "/governance/connectors"),
    ("GET", "/governance/laboratories"),
    ("GET", "/governance/workers/ranking"),
]


@pytest.fixture(scope="module")
def client() -> TestClient:
    from app.main import app

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.mark.parametrize(("method", "path"), MUST_REFUSE)
def test_route_refuses_an_unauthenticated_caller(client: TestClient, method: str, path: str) -> None:
    response = client.request(method, path, json={})
    assert response.status_code in (401, 403), (
        f"{method} {path} reached past authentication with no credentials "
        f"(got {response.status_code}); it must refuse"
    )


def test_the_liveness_probe_stays_public(client: TestClient) -> None:
    """The one governance route that is public by design, asserted so it stays that way."""
    assert client.get("/governance/health").status_code == 200


def test_every_governance_route_declares_a_guard_or_is_public() -> None:
    """A route added without a guard is invisible in review; this is the ratchet."""
    tree = ast.parse(GOVERNANCE_ROUTES.read_text(encoding="utf-8"))
    unguarded: list[str] = []
    total = 0
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call):
                continue
            fn = dec.func
            if not (isinstance(fn, ast.Attribute)
                    and fn.attr in {"get", "post", "put", "patch", "delete"}):
                continue
            total += 1
            path = dec.args[0].value if dec.args and isinstance(dec.args[0], ast.Constant) else "?"
            if any(kw.arg == "dependencies" for kw in dec.keywords):
                continue
            if path in PUBLIC_BY_DESIGN:
                continue
            unguarded.append(f"{fn.attr.upper()} {path}")
    assert total >= 60, f"only {total} governance routes parsed; the guard would be vacuous"
    assert not unguarded, (
        "these governance routes have no authorization dependency and are not declared "
        "public; add the guard its family already uses, or declare it public with a "
        "reason in PUBLIC_BY_DESIGN:\n  " + "\n  ".join(unguarded)
    )
