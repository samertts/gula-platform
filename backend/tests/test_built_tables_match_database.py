"""NR-069 / ADR-027 — the derivation must equal what PostgreSQL actually builds.

`test_built_table_evidence.py` proves the extractor is self-consistent: it
resolves every creation form, and the checked-in snapshot agrees with it. That
is AST evidence, which sits well down the evidence hierarchy. It cannot catch a
migration that *declares* a table the database never gets, or a creation form
nobody thought to model.

This file closes that gap with the strongest tier available: run the real chain
against a real PostgreSQL and compare the derived set against `pg_tables`.

Measured on PostgreSQL 16.13 after `alembic upgrade head`:

    physical (pg_tables, public schema) : 423
    derived  (AST over migrations)      : 422
    difference                          : {"alembic_version"}

`alembic_version` is Alembic's own bookkeeping table, created by the migration
runner rather than by any migration, so it is the one expected asymmetry and is
excluded by name rather than by a fudge factor. Everything else matches exactly
in both directions -- no derived table is missing from the database, and no
database table is missing from the derivation.

That is what promotes `built_tables()` from "internally consistent" to
"validated against reality". The three tables NR-069 was about --
`niam_admin_units`, `niam_organization_representatives`,
`niam_organization_ownerships` -- are asserted present physically, which is the
claim the original snapshot got wrong.

Marked `integration`: it needs a migrated database. The IAM migration job runs
it after `alembic upgrade head`, reading `MIGRATION_DATABASE_URL` -- which that
job already exports -- because `conftest.py` pins `DATABASE_URL` to in-memory
SQLite before any app import. The unit job deselects it.
"""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, text

from tests.orm_resolution import built_tables

pytestmark = pytest.mark.integration

#: Created by Alembic itself, not by a migration in the chain.
RUNNER_OWNED = {"alembic_version"}

#: The tables NR-069 was about: created through a helper whose table-name
#: argument is a function parameter, and therefore invisible to a literal-only
#: scan. Asserted physically so the finding can never be quietly re-broken.
HELPER_CREATED = {
    "niam_admin_units",
    "niam_organization_representatives",
    "niam_organization_ownerships",
}


def _physical_tables() -> set[str]:
    # `conftest.py` hard-sets DATABASE_URL to in-memory SQLite before any app
    # import, so it cannot be used here. The IAM migration job already exports
    # MIGRATION_DATABASE_URL pointing at the same PostgreSQL service it runs
    # `alembic upgrade head` against, which is exactly the database this
    # comparison needs.
    url = os.environ.get("MIGRATION_DATABASE_URL")
    if not url:
        pytest.skip(
            "MIGRATION_DATABASE_URL is not set; this check needs the migrated "
            "PostgreSQL database, and DATABASE_URL is pinned to SQLite by conftest"
        )
    if url.startswith("sqlite"):
        pytest.skip("this check compares against PostgreSQL, not SQLite")
    engine = create_engine(url)
    try:
        with engine.connect() as connection:
            rows = connection.execute(
                text(
                    "SELECT tablename FROM pg_tables "
                    "WHERE schemaname = 'public' ORDER BY tablename"
                )
            )
            return {row[0] for row in rows}
    finally:
        engine.dispose()


def test_the_derivation_matches_the_migrated_database_exactly() -> None:
    """Ground truth, in both directions.

    A table in the database but not derived means the extractor has a blind
    spot -- the NR-069 failure, which understates what is built and overstates
    the unbuilt surface.

    A table derived but not in the database is the opposite and more dangerous
    error: guards would treat it as built and wave through reads that raise
    UndefinedTable at runtime.
    """
    physical = _physical_tables() - RUNNER_OWNED
    derived = set(built_tables())

    assert physical, (
        "no tables found in the public schema; the database is not migrated, so "
        "this comparison would pass vacuously"
    )

    missing_from_derivation = sorted(physical - derived)
    assert missing_from_derivation == [], (
        "PostgreSQL has these tables and the migration derivation does not "
        "produce them, so every guard keyed on 'is this built?' treats them as "
        "absent. The extractor has a blind spot -- find the creation form it "
        f"does not model: {missing_from_derivation}"
    )

    missing_from_database = sorted(derived - physical)
    assert missing_from_database == [], (
        "the derivation claims these tables are built but the migrated database "
        "does not have them, so guards would wave through reads that raise "
        f"UndefinedTable at runtime: {missing_from_database}"
    )


def test_the_helper_created_tables_physically_exist() -> None:
    """NR-069 as a physical regression rather than a parsing one."""
    physical = _physical_tables()
    missing = sorted(HELPER_CREATED - physical)
    assert missing == [], (
        "these tables are created through `_create_if_missing` in "
        "20260814_0002_organization_structure.py and must exist after "
        f"`alembic upgrade head`: {missing}"
    )
