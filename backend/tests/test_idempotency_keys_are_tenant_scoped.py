"""An idempotency key is unique within a tenant, never across the platform.

A key is chosen by the client. Clients choose invoice numbers, counters, dates
and order references -- values that collide across tenants by construction. So
a globally unique idempotency column does not deduplicate; it lets whichever
tenant gets there first take a key away from everybody else. Nothing leaks:
the affected tenant's write is simply refused.

That was live on `claims`, and executed against PostgreSQL 16 at head:

    lab 901 creates a claim with key 'INV-2026-001'  -> OK
    lab 902's lab-scoped idempotency lookup finds     -> 0, so it proceeds
    lab 902's INSERT                                  -> REFUSED,
        duplicate key value violates unique constraint "claims_idempotency_key_key"

Both application read paths -- `services/claims_service.py::create_claim` and
`insurance/api/claims.py::create_claim` -- already filtered `lab_id` alongside
the key. Only the constraint did not, which is why the failure surfaced as a
refused INSERT rather than as a cross-tenant read.

The platform already had the convention; `claims` was the one table missing it.
Nine comparable tables scope the key by lab, tenant, institution or
subscription. This test makes that the rule rather than the habit, measured
against the live database rather than against the ORM, because the constraint
that matters is the one PostgreSQL enforces.

Runs in the migration job, which has a migrated PostgreSQL.
"""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, text

#: Column names that carry a client-chosen idempotency token.
_KEY_PATTERN = "%idempotency%"

#: Anything in this set discriminates one tenant from another. A unique index
#: over an idempotency key must include at least one of them.
TENANT_DISCRIMINATORS = frozenset(
    {"lab_id", "tenant_id", "institution_id", "organization_id", "org_id", "subscription_id"},
)

#: Tables whose idempotency key is deliberately NOT tenant-scoped, each with the
#: reason. This may shrink. It may not grow without an entry explaining why a
#: client-chosen key is safe to make globally exclusive.
DECLARED_UNSCOPED = {
    "niam_account_creation_requests": (
        "National scope by design: account creation is a national-registry "
        "operation and the table carries no tenant column at all. NR-022 "
        "established Person/Identity as the canonical national subject."
    ),
    "niam_citizen_relationships": (
        "National scope by design, same as above -- a citizen relationship is "
        "not owned by a lab. Confirmed: the table has no tenant column."
    ),
}

#: Tables that intentionally have NO unique index over the key, with the reason.
DECLARED_NOT_UNIQUE = {
    "edge_tasks": (
        "Deliberate. app/edge/scheduler.py only treats a key as taken while the "
        "task is pending/dispatched/running/completed, so a task that reached "
        "'failed' may legitimately be retried under the same key. A unique "
        "constraint would forbid that retry. The composite index "
        "idx_edge_tasks_idem (lab_id, idempotency_key) supports the lookup "
        "without constraining it."
    ),
}


def _database_url() -> str:
    for var in ("GULA_SCHEMA_DATABASE_URL", "MIGRATION_DATABASE_URL", "DATABASE_URL"):
        url = os.environ.get(var)
        if url and url.startswith(("postgresql://", "postgresql+psycopg2://")):
            return url
    pytest.skip("needs a migrated PostgreSQL")
    raise AssertionError  # unreachable


@pytest.fixture(scope="module")
def columns() -> list[tuple[str, str]]:
    engine = create_engine(_database_url())
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT table_name, column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND column_name ILIKE :pat
                    ORDER BY table_name, column_name
                    """,
                ),
                {"pat": _KEY_PATTERN},
            ).fetchall()
    finally:
        engine.dispose()
    return [(r.table_name, r.column_name) for r in rows]


@pytest.fixture(scope="module")
def unique_indexes() -> dict[str, list[str]]:
    engine = create_engine(_database_url())
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT tablename, indexdef FROM pg_indexes
                    WHERE schemaname = 'public' AND indexdef ILIKE '%UNIQUE%'
                    """,
                ),
            ).fetchall()
    finally:
        engine.dispose()
    found: dict[str, list[str]] = {}
    for row in rows:
        found.setdefault(row.tablename, []).append(row.indexdef)
    return found


def test_the_census_still_finds_the_idempotency_columns(columns) -> None:
    """Guards the guard: a rename that hides the population must not pass silently."""
    assert len(columns) >= 12, (
        f"only {len(columns)} idempotency-bearing columns found, expected at least 12. "
        "Either the schema shrank or the census pattern stopped matching -- and a "
        "census that matches nothing passes every test below for the wrong reason."
    )


def test_every_idempotency_key_is_unique_within_a_tenant_not_across_them(
    columns, unique_indexes,
) -> None:
    """The invariant. A client-chosen key must not be globally exclusive."""
    offenders = []
    for table, column in columns:
        if table in DECLARED_UNSCOPED or table in DECLARED_NOT_UNIQUE:
            continue
        covering = [
            definition for definition in unique_indexes.get(table, [])
            if column in definition
        ]
        if not covering:
            offenders.append((table, column, "no unique index over the key"))
            continue
        if not any(
            discriminator in definition
            for definition in covering
            for discriminator in TENANT_DISCRIMINATORS
        ):
            offenders.append((table, column, covering[0]))

    assert offenders == [], (
        "an idempotency key is unique across the whole platform rather than "
        f"within a tenant: {offenders}. A client picks these values -- invoice "
        "numbers, counters -- so one tenant would take the key away from every "
        "other, whose INSERT is then refused. Scope the unique index by the "
        "tenant column, as uq_billing_invoice_lab_idempotency does, or declare "
        "the table in DECLARED_UNSCOPED with the reason."
    )


def test_the_declared_exceptions_still_describe_reality(columns, unique_indexes) -> None:
    """The rot check.

    An exception that has quietly become unnecessary is worse than no exception:
    it exempts a table that no longer needs exempting, so a future regression
    there passes.
    """
    present = {table for table, _ in columns}

    stale_unscoped = [
        table for table in DECLARED_UNSCOPED
        if table in present
        and any(
            discriminator in definition
            for definition in unique_indexes.get(table, [])
            for discriminator in TENANT_DISCRIMINATORS
        )
    ]
    assert stale_unscoped == [], (
        f"these tables are declared as having no tenant scope, but now have a "
        f"tenant-scoped unique index: {stale_unscoped}. Remove them from "
        "DECLARED_UNSCOPED so the invariant covers them."
    )

    stale_not_unique = [
        table for table in DECLARED_NOT_UNIQUE
        if table in present
        and any("idempotency" in d for d in unique_indexes.get(table, []))
    ]
    assert stale_not_unique == [], (
        f"these tables are declared as intentionally having no unique index "
        f"over the key, but now have one: {stale_not_unique}. Remove them from "
        "DECLARED_NOT_UNIQUE."
    )


def test_claims_specifically_is_scoped_by_lab(unique_indexes) -> None:
    """NR-094's own regression, named so a revert is unambiguous."""
    definitions = unique_indexes.get("claims", [])
    scoped = [d for d in definitions if "idempotency_key" in d and "lab_id" in d]
    globally_unique = [
        d for d in definitions
        if "idempotency_key" in d and "lab_id" not in d
    ]
    assert scoped, (
        "claims has no unique index over (lab_id, idempotency_key). NR-094 "
        "added uq_claims_lab_idempotency; a migration appears to have removed it."
    )
    assert globally_unique == [], (
        f"claims has a globally unique index over idempotency_key again: "
        f"{globally_unique}. That is the defect NR-094 fixed -- one lab's key "
        "becomes unusable for every other lab."
    )
