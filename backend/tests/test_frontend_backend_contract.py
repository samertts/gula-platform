"""NR-054 — the frontend may only offer what the backend actually registers.

Nine routes under `/capabilities/*` shipped with pages, navigation entries and a
`dashboard:read` gate, and each called `GET /<capability>` — a router under
`backend/app/capabilities/` that `factory.py` never includes. Every one answered
404 while the navigation presented it as a working feature.

The cause was not a typo. `scripts/zero_drift_engine.py` generates pages from
`docs/api/backend_inventory.json`, and that inventory catalogues backend **route
files**, not **registered routes** — so defining an `APIRouter` was enough to
put a feature in front of a user, whether or not the application ever mounted
it.

These tests compare the frontend's API calls against the application's real
OpenAPI schema, which is the only artifact that knows what is actually
reachable.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
FRONTEND_SRC = REPO / "frontend-v3" / "src"

# The eight capabilities with no registered backend contract and no unambiguous
# canonical owner. They stay out of the router and out of NAV_ITEMS until one
# exists. See frontend-v3/src/pages/capabilities/README.md.
DISABLED_CAPABILITIES = (
    "clinical-foundation",
    "document-management",
    "healthcare-consent",
    "provider-management",
    "reporting-service",
    "search-service",
    "storage-service",
    "workflow-engine",
)

# The one capability route that survives, and the canonical endpoint it was
# bound to instead of its own stub.
ROUTED_CAPABILITY = "encounter-management"
CANONICAL_ENCOUNTERS = "/national-data/encounters"

# Literal frontend calls that do not resolve to a registered route and are NOT
# NR-054's to fix — the same defect class in other domains, recorded as NR-057.
# This ledger exists so the guard passes on today's repository while still
# failing the moment a *new* orphan appears. It may shrink, never grow.
#
# It shrank by eight on NR-122. Those /niam/* calls were never orphans: the
# backend served them one segment deeper, at /niam/niam/*, because three
# routers under app/identity repeated the prefix their parent already applied.
# Correcting the prefix made the paths the frontend had been asking for all
# along reachable, and this guard's rot check is what flagged them for removal.
DECLARED_UNREGISTERED_CALLS = frozenset({
    "/blood-bank/crossmatch/compatible-groups",
    "/certification/level",
    "/certification/report",
    "/citizen-platform/appointments",
    "/citizen-platform/dashboard",
    "/citizen-platform/health-summary",
    "/citizen-platform/lab-results",
    "/citizen-platform/medications",
    "/citizen-platform/profile",
    "/control-plane/config",
    "/health-data/lineage",
    "/lifecycle/components/name",
    "/national/notifications/delivery",
    "/niam/adaptive-auth/risk-history",
    "/niam/certificates",
    "/niam/federation/identities",
    "/niam/governance/registries",
    "/niam/lifecycle/citizen",
    "/niam/lifecycle/enterprise",
    "/niam/lifecycle/workforce",
    "/niam/trust/trust-anchors",
    "/pilot-platform/certify",
})

_CALL = re.compile(r'api\.(?:get|post|put|patch|delete)\(\s*"(/[^"]*)"')


def _is_disabled_page(path: Path) -> bool:
    """True for a page under a capability that NR-054 took out of the router."""
    parts = path.parts
    return any(
        parts[i:i + 2] == ("capabilities", capability)
        for capability in DISABLED_CAPABILITIES
        for i in range(len(parts) - 1)
    )


def _frontend_calls() -> dict[str, set[str]]:
    """Every statically resolvable `api.<method>("/literal")` in the frontend.

    Deliberately literal-only. A call built from a template literal or by
    concatenation (`api.get("/national/documents/" + id + "/versions")`) cannot
    be resolved without evaluating the expression, and guessing at it would
    manufacture failures rather than find them. Those are listed in
    `test_dynamic_calls_are_acknowledged_not_silently_ignored`.
    """
    calls: dict[str, set[str]] = {}
    for path in FRONTEND_SRC.rglob("*.ts*"):
        if _is_disabled_page(path):
            # An unrouted page cannot issue a request, so its calls are not a
            # live contract. They are still held to account: the disabled set is
            # asserted to be absent from the router and the navigation, absent
            # from the backend, preserved on disk and documented.
            continue
        for match in _CALL.finditer(path.read_text(encoding="utf-8", errors="ignore")):
            endpoint = match.group(1)
            if "//" in endpoint:
                # NR-123. These were skipped here as "the literal half of a
                # concatenated URL". RE-MEASURED: there is no concatenated API
                # URL anywhere in frontend-v3 -- all 21 are single literal
                # strings, e.g. api.get("/national/documents//versions"), and
                # every one is a guaranteed 404 on page load. Skipping them
                # excluded from this guard exactly the calls that are most
                # certainly broken. They go to _malformed_calls() instead of
                # being dropped.
                continue
            calls.setdefault(endpoint, set()).add(str(path.relative_to(FRONTEND_SRC)))
    return calls


def _malformed_calls() -> dict[str, set[str]]:
    """Calls with an empty path segment where an id belongs (NR-123)."""
    calls: dict[str, set[str]] = {}
    for path in FRONTEND_SRC.rglob("*.ts*"):
        if _is_disabled_page(path):
            continue
        for match in _CALL.finditer(path.read_text(encoding="utf-8", errors="ignore")):
            endpoint = match.group(1)
            if "//" in endpoint:
                calls.setdefault(endpoint, set()).add(str(path.relative_to(FRONTEND_SRC)))
    return calls


@pytest.fixture(scope="module")
def registered_paths() -> set[str]:
    """The application's own OpenAPI schema — what is genuinely reachable."""
    from app.factory import create_app

    schema = create_app().openapi()
    return {p.rstrip("/") or "/" for p in schema.get("paths", {})}


