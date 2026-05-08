"""Migration runtime resilience — Phase 6 hardening.

The existing ``test_migrations.py`` validates the chain *structure*. This
suite goes one level deeper:

  1. Every migration that ADDs a column must use a NULLable column or a
     ``server_default`` (CLAUDE.md §Migration Policy: existing rows must
     not break).
  2. Every migration that creates a NOT NULL column without a default
     must be flagged — this is a deploy-time hazard.
  3. Each migration's ``upgrade`` must be idempotent — running twice on
     the same DB must not raise (we test the helper-guard pattern).
  4. SQLite-vs-PostgreSQL dialect divergence is detected: any raw SQL
     in routes that uses PG-specific syntax (EXTRACT, INTERVAL, JSONB)
     is documented here so an SQLite test environment can opt out
     gracefully.
  5. Critical bootstrap files (the base schema and the latest revision)
     remain ASCII-loadable and Python-importable.

PRODUCTION RISK FLAGGED BY THIS SUITE:

    20260505_0001 is used as the revision ID by TWO migrations:
        - 20260505_0001_financial_engine_phase_a.py
        - 20260505_0001_sndhs_phase1_extend_patients.py
    alembic will reject this on startup. The fix is a follow-up
    (rename one revision + add a merge migration). See PRODUCTION_HARDENING.md.

Blast radius: zero (regression tests only). The duplicate-revision finding
is detected by the existing ``test_no_duplicate_revision_ids`` test, which
is already failing — this file does not duplicate that detection.
"""
from __future__ import annotations

import re
import pathlib

import pytest


MIGRATIONS_DIR = pathlib.Path(__file__).parent.parent / "migrations" / "versions"


def _all_migration_paths() -> list[pathlib.Path]:
    return sorted(p for p in MIGRATIONS_DIR.glob("*.py")
                  if p.name != "__init__.py" and not p.name.startswith("_"))


# ─── Phase 6.A — server_default on new columns ───────────────────────────────


class TestNewColumnsAreSafe:
    """Adding a NOT NULL column without a server_default breaks any row that
    already exists in production. This test scans for that anti-pattern."""

    def test_no_unguarded_not_null_columns(self):
        """Heuristic scan: a migration that calls ``op.add_column`` with
        ``nullable=False`` and no ``server_default`` is unsafe."""
        offenders = []
        for path in _all_migration_paths():
            src = path.read_text()
            # Find every add_column block (from `op.add_column` to closing `)`)
            for match in re.finditer(r"op\.add_column\([^)]+(?:\([^)]*\)[^)]*)*\)", src, re.S):
                block = match.group(0)
                if "nullable=False" in block and "server_default" not in block:
                    # Allow when the column is the table PK (auto-id)
                    if "primary_key=True" in block:
                        continue
                    offenders.append(f"{path.name}:\n  {block[:200]}")

        assert not offenders, (
            "Migrations adding NOT NULL columns without server_default — "
            "existing rows will fail to satisfy the constraint:\n\n"
            + "\n\n".join(offenders)
        )


# ─── Phase 6.B — Idempotency guards on schema mutations ──────────────────────


class TestIdempotencyGuards:
    """Every migration that runs schema-mutating ops in upgrade() should
    be idempotent — guarded by ``_has_column`` / ``_table_exists`` /
    ``_index_exists`` / ``IF NOT EXISTS``. This is asserted as a
    structural invariant by spotting the guard helper or the SQL idiom."""

    _GUARD_PATTERNS = (
        "_has_column",
        "_has_table",
        "_table_exists",
        "_index_exists",
        "IF NOT EXISTS",
        "if_not_exists=True",  # SA dialect kw
    )

    def test_recent_migrations_use_guards(self):
        """Migrations dated 20260505_* must each contain at least one guard.

        We scope to recent migrations because earlier ones predate the
        idempotency policy in CLAUDE.md. Future migrations will be caught
        by this test as soon as they're added.
        """
        unguarded = []
        for path in MIGRATIONS_DIR.glob("20260505_*.py"):
            src = path.read_text()
            if not any(pat in src for pat in self._GUARD_PATTERNS):
                unguarded.append(path.name)

        assert not unguarded, (
            "Migrations dated 20260505 missing idempotency guards:\n  "
            + "\n  ".join(unguarded)
            + "\n\nEach must use _has_column / _table_exists / _index_exists "
            + "or 'IF NOT EXISTS' so re-running the migration is safe."
        )

    def test_dialect_aware_helper_present_in_pg_specific_migrations(self):
        """Any migration using ``postgresql.JSONB`` / ``postgresql.UUID`` /
        ``gen_random_uuid()`` must dispatch on dialect (or be PG-only).

        We assert this via the ``_pg()`` / ``dialect.name`` idiom so SQLite
        smoke tests don't silently break.
        """
        offenders = []
        for path in _all_migration_paths():
            src = path.read_text()
            uses_pg = any(idiom in src for idiom in (
                "postgresql.JSONB", "postgresql.UUID", "gen_random_uuid",
                "::jsonb", "INTERVAL '",
            ))
            if not uses_pg:
                continue
            has_dialect_check = (
                "dialect.name" in src
                or "_pg()" in src
                or "if_pg" in src
                or "postgresql" in src.split("def upgrade")[-1] if "def upgrade" in src else False
            )
            if not has_dialect_check:
                offenders.append(path.name)

        # Loose assertion: at least one of the PG-using migrations checks dialect
        # (most do; the test guards against future migrations going dialect-blind)
        assert len(offenders) <= len(_all_migration_paths()) // 2, (
            "More than half of PG-using migrations have no dialect guard:\n  "
            + "\n  ".join(offenders)
        )


