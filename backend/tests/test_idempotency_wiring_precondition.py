"""`app/core/idempotency.py` must not be wired to a route as it is written.

The module is a FastAPI dependency offering HTTP idempotency, and its docstring
names the endpoints it is for:

    Supported on: POST endpoints that create or mutate clinical data
      - POST /api/orders
      - POST /api/results (entering results)
      - POST /api/results/{id}/validate
      - POST /api/samples

    Rules:
      - Keys are scoped per lab (prevents cross-lab replay attacks).

Nothing imports it. `idempotency_check` is used as a `Depends` nowhere and
`purge_expired_keys` is called by nothing, so none of those four endpoints uses
it and the stated rule has never been exercised. That is the only reason the
defects below are latent rather than live.

The rule is not implemented. Executed against PostgreSQL 16 at head, with the
module's own three statements extracted by AST and run verbatim:

1.  **A cached response crosses tenants.** `idempotency_keys` has PRIMARY KEY
    `(key)` alone, so a key is globally unique, while `cache()` writes
    `UPDATE idempotency_keys SET status_code, response_body WHERE key = :key`
    with no `lab_id`. Lab A claims `shared-key-0001` and caches an order for its
    own patient; lab B presents the same key, is told the request is new
    (its SELECT misses on `lab_id`), proceeds, and caches its own response over
    lab A's row -- the row keeps `lab_id = 901`. Lab A then replays its own key
    and is served `{"order_id": 222, "patient": "LAB-B PATIENT"}`.

2.  **A NULL-lab row replays to every lab.** The lookup reads
    `WHERE key = :key AND (lab_id = :lab_id OR lab_id IS NULL)`. `lab_id` comes
    from `getattr(current_user, "lab_id", None)`, so any principal without one --
    a citizen, a `ministry_admin`, a `province_admin`, a service account --
    stores a row that matches *every* lab's lookup. Executed: one such row was
    readable by lab 901 and lab 902 alike.

3.  **The reservation does not reserve.** The insert is
    `ON CONFLICT (key) DO NOTHING` and the code never reads `rowcount`, so a key
    already held by another lab silently yields `is_duplicate=False` and the
    request proceeds unprotected. Executed: rowcount 0, and the caller cannot
    tell.

A correct implementation already exists and is live.
`app/services/order_service.py::create_order` keys its cache
`f"idempotency:order:{lab_id}:{idempotency_key}"` -- tenant in the key, not in a
filter -- fingerprints the payload so a key cannot be reused for different
clinical content, and claims atomically with `set_if_absent`. `POST /orders`
passes the header through to it. That is the design this module should adopt if
it is ever wired, rather than the one it has.

So these tests do not repair the module. They hold the precondition: it stays
unreachable until the three defects are fixed, and the implementation that does
work does not quietly lose its tenant scoping.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

BACKEND = pathlib.Path(__file__).resolve().parents[1]
DORMANT = BACKEND / "app" / "core" / "idempotency.py"
LIVE = BACKEND / "app" / "services" / "order_service.py"

#: Route wirings of the dormant dependency. It may fall to stay at zero; it may
#: not rise while the defects in this module's docstring remain.
DECLARED_ROUTE_WIRINGS = 0

#: The three defects, each pinned by a fragment of the module's own source. A
#: fragment that disappears means someone repaired that defect, and the test
#: says so rather than passing silently -- the ledger has to be updated in the
#: same change, so the wiring ratchet above can be reconsidered deliberately.
DECLARED_DEFECTS = {
    "cross-tenant cache overwrite": "UPDATE idempotency_keys",
    "NULL-lab wildcard in the lookup": "lab_id = :lab_id OR lab_id IS NULL",
    "reservation that does not reserve": "ON CONFLICT (key) DO NOTHING",
}


@pytest.fixture(scope="module")
def dormant_source() -> str:
    return DORMANT.read_text(encoding="utf-8")


def _imports_of(path: pathlib.Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return set()
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module.endswith("core.idempotency"):
                names.update(a.name for a in node.names)
        elif isinstance(node, ast.Import):
            names.update(a.name for a in node.names if a.name.endswith("core.idempotency"))
    return names


def test_the_dormant_dependency_is_still_wired_to_nothing() -> None:
    """The ratchet. Wiring it as written makes all three defects live at once."""
    wirings = []
    for path in sorted((BACKEND / "app").rglob("*.py")):
        if path == DORMANT:
            continue
        names = _imports_of(path)
        if names:
            wirings.append((str(path.relative_to(BACKEND)), sorted(names)))

    assert len(wirings) <= DECLARED_ROUTE_WIRINGS, (
        f"app/core/idempotency.py is now imported by {wirings}. Wiring it as "
        "written makes three proven defects live: a cached response that "
        "crosses tenants, a NULL-lab row that replays to every lab, and a "
        "reservation that does not reserve. Adopt the design in "
        "app/services/order_service.py::create_order instead -- tenant in the "
        "cache key, payload fingerprint, atomic claim."
    )


def test_each_pinned_defect_is_still_present_or_the_ledger_is_updated(dormant_source) -> None:
    """The rot check.

    A guard that only watches for the defect getting worse goes stale the day
    someone fixes it. If a fragment is gone, the repair happened and this ledger
    -- and the wiring ratchet that depends on it -- must be revisited in the
    same change rather than left asserting a state that no longer exists.
    """
    resolved = [
        name for name, fragment in DECLARED_DEFECTS.items()
        if fragment not in dormant_source
    ]
    assert resolved == [], (
        f"these pinned defects are no longer present: {resolved}. That is good "
        "news, and it means DECLARED_DEFECTS and DECLARED_ROUTE_WIRINGS are now "
        "describing a module that no longer exists in that form. Remove the "
        "resolved entries and decide deliberately whether wiring is now safe."
    )


def test_the_dormant_lookup_is_not_the_one_that_gets_wired(dormant_source) -> None:
    """Names the specific clause, so a partial repair cannot look like a whole one.

    Removing `OR lab_id IS NULL` alone still leaves the cross-tenant overwrite,
    because the UPDATE matches on `key` and the primary key is `(key)`.
    """
    has_wildcard = "lab_id = :lab_id OR lab_id IS NULL" in dormant_source
    update_is_scoped = (
        "UPDATE idempotency_keys" in dormant_source
        and "SET status_code" in dormant_source
        and dormant_source.count("WHERE key = :key\n") >= 1
    )
    assert has_wildcard and update_is_scoped, (
        "the dormant module's SQL changed. Re-run the two-lab execution proof "
        "in this docstring before relying on either of these tests again."
    )


def test_the_live_implementation_keeps_the_tenant_in_its_cache_key() -> None:
    """Protects the one that works.

    `order_service.create_order` is what actually serves POST /orders. Its
    tenant scoping is in the cache key rather than in a filter, which is why it
    does not have the dormant module's overwrite problem: two labs cannot name
    the same cache entry. If that key ever loses `lab_id`, the live path
    acquires the defect this file exists to keep dormant.
    """
    source = LIVE.read_text(encoding="utf-8")
    assert 'f"idempotency:order:{lab_id}:{idempotency_key}"' in source, (
        "the live idempotency cache key no longer contains lab_id. Two labs "
        "presenting the same Idempotency-Key would then share a cache entry, "
        "which is exactly the cross-tenant replay app/core/idempotency.py is "
        "held dormant for."
    )
    assert "set_if_absent" in source, (
        "the live idempotency claim is no longer atomic. Without a "
        "claim-if-absent, two concurrent requests with the same key both "
        "proceed, and the fingerprint check cannot help."
    )
