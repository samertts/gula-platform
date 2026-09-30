"""IA-001 — the app/reference package takes its tenant scope from the client.

Four routes under ``app/reference/routes/`` accept ``lab_id`` as a query
parameter and pass it straight to the service layer:

    routes/patients.py:44   create_patient         lab_id: str  = Query(...)   WRITE
    routes/orders.py:27     create_order           lab_id: str  = Query(...)   WRITE
    routes/patients.py:73   search_patients        lab_id: str | None = Query(None)
    routes/results.py:75    list_critical_results  lab_id: str  = Query(...)

Two of the four are writes, so the client does not merely read another
laboratory's data -- it names the laboratory a new patient or order is filed
into. The handler names were measured from the AST, not guessed: an earlier draft
of this pin listed "list_orders" and "list_patients" and failed, which is the
reason the set is asserted rather than described in prose.

``current_user`` appears NOWHERE in the whole package, so these handlers have no
way to compare the requested laboratory against the authenticated one even in
principle. CLAUDE.md Security Invariant #1 is "All patient-data queries MUST
filter by ``lab_id = current_user.lab_id``"; here it is ``lab_id = <client
input>``, over patients, laboratory orders and critical results.

WHY THIS IS NOT CURRENTLY A BREACH, measured rather than assumed: the reference
routers are mounted nowhere. The assembled app serves 1794 paths and **0** of
them begin with ``/reference``. The three routers also each carry
``dependencies=[Depends(require_permission("system:admin"))]``, so even mounted
they would not be anonymous.

So this is a latent defect, and the danger is a future ``include_router``. These
tests are the tripwire: the first assertion fails the moment the package is
served while it still derives scope from client input, and the second keeps the
inventory of offending signatures from growing. Neither is a substitute for the
fix, which is to derive ``lab_id`` from the authenticated principal.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

_REFERENCE = pathlib.Path(__file__).resolve().parents[2] / "app" / "reference"
_TENANT_PARAMS = {"lab_id", "laboratory_id", "facility_id", "organization_id", "org_id"}

#: Signatures that take the tenant from the client today. Pinned as an exact set
#: so a new one fails, and so removing one (by deriving it from the principal)
#: also fails and forces this note to be updated with the repair.
KNOWN_CLIENT_SUPPLIED_SCOPE = {
    ("orders.py", "create_order"),            # WRITE: creates into a client-named lab
    ("patients.py", "create_patient"),        # WRITE: creates into a client-named lab
    ("patients.py", "search_patients"),       # read
    ("results.py", "list_critical_results"),  # read
}


def _client_scoped_handlers() -> set[tuple[str, str]]:
    found: set[tuple[str, str]] = set()
    for path in sorted(_REFERENCE.rglob("routes/*.py")):
        tree = ast.parse(path.read_text())
        for fn in tree.body:
            if not isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            args = fn.args.args + fn.args.kwonlyargs
            if any(a.arg in _TENANT_PARAMS for a in args):
                found.add((path.name, fn.name))
    return found


def test_the_reference_package_never_consults_the_authenticated_principal() -> None:
    """The structural reason the scope cannot be checked: there is no principal."""
    sources = [p.read_text() for p in _REFERENCE.rglob("*.py")]
    offenders = [
        p.name for p in _REFERENCE.rglob("*.py")
        if "current_user" in p.read_text() or "get_current_user" in p.read_text()
    ]
    assert sources, "app/reference has no sources; re-derive this finding"
    assert offenders == [], (
        "app/reference now reads the principal somewhere: that is the repair this "
        f"finding asks for, so update IA-001 and this pin. Files: {offenders}"
    )


def test_the_set_of_client_scoped_reference_handlers_has_not_grown() -> None:
    assert _client_scoped_handlers() == KNOWN_CLIENT_SUPPLIED_SCOPE, (
        "the reference package's client-supplied tenant scope changed. A new entry "
        "is a new latent tenant-isolation hole; a removed entry means it was fixed "
        "and IA-001 should be closed."
    )


def test_the_reference_routers_are_not_served_while_scope_comes_from_the_client() -> None:
    """The tripwire. Mounting this package as-is makes IA-001 live.

    Asserted against the served OpenAPI surface, not against ``app.routes``: the
    platform mounts through a lazy ``_IncludedRouter`` wrapper, so a flat scan of
    ``app.routes`` reports nothing useful and reading one would be how this test
    passes while the routes are in fact served.
    """
    import app.main as main

    served = sorted(p for p in main.app.openapi()["paths"] if p.startswith("/reference"))
    if not served:
        return
    pytest.fail(
        "app/reference is now served while it still derives lab_id from client "
        f"input, which makes IA-001 a live cross-tenant read over patients, "
        f"orders and critical results. Served: {served}"
    )