def _is_registered(endpoint: str, registered: set[str]) -> bool:
    return (endpoint.rstrip("/") or "/") in registered


# ── A/C. no active route calls an unregistered endpoint ──────────────────────


def test_the_frontend_calls_are_discovered_at_all() -> None:
    """A scanner that finds nothing would make every assertion below vacuous."""
    calls = _frontend_calls()
    assert len(calls) >= 150, f"only {len(calls)} literal API calls found; the scanner has drifted"


def test_no_frontend_call_reaches_an_unregistered_endpoint(registered_paths) -> None:
    """The NR-054 guard.

    Every literal endpoint the frontend calls must be registered, unless it is
    named in the NR-057 ledger above. A new orphan is in neither set and fails
    here.
    """
    offenders = {
        endpoint: sorted(files)
        for endpoint, files in _frontend_calls().items()
        if not _is_registered(endpoint, registered_paths)
        and endpoint not in DECLARED_UNREGISTERED_CALLS
    }
    assert offenders == {}, (
        "these frontend calls do not correspond to any registered backend route:\n"
        + "\n".join(f"  {e} <- {f[0]}" for e, f in sorted(offenders.items()))
    )


def test_the_unregistered_ledger_does_not_grow(registered_paths) -> None:
    """NR-057's population may shrink as those domains are repaired; it may not
    grow. An entry that has since been registered should be deleted from the
    ledger rather than left to rot."""
    calls = set(_frontend_calls())
    stale = sorted(
        e for e in DECLARED_UNREGISTERED_CALLS
        if _is_registered(e, registered_paths) or e not in calls
    )
    assert stale == [], (
        f"these ledger entries are no longer unregistered orphans; remove them: {stale}"
    )
    assert not (DECLARED_UNREGISTERED_CALLS & {f"/{c}" for c in DISABLED_CAPABILITIES}), (
        "a disabled capability must not be carried in the NR-057 ledger"
    )


# ── B/D/E/F/G. the routed capability has a real contract ─────────────────────


def test_the_routed_capability_calls_a_registered_endpoint(registered_paths) -> None:
    page = (
        FRONTEND_SRC / "pages" / "capabilities" / "encounter-management"
        / "CapabilitiesEncounterManagementPage.tsx"
    ).read_text(encoding="utf-8")

    assert f'api.get("{CANONICAL_ENCOUNTERS}")' in page, (
        "the encounter page no longer calls the canonical endpoint"
    )
    assert f'api.get("/{ROUTED_CAPABILITY}")' not in page, (
        "the encounter page still calls its unregistered capability stub"
    )
    assert _is_registered(CANONICAL_ENCOUNTERS, registered_paths)


