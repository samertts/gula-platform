"""stats/trends performance indexes

Revision ID: 20260503_0001
Revises: 20260428_0001
Create Date: 2026-05-03

Adds targeted composite indexes to accelerate the new /stats/* endpoints
and common dashboard/reporting queries.

1. ix_lab_results_lab_created  — (lab_orders.lab_id, lab_results.created_at DESC)
   Covers daily/weekly trends GROUP BY date with lab isolation.
2. ix_lab_results_test_lab     — (lab_results.test_name, lab_orders.lab_id)
   Covers test-frequency aggregations scoped to a lab.
3. ix_lab_orders_lab_status    — (lab_orders.lab_id, lab_orders.status, lab_orders.created_at DESC)
   Covers turnaround-time query (WHERE lab_id = ? AND status = 'completed').
4. ix_lab_results_flag_created — (lab_results.flag, lab_results.created_at DESC)
   WHERE flag = 'critical' ordered by date — accelerates critical-alert dashboard.
5. ix_patients_lab_created     — (patients.lab_id, patients.created_at DESC)
   Covers patient-growth weekly trend query.
6. ix_lab_orders_lab_created   — (lab_orders.lab_id, lab_orders.created_at DESC)
   Covers order-count queries by lab scoped to time windows.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


revision = "20260503_0001"
down_revision = "20260428_0001"
branch_labels = None
depends_on = None


def _index_exists(conn, index_name: str) -> bool:
    inspector = Inspector.from_engine(conn)
    for table in inspector.get_table_names():
        for idx in inspector.get_indexes(table):
            if idx["name"] == index_name:
                return True
    return False


def _table_exists(conn, table: str) -> bool:
    return table in Inspector.from_engine(conn).get_table_names()


def upgrade():
    conn = op.get_bind()

    # 1. lab_orders: (lab_id, created_at DESC) — covers all time-windowed order counts
    if not _index_exists(conn, "ix_lab_orders_lab_created"):
        op.create_index(
            "ix_lab_orders_lab_created",
            "lab_orders",
            ["lab_id", sa.text("created_at DESC")],
            unique=False,
        )

    # 2. lab_orders: (lab_id, status, created_at DESC) — covers turnaround-time query
    if not _index_exists(conn, "ix_lab_orders_lab_status_created"):
        op.create_index(
            "ix_lab_orders_lab_status_created",
            "lab_orders",
            ["lab_id", "status", sa.text("created_at DESC")],
            unique=False,
        )

    # 3. patients: (lab_id, created_at DESC) — covers patient growth trend
    if not _index_exists(conn, "ix_patients_lab_created"):
        op.create_index(
            "ix_patients_lab_created",
            "patients",
            ["lab_id", sa.text("created_at DESC")],
            unique=False,
        )

    # 4. lab_results: (flag, created_at DESC) — accelerates flag-distribution query
    if not _index_exists(conn, "ix_lab_results_flag_created"):
        op.create_index(
            "ix_lab_results_flag_created",
            "lab_results",
            ["flag", sa.text("created_at DESC")],
            unique=False,
        )

    # 5. lab_results: (test_name, created_at DESC) — accelerates test-frequency query
    if not _index_exists(conn, "ix_lab_results_testname_created"):
        op.create_index(
            "ix_lab_results_testname_created",
            "lab_results",
            ["test_name", sa.text("created_at DESC")],
            unique=False,
        )

    # 6. lab_results: (order_id, created_at DESC) — speeds up per-order result listing
    if not _index_exists(conn, "ix_lab_results_order_created"):
        op.create_index(
            "ix_lab_results_order_created",
            "lab_results",
            ["order_id", sa.text("created_at DESC")],
            unique=False,
        )


def downgrade():
    conn = op.get_bind()
    for idx_name in [
        "ix_lab_results_order_created",
        "ix_lab_results_testname_created",
        "ix_lab_results_flag_created",
        "ix_patients_lab_created",
        "ix_lab_orders_lab_status_created",
        "ix_lab_orders_lab_created",
    ]:
        if _index_exists(conn, idx_name):
            op.drop_index(idx_name)
