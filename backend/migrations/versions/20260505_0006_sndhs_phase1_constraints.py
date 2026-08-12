"""SNDHS-lite Phase 1 — Step F: roll-out constraints AFTER backfill.

Run **only** after the backfill script
(``scripts/sndhs_phase1_backfill.py``) reports 100% coverage and a
``sndhs_phase1_check`` row in the operator's runbook log.

Adds, in order:

1. Foreign key ``lab_orders.visit_id → visits.id`` using
   ``ADD CONSTRAINT ... NOT VALID`` (no full table scan, brief lock),
   then ``VALIDATE CONSTRAINT`` (no lock, online).

2. Partial UNIQUE index on ``patients.national_id WHERE national_id IS
   NOT NULL`` using ``CREATE UNIQUE INDEX CONCURRENTLY`` so production
   writes are not blocked.

If pre-conditions are not satisfied the migration aborts loudly:

- Any ``lab_orders`` row with ``visit_id IS NULL`` → abort.
- Any duplicate non-null ``patients.national_id`` → abort.

This guarantees we never apply a constraint to dirty data.

Rollback (downgrade) drops the constraint / index. It does NOT remove
columns — those are removed by 0001/0003/0004 downgrades.

Revision ID : 20260505_0006
Revises     : 20260505_0005
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text


revision      = "20260505_0006"
down_revision = "20260505_0005"
branch_labels = None
depends_on    = None


def _pg() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def _index_exists(name: str, table: str) -> bool:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return name in {ix["name"] for ix in inspect(bind).get_indexes(table)}
    row = bind.execute(text(
        "SELECT 1 FROM pg_indexes WHERE schemaname = current_schema() "
        "AND indexname = :n"
    ), {"n": name}).first()
    return row is not None


def _constraint_exists(name: str, table: str) -> bool:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return False
    row = bind.execute(text(
        "SELECT 1 FROM pg_constraint c "
        "JOIN pg_class t ON t.oid = c.conrelid "
        "WHERE t.relname = :tab AND c.conname = :n"
    ), {"tab": table, "n": name}).first()
    return row is not None


def _assert_pre_conditions() -> None:
    bind = op.get_bind()

    # 1. Every lab_orders row must have a visit_id.
    nulls = bind.execute(text(
        "SELECT count(*) FROM lab_orders WHERE visit_id IS NULL"
    )).scalar() or 0
    if nulls:
        raise RuntimeError(
            f"Phase-1 step F refuses to run: {nulls} lab_orders row(s) "
            "still have visit_id IS NULL. Run "
            "scripts/sndhs_phase1_backfill.py until coverage is 100% "
            "before applying this migration."
        )

    # 2. No duplicate non-null national_id.
    dup = bind.execute(text(
        "SELECT count(*) FROM ("
        "  SELECT national_id FROM patients "
        "  WHERE national_id IS NOT NULL "
        "  GROUP BY national_id HAVING count(*) > 1"
        ") s"
    )).scalar() or 0
    if dup:
        raise RuntimeError(
            f"Phase-1 step F refuses to run: {dup} duplicate non-null "
            "national_id value(s) in patients. Resolve duplicates "
            "before applying this migration."
        )


def upgrade() -> None:
    if _pg():
        _assert_pre_conditions()

        # 1. FK: NOT VALID first (cheap), then VALIDATE outside any tx.
        if not _constraint_exists("fk_lab_orders_visit_id", "lab_orders"):
            op.execute(text(
                "ALTER TABLE lab_orders "
                "ADD CONSTRAINT fk_lab_orders_visit_id "
                "FOREIGN KEY (visit_id) REFERENCES visits(id) "
                "ON DELETE SET NULL NOT VALID"
            ))
        # VALIDATE is online (only an ACCESS SHARE lock).
        op.execute(text(
            "ALTER TABLE lab_orders VALIDATE CONSTRAINT fk_lab_orders_visit_id"
        ))

        # 2. Partial UNIQUE on patients.national_id WHERE NOT NULL.
        if not _index_exists("ux_patients_national_id_notnull", "patients"):
            with op.get_context().autocommit_block():
                op.execute(text(
                    "CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS "
                    "ux_patients_national_id_notnull "
                    "ON patients (national_id) "
                    "WHERE national_id IS NOT NULL"
                ))
    else:
        # Non-PG dialects (sqlite test path).
        _assert_pre_conditions()
        if not _constraint_exists("fk_lab_orders_visit_id", "lab_orders"):
            with op.batch_alter_table("lab_orders") as bop:
                bop.create_foreign_key(
                    "fk_lab_orders_visit_id", "visits",
                    ["visit_id"], ["id"], ondelete="SET NULL",
                )
        if not _index_exists("ux_patients_national_id_notnull", "patients"):
            op.create_index(
                "ux_patients_national_id_notnull",
                "patients",
                ["national_id"],
                unique=True,
                postgresql_where=None,
            )


def downgrade() -> None:
    if _pg():
        if _index_exists("ux_patients_national_id_notnull", "patients"):
            with op.get_context().autocommit_block():
                op.execute(text(
                    "DROP INDEX CONCURRENTLY IF EXISTS ux_patients_national_id_notnull"
                ))
        if _constraint_exists("fk_lab_orders_visit_id", "lab_orders"):
            op.execute(text(
                "ALTER TABLE lab_orders DROP CONSTRAINT IF EXISTS fk_lab_orders_visit_id"
            ))
    else:
        if _index_exists("ux_patients_national_id_notnull", "patients"):
            op.drop_index("ux_patients_national_id_notnull", table_name="patients")
        if _constraint_exists("fk_lab_orders_visit_id", "lab_orders"):
            with op.batch_alter_table("lab_orders") as bop:
                bop.drop_constraint("fk_lab_orders_visit_id", type_="foreignkey")