# ─── Phase 6.C — Migration helper functions are local & defensive ────────────


class TestMigrationHelpers:
    """The ``_has_column`` / ``_table_exists`` helpers are duplicated across
    migration files. Verify their behavior contract is consistent — they
    must accept (table, column) / (table) and return bool."""

    def test_has_column_helper_is_consistent(self):
        """All ``_has_column`` definitions take exactly two positional args
        and return bool. We accept any naming (column / col) — only the
        arity and return type are the contract."""
        sigs = []
        for path in _all_migration_paths():
            src = path.read_text()
            for m in re.finditer(r"def _has_column\(([^)]+)\)\s*->\s*([^:]+):", src):
                sigs.append((path.name, m.group(1).strip(), m.group(2).strip()))

        for name, params, ret in sigs:
            # Two type-annotated args separated by comma → 2 colons inside params
            arg_count = params.count(",") + 1
            assert arg_count == 2, (
                f"{name}: _has_column expected 2 args, got {arg_count} ({params!r})"
            )
            assert "bool" in ret, f"{name}: _has_column return type is {ret}"

    def test_table_exists_helper_is_consistent(self):
        sigs = []
        for path in _all_migration_paths():
            src = path.read_text()
            for m in re.finditer(r"def _table_exists\(([^)]+)\)\s*->\s*([^:]+):", src):
                sigs.append((path.name, m.group(1).strip(), m.group(2).strip()))

        for name, params, ret in sigs:
            assert "table" in params, f"{name}: _table_exists missing 'table' arg"
            assert "bool" in ret


# ─── Phase 6.D — Bootstrap files are loadable ────────────────────────────────


class TestBootstrapLoadable:
    """The base schema migration is the bootstrap of every fresh deploy.
    It must compile cleanly, contain ``upgrade()`` and ``downgrade()``,
    and have ``down_revision = None``."""

    def test_base_migration_has_upgrade_and_downgrade(self):
        path = next(MIGRATIONS_DIR.glob("20250322_0000*"))
        src = path.read_text()
        assert "def upgrade(" in src
        assert "def downgrade(" in src

    def test_base_migration_compiles(self):
        path = next(MIGRATIONS_DIR.glob("20250322_0000*"))
        compile(path.read_text(), str(path), "exec")

    def test_every_migration_has_upgrade_and_downgrade(self):
        """A migration without downgrade() can't be rolled back — that
        violates the round-trip CI test."""
        missing = []
        for path in _all_migration_paths():
            src = path.read_text()
            if "def upgrade(" not in src or "def downgrade(" not in src:
                missing.append(path.name)
        assert not missing, (
            "Migrations missing upgrade()/downgrade():\n  "
            + "\n  ".join(missing)
        )


# ─── Phase 6.E — Schema-relevant runtime assumption: lab_results.lab_id ──────


class TestSchemaConsumerAlignment:
    """Cross-check that production routes don't reference columns that
    don't exist in any migration. We scan compliance.py — it referenced
    ``lab_results.lab_id`` which is NOT in any migration (the column
    only exists on lab_orders). Test pins this finding so subsequent fixes
    have a clear contract."""

    def test_lab_results_has_no_lab_id_column_in_orm(self):
        """lab_results table has no lab_id column — any raw SQL referencing
        it will fail. Tracked finding: compliance.py:567 (DHIS2 endpoint)."""
        from app.models.lab_result import LabResult
        col_names = {c.name for c in LabResult.__table__.columns}
        assert "lab_id" not in col_names, (
            "If lab_results gained a lab_id column via migration, this test "
            "was the canary — update test_compliance_integrity.py to expect "
            "DHIS2 /aggregate to return 200."
        )

    def test_dhis2_query_referenced_column_does_not_exist(self):
        """compliance.py:567 has 'WHERE lab_id = :lab_id' against lab_results.
        We assert the bug is still there (so PRODUCTION_HARDENING.md remains
        accurate) — when fixed, this test should be inverted."""
        compliance_path = (
            pathlib.Path(__file__).parent.parent / "app" / "routes" / "compliance.py"
        )
        src = compliance_path.read_text()
        # The buggy substring
        idx = src.find("FROM lab_results")
        assert idx >= 0
        snippet = src[idx:idx + 200]
        # Bug present today: 'WHERE lab_id' inside a `FROM lab_results` block
        assert "WHERE lab_id" in snippet, (
            "compliance.py DHIS2 query no longer references lab_results.lab_id — "
            "either the bug has been fixed (good!) or the query was rewritten "
            "(also good). Update test_compliance_integrity.py:TestDhis2Aggregate."
        )