def test_the_canonical_encounter_contract_matches_what_the_page_renders() -> None:
    """G. Response shape.

    The generated scaffold read `name` and `created_at`; the canonical record has
    neither, so those columns rendered blank and "Invalid Date". Assert the page
    now reads fields the backend actually returns.
    """
    from app.national_data.models.canonical_encounter import CanonicalEncounter

    produced = set(CanonicalEncounter.__annotations__)
    page = (
        FRONTEND_SRC / "pages" / "capabilities" / "encounter-management"
        / "CapabilitiesEncounterManagementPage.tsx"
    ).read_text(encoding="utf-8")

    consumed = set(re.findall(r'col\.accessor\("([a-z_]+)"', page))
    assert consumed, "no columns found on the encounter page"
    assert consumed <= produced, (
        f"the page renders fields the canonical encounter does not return: {sorted(consumed - produced)}"
    )


def test_the_canonical_encounter_endpoint_answers_a_real_request(
    client, make_lab, make_lab_user,
) -> None:
    """The full chain: route → authorization → canonical service → response.

    A list, not `{"items": [], "total": 0}`. Empty here because nothing is
    seeded — that is a real query returning no rows, which is a different thing
    from a handler that returns a literal empty page.
    """
    from tests.conftest import auth_headers

    lab = make_lab("NR054 Encounter Lab")
    user = make_lab_user(lab.id, role="admin")

    response = client.get(CANONICAL_ENCOUNTERS, headers=auth_headers(user.id, lab.id, role="admin"))

    assert response.status_code == 200, response.text
    assert isinstance(response.json(), list), (
        "the page treats the body as an array; the endpoint must return one"
    )


# ── I/J. authorization stays server-side ─────────────────────────────────────


def test_the_encounter_endpoint_refuses_an_unauthenticated_caller(client) -> None:
    """The nav permission is a usability filter. This is the boundary."""
    assert client.get(CANONICAL_ENCOUNTERS).status_code in (401, 403)


def test_the_nav_gate_matches_the_permission_the_backend_enforces() -> None:
    """A nav entry gated more loosely than the endpoint offers users a link that
    403s. `dashboard:read` was that mismatch."""
    source = (BACKEND / "app" / "routes" / "national_data.py").read_text(encoding="utf-8")
    index = source.index("def list_canonical_encounters")
    assert 'require_permission("patients:read")' in source[index - 400:index + 400]

    nav = (FRONTEND_SRC / "permissions" / "index.ts").read_text(encoding="utf-8")
    entry = next(
        line for line in nav.splitlines()
        if f'path: "/capabilities/{ROUTED_CAPABILITY}"' in line
    )
    assert '"patients:read"' in entry, f"nav gate does not match the backend: {entry.strip()}"


def test_the_canonical_encounter_query_is_tenant_scoped() -> None:
    """J. Tenant isolation is preserved by binding to the canonical owner."""
    source = (
        BACKEND / "app" / "national_data" / "models" / "canonical_encounter.py"
    ).read_text(encoding="utf-8")
    assert "query.filter(NationalPatient.lab_id == lab_id)" in source

    route = (BACKEND / "app" / "routes" / "national_data.py").read_text(encoding="utf-8")
    index = route.index("def list_canonical_encounters")
    assert "lab_id=current_user.lab_id" in route[index:index + 600], (
        "the route must pass the caller's own lab_id, never one from the request"
    )


# ── the eight stay disabled ──────────────────────────────────────────────────


@pytest.mark.parametrize("capability", DISABLED_CAPABILITIES)
def test_a_disabled_capability_is_not_reachable(capability: str) -> None:
    """Regression proof for DISABLE_UNTIL_BACKEND_READY: absent from the router
    and absent from the navigation."""
    routes = (FRONTEND_SRC / "routes" / "index.tsx").read_text(encoding="utf-8")
    nav = (FRONTEND_SRC / "permissions" / "index.ts").read_text(encoding="utf-8")

    assert f'path: "capabilities/{capability}"' not in routes, (
        f"{capability} was re-added to the router but still has no backend contract"
    )
    assert f'path: "/capabilities/{capability}"' not in nav, (
        f"{capability} was re-added to the navigation but still has no backend contract"
    )


