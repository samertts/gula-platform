"""Performance indexes + audit_logs append-only protection.

Changes:
  - Index lab_orders(lab_id)       — list_orders query (N+1 fix)
  - Index lab_orders(created_at)   — pagination sorting
  - Index lab_results(order_id)    — eager-load results per order
  - Index audit_logs(user_id, created_at) — audit log filtering
  - Index lab_users(role)          — role-based filtering
  - PostgreSQL trigger: make audit_logs append-only
    (UPDATE and DELETE raise an exception at DB level — not bypassable from app)
  - lab_orders.doctor_user_id column — links order to a doctor account

Revision ID: 20250322_0002
Revises    : 20250322_0001
Create Date: 2025-03-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

revision = "20250322_0002"
down_revision = "20250322_0001"
branch_labels = None
depends_on = None


def _index_exists(table: str, index_name: str) -> bool:
    bind = op.get_bind()
    insp = inspect(bind)
    return any(i["name"] == index_name for i in insp.get_indexes(table))


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    insp = inspect(bind)
    return column in [c["name"] for c in insp.get_columns(table)]


def _is_postgresql() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    # ── Performance indexes ────────────────────────────────────────────────────
    if not _index_exists("lab_orders", "ix_lab_orders_lab_id"):
        op.create_index("ix_lab_orders_lab_id", "lab_orders", ["lab_id"])
    if not _index_exists("lab_orders", "ix_lab_orders_created_at"):
        op.create_index("ix_lab_orders_created_at", "lab_orders", ["created_at"])
    if not _index_exists("lab_results", "ix_lab_results_order_id"):
        op.create_index("ix_lab_results_order_id", "lab_results", ["order_id"])
    if not _index_exists("lab_users", "ix_lab_users_role"):
        op.create_index("ix_lab_users_role", "lab_users", ["role"])
    if not _index_exists("audit_logs", "ix_audit_logs_user_created"):
        op.create_index(
            "ix_audit_logs_user_created", "audit_logs",
            ["user_id", "created_at"],
        )

    # ── doctor_user_id on lab_orders ──────────────────────────────────────────
    bind = op.get_bind()
    if not _has_column("lab_orders", "doctor_user_id"):
        if bind.dialect.name == "sqlite":
            with op.batch_alter_table("lab_orders", recreate="always") as batch_op:
                batch_op.add_column(sa.Column("doctor_user_id", sa.Integer(), nullable=True))
                batch_op.create_foreign_key(
                    "fk_lab_orders_doctor_user_id",
                    "lab_users",
                    ["doctor_user_id"],
                    ["id"],
                    ondelete="SET NULL",
                )
        else:
            op.add_column(
                "lab_orders",
                sa.Column(
                    "doctor_user_id",
                    sa.Integer(),
                    sa.ForeignKey("lab_users.id", ondelete="SET NULL"),
                    nullable=True,
                ),
            )
        op.create_index("ix_lab_orders_doctor_user_id", "lab_orders", ["doctor_user_id"])

    # ── audit_logs append-only trigger (PostgreSQL only) ─────────────────────
    # This is a DB-level lock: even if the app is compromised, audit rows
    # cannot be modified or deleted.  Checked in both UPDATE and DELETE.
    if _is_postgresql():
        op.execute(text("""
            CREATE OR REPLACE FUNCTION audit_logs_deny_mutation()
            RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN
                RAISE EXCEPTION
                    'audit_logs is append-only: % operation is not permitted',
                    TG_OP;
            END;
            $$;
        """))

        # Drop existing triggers before recreating (idempotent)
        op.execute(text("""
            DROP TRIGGER IF EXISTS trg_audit_logs_no_update ON audit_logs;
            DROP TRIGGER IF EXISTS trg_audit_logs_no_delete ON audit_logs;
        """))

        op.execute(text("""
            CREATE TRIGGER trg_audit_logs_no_update
            BEFORE UPDATE ON audit_logs
            FOR EACH ROW EXECUTE FUNCTION audit_logs_deny_mutation();
        """))

        op.execute(text("""
            CREATE TRIGGER trg_audit_logs_no_delete
            BEFORE DELETE ON audit_logs
            FOR EACH ROW EXECUTE FUNCTION audit_logs_deny_mutation();
        """))


def downgrade() -> None:
    if _is_postgresql():
        op.execute(text("DROP TRIGGER IF EXISTS trg_audit_logs_no_update ON audit_logs;"))
        op.execute(text("DROP TRIGGER IF EXISTS trg_audit_logs_no_delete ON audit_logs;"))
        op.execute(text("DROP FUNCTION IF EXISTS audit_logs_deny_mutation();"))

    bind = op.get_bind()
    insp = inspect(bind)

    if _has_column("lab_orders", "doctor_user_id"):
        if _index_exists("lab_orders", "ix_lab_orders_doctor_user_id"):
            op.drop_index("ix_lab_orders_doctor_user_id", "lab_orders")
        if bind.dialect.name == "sqlite":
            foreign_keys = insp.get_foreign_keys("lab_orders")
            with op.batch_alter_table("lab_orders", recreate="always") as batch_op:
                for foreign_key in foreign_keys:
                    if "doctor_user_id" in (foreign_key.get("constrained_columns") or ()) and foreign_key.get("name"):
                        batch_op.drop_constraint(foreign_key["name"], type_="foreignkey")
                batch_op.drop_column("doctor_user_id")
        else:
            op.drop_column("lab_orders", "doctor_user_id")

    for idx, tbl in [
        ("ix_audit_logs_user_created", "audit_logs"),
        ("ix_lab_users_role", "lab_users"),
        ("ix_lab_results_order_id", "lab_results"),
        ("ix_lab_orders_created_at", "lab_orders"),
        ("ix_lab_orders_lab_id", "lab_orders"),
    ]:
        if _index_exists(tbl, idx):
            op.drop_index(idx, tbl)
