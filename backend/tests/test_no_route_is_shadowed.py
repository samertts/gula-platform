"""NR-099 — literal routes declared after a parameterised sibling are unreachable.

Starlette resolves routes in declaration order. `GET /pharmacy/drugs/{drug_id}`
matches `/pharmacy/drugs/search`, so a `GET /pharmacy/drugs/search` declared
later never runs: the request lands in `get_drug` with `drug_id="search"`.

Thirty routes across thirteen modules are in that state. Confirmed not by
re-implementing the matcher but by asking the application's own: for each, the
route the app selects is the parameterised sibling, not the intended handler.

This is a correctness and availability defect rather than a security one --
measured: on all thirty pairs the swallowing handler's dependency set is equal
to or stricter than the intended handler's, so none of them weakens
authorization. What it does is make thirty endpoints dead, several of which
have live frontend callers (PublicHealthApiPage calls
/public-health/disease-cases/stats; useApi.ts calls /hospital/occupancy and
/hospital/appointments).

Fixing the order ACTIVATES a handler that has never served a request, which is
the trap NR-098 names: a path that is safe only because it is broken. So each
entry leaves this ledger only once its handler has been shown to scope its
reads to the caller's tenant. The ledger may shrink and may never grow.
"""

from __future__ import annotations

import pytest
from app.factory import create_app
from fastapi.routing import APIRoute


@pytest.fixture(scope="module")
def flat_routes():
    app = create_app()
    out: list[APIRoute] = []

    def walk(container) -> None:
        for r in getattr(container, "routes", []):
            if isinstance(r, APIRoute):
                out.append(r)
            elif hasattr(r, "original_router"):
                walk(r.original_router)
            else:
                walk(r)

    walk(app)
    return out


def _shadowed(routes: list[APIRoute]) -> list[tuple[APIRoute, APIRoute]]:
    """(intended, swallower) for every literal route an earlier pattern matches."""
    found = []
    for i, r in enumerate(routes):
        if "{" in r.path:
            continue
        for earlier in routes[:i]:
            if "{" not in earlier.path or not (r.methods & earlier.methods):
                continue
            if earlier.path_regex.match(r.path):
                found.append((r, earlier))
                break
    return found


#: Shadowed routes as measured on 2026-09-17. MAY SHRINK, MAY NEVER GROW.
#: Remove an entry only together with the declaration reorder that fixes it,
#: and only after confirming the newly reachable handler scopes to the caller's
#: tenant.
DECLARED_SHADOWED = frozenset({
    "GET /certificates/authorities",
    "GET /certificates/expiring",
    "GET /governance/workers/ranking",
    "GET /national/documents/categories",
    "GET /national/documents/health",
    "GET /national/jobs/dashboard",
    "GET /national/jobs/due",
    "GET /national/jobs/health",
    "GET /national/jobs/stats",
    "GET /national/notifications/channels",
    "GET /national/notifications/health",
    "GET /national/notifications/preferences",
    "GET /national/notifications/schedules",
    "GET /national/notifications/stats",
    "GET /national/notifications/templates",
    "GET /national/observability/traces/search",
    "GET /national/rules/categories",
    "GET /national/rules/health",
    "GET /national/tasks/health",
    "GET /national/tasks/overdue",
    "GET /national/tasks/pending",
    "GET /national/tasks/queues",
    "GET /national/tasks/sla-definitions",
    "GET /national/tasks/stats",
    "GET /public-health/disease-cases/stats",
})

#: Guard the guard. If the scan stops finding routes at all it must fail rather
#: than pass vacuously -- the first version of this scan returned zero because
#: this FastAPI mounts included routers as `_IncludedRouter` rather than
#: flattening them, and zero looked like good news.
MINIMUM_ROUTES_SCANNED = 1800


def test_the_scan_actually_sees_the_route_table(flat_routes):
    assert len(flat_routes) >= MINIMUM_ROUTES_SCANNED, (
        f"only {len(flat_routes)} routes flattened, expected at least "
        f"{MINIMUM_ROUTES_SCANNED}. The walk is not reaching the route table, so "
        "every other assertion in this file would pass vacuously."
    )
    assert any("{" in r.path for r in flat_routes), "no parameterised routes found"
    assert any("{" not in r.path for r in flat_routes), "no literal routes found"


def test_no_new_route_is_shadowed(flat_routes):
    current = {
        f"{','.join(sorted(r.methods & e.methods))} {r.path}"
        for r, e in _shadowed(flat_routes)
    }
    new = current - DECLARED_SHADOWED
    assert not new, (
        "these literal routes are unreachable because a parameterised route is "
        "declared before them. Move the literal declaration above the "
        "parameterised one in its router:\n  " + "\n  ".join(sorted(new))
    )


def test_the_ledger_does_not_keep_stale_entries(flat_routes):
    """A fixed route must leave the ledger, or the ceiling stops meaning anything."""
    current = {
        f"{','.join(sorted(r.methods & e.methods))} {r.path}"
        for r, e in _shadowed(flat_routes)
    }
    resolved = DECLARED_SHADOWED - current
    assert not resolved, (
        "these routes are no longer shadowed and must be removed from "
        "DECLARED_SHADOWED:\n  " + "\n  ".join(sorted(resolved))
    )


def test_shadowing_never_weakens_authorization(flat_routes):
    """The reason this is P2 and not P1. If that ever stops holding, it is P1."""

    def security_deps(route: APIRoute) -> set[str]:
        names: set[str] = set()

        def rec(dep) -> None:
            if dep.call is not None:
                names.add(getattr(dep.call, "__name__", str(dep.call)))
            for sub in dep.dependencies:
                rec(sub)

        for dep in route.dependant.dependencies:
            rec(dep)
        return {
            n for n in names
            if any(k in n.lower() for k in (
                "user", "auth", "permission", "require", "role",
                "token", "current", "actor", "tenant", "scope", "admin",
            ))
        }

    weakened = []
    for intended, swallower in _shadowed(flat_routes):
        wanted, actual = security_deps(intended), security_deps(swallower)
        if not actual >= wanted:
            weakened.append(
                f"{intended.path}: intended {sorted(wanted)} but "
                f"{swallower.path} enforces only {sorted(actual)}"
            )
    assert not weakened, (
        "a shadowed route is served by a handler with weaker authorization than "
        "the route the caller addressed. This is no longer a correctness defect:\n  "
        + "\n  ".join(weakened)
    )