@pytest.mark.parametrize("capability", DISABLED_CAPABILITIES)
def test_a_disabled_capability_is_indeed_unregistered(capability, registered_paths) -> None:
    """K. The reason they are disabled, restated as an assertion: if one of these
    ever becomes a registered contract, this test fails and asks for the route
    to be restored deliberately rather than forgotten."""
    assert not _is_registered(f"/{capability}", registered_paths), (
        f"/{capability} is now registered — re-enable its route on purpose, "
        "and check it is not still the stub that returns a literal empty page"
    )


def test_the_disabled_pages_are_preserved_and_documented() -> None:
    """Disabled, not deleted — and explicitly so."""
    base = FRONTEND_SRC / "pages" / "capabilities"
    for capability in DISABLED_CAPABILITIES:
        assert (base / capability).is_dir(), f"{capability} page was deleted rather than disabled"
    readme = (base / "README.md").read_text(encoding="utf-8")
    for capability in DISABLED_CAPABILITIES:
        assert capability in readme, f"{capability} is not accounted for in the disposition README"


def test_dynamic_calls_are_acknowledged_not_silently_ignored() -> None:
    """Phase 7 asks for the unresolvable cases to be documented rather than
    guessed at. This records how many there are, so a future reader knows the
    guard's coverage is partial by construction and by how much."""
    dynamic = 0
    for path in FRONTEND_SRC.rglob("*.ts*"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        dynamic += len(re.findall(r"api\.(?:get|post|put|patch|delete)\(\s*`", text))
        dynamic += len(re.findall(r'api\.(?:get|post|put|patch|delete)\(\s*"[^"]*"\s*\+', text))
    assert dynamic > 0
    assert dynamic < 200, (
        f"{dynamic} dynamic API calls — the statically checkable share is shrinking; "
        "consider a typed client before this guard stops being meaningful"
    )


# ── NR-123: calls that cannot be served, whatever the backend registers ───────
#
# 21 calls contain an empty path segment where an id belongs, e.g.
# api.get("/pilot-platform/pilots//gates"). They are generated pages firing an
# unconditional query at a detail endpoint with no id in scope, so each is a
# guaranteed 404 on page load. Fixing them means giving each page selection
# state, which is feature work rather than a contract repair, so they are
# declared rather than papered over.
DECLARED_MALFORMED_CALLS = frozenset({
    "/certification/dimensions//checks",
    "/ecosystem/connectors//health",
    "/ecosystem/partners//audit",
    "/integration/connectors//health",
    "/intelligence/kpis//trend",
    "/national/documents//attachments",
    "/national/documents//history",
    "/national/documents//qrcode",
    "/national/documents//signatures",
    "/national/documents//versions",
    "/national/jobs//executions",
    "/national/jobs//schedules",
    "/national/rules//evaluations",
    "/national/rules//versions",
    "/national/tasks//comments",
    "/national/tasks//history",
    "/national/workflows/executions//approvals",
    "/national/workflows/executions//steps",
    "/pilot-platform/facilities//readiness",
    "/pilot-platform/pilots//facilities",
    "/pilot-platform/pilots//gates",
})
_MALFORMED_CEILING = 21


def test_the_malformed_scanner_still_finds_them() -> None:
    """Positive control. This guard's whole value is that it stopped skipping."""
    assert _malformed_calls(), (
        "no malformed calls found at all — either they were all fixed (remove "
        "the ledger) or the scanner stopped seeing them"
    )


def test_no_new_call_has_an_empty_path_segment() -> None:
    """A path with `//` in it can only ever be a 404, on any backend."""
    malformed = set(_malformed_calls())
    undeclared = sorted(malformed - DECLARED_MALFORMED_CALLS)
    assert not undeclared, (
        "these frontend calls have an empty path segment where an id belongs:\n  "
        + "\n  ".join(undeclared)
    )


def test_the_malformed_ledger_only_shrinks() -> None:
    assert len(DECLARED_MALFORMED_CALLS) <= _MALFORMED_CEILING, (
        f"the malformed-call ledger grew to {len(DECLARED_MALFORMED_CALLS)}; "
        f"the ceiling is {_MALFORMED_CEILING}"
    )


def test_the_malformed_ledger_does_not_rot() -> None:
    live = set(_malformed_calls())
    stale = sorted(DECLARED_MALFORMED_CALLS - live)
    assert not stale, f"declared but no longer in the source: {stale}"
