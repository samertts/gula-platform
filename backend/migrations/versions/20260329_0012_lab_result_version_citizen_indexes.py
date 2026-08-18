"""lab_result version column + citizen lookup indexes

Revision ID: 20260329_0012
Revises: 20260329_0011
Create Date: 2026-03-29

Changes:
1. Add `version` (integer, not null, default 1) to lab_results — enables
   optimistic locking on result updates (same pattern as lab_orders).
2. Add composite index on patients(phone, lab_id) for fast citizen result
   lookups: SELECT * FROM patients WHERE phone = ? covers all labs.
3. Add index on patients(national_id_hash) — fallback citizen identity link.
4. Add index on lab_results(flag) WHERE flag != 'normal' — fast critical/
   abnormal result queries for citizen health record endpoint.
"""
from alembic import context, op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers
revision = "20260329_0012"
down_revision = "20260329_0011"
branch_labels = None
depends_on = None


def _table_exists(conn, table: str) -> bool:
    if context.is_offline_mode():
        return True
    inspector = Inspector.from_engine(conn)
    return table in inspector.get_table_names()


def _column_exists(conn, table: str, column: str) -> bool:
    if context.is_offline_mode():
        return False
    inspector = Inspector.from_engine(conn)
    cols = [c["name"] for c in inspector.get_columns(table)]
    return column in cols


def _index_exists(conn, index: str) -> bool:
    if context.is_offline_mode():
        return False
    inspector = Inspector.from_engine(conn)
    for table in inspector.get_table_names():
        idx_names = [i["name"] for i in inspector.get_indexes(table)]
        if index in idx_names:
            return True
    return False


def upgrade():
    conn = op.get_bind()

    # ── 1. Add version column to lab_results ─────────────────────────────────
    if _table_exists(conn, "lab_results") and not _column_exists(conn, "lab_results", "version"):
        op.add_column(
            "lab_results",
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        )
        # Back-fill existing rows
        op.execute("UPDATE lab_results SET version = 1 WHERE version IS NULL")

    # ── 2. Composite index: patients(phone, lab_id) ───────────────────────────
    if not _index_exists(conn, "ix_patients_phone_lab"):
        op.create_index(
            "ix_patients_phone_lab",
            "patients",
            ["phone", "lab_id"],
            unique=False,
        )

    # ── 3. Index on patients(national_id_hash) ────────────────────────────────
    if not _index_exists(conn, "ix_patients_nid_hash"):
        op.create_index(
            "ix_patients_nid_hash",
            "patients",
            ["national_id_hash"],
            unique=False,
            postgresql_where=sa.text("national_id_hash IS NOT NULL"),
        )

    # ── 4. Partial index: lab_results flagged abnormal ────────────────────────
    if not _index_exists(conn, "ix_lab_results_flag_abnormal"):
        op.create_index(
            "ix_lab_results_flag_abnormal",
            "lab_results",
            ["flag", "order_id"],
            unique=False,
            postgresql_where=sa.text("flag IS NOT NULL AND flag != 'normal'"),
        )

    # ── 5. Composite: lab_orders(patient_id, created_at DESC) ─────────────────
    # Speeds up citizen portal: ORDER BY created_at DESC for a patient's orders
    if not _index_exists(conn, "ix_lab_orders_patient_created"):
        op.create_index(
            "ix_lab_orders_patient_created",
            "lab_orders",
            ["patient_id", sa.text("created_at DESC")],
            unique=False,
        )


def downgrade():
    conn = op.get_bind()
    for idx in [
        "ix_lab_orders_patient_created",
        "ix_lab_results_flag_abnormal",
        "ix_patients_nid_hash",
        "ix_patients_phone_lab",
    ]:
        if _index_exists(conn, idx):
            op.drop_index(idx)

    if _table_exists(conn, "lab_results") and _column_exists(conn, "lab_results", "version"):
        op.drop_column("lab_results", "version")
