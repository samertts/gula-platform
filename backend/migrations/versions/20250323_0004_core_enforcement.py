"""Core DB-level enforcement: optimistic locking + state machine trigger
+ idempotency table + outbox events table.

These are the DB-level guarantees that back up the application-layer rules.
Even if the application is fully compromised, these constraints hold.

Changes:
  lab_orders:
    - ADD COLUMN version INT NOT NULL DEFAULT 1
    - ADD CHECK (status IN (...)) — DB refuses illegal status strings
    - CREATE TRIGGER trg_order_state_machine  — DB refuses illegal transitions
      and prevents ANY update to a validated/locked order

  CREATE TABLE idempotency_keys  — prevents duplicate request processing
  CREATE TABLE outbox_events     — Outbox Pattern for reliable event delivery

Revision ID : 20250323_0004
Revises     : 20250322_0003
Create Date : 2025-03-23
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

revision = "20250323_0004"
down_revision = "20250322_0003"
branch_labels = None
depends_on = None


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _pg() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def _has_column(table: str, col: str) -> bool:
    bind = op.get_bind()
    return col in [c["name"] for c in inspect(bind).get_columns(table)]


def _table_exists(table: str) -> bool:
    bind = op.get_bind()
    return inspect(bind).has_table(table)


def _constraint_exists(table: str, name: str) -> bool:
    if not _pg():
        return False
    bind = op.get_bind()
    row = bind.execute(
        text(
            "SELECT 1 FROM pg_constraint WHERE conname = :name AND conrelid = to_regclass(:table)"
        ),
        {"name": name, "table": table},
    ).fetchone()
    return row is not None


def _trigger_exists(trigger: str, table: str) -> bool:
    if not _pg():
        return False
    bind = op.get_bind()
    row = bind.execute(
        text("SELECT 1 FROM pg_trigger WHERE tgname = :t AND tgrelid = to_regclass(:table)"),
        {"t": trigger, "table": table},
    ).fetchone()
    return row is not None


# ─── Upgrade ─────────────────────────────────────────────────────────────────


def upgrade() -> None:
    # ── 1. Optimistic locking: version column ─────────────────────────────────
    if not _has_column("lab_orders", "version"):
        op.add_column(
            "lab_orders",
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        )

    # ── 2. DB CHECK constraint on status ──────────────────────────────────────
    # Prevents the DB from ever storing an unknown status string.
    if _pg() and not _constraint_exists("lab_orders", "ck_lab_orders_status"):
        op.execute(
            text("""
            ALTER TABLE lab_orders
            ADD CONSTRAINT ck_lab_orders_status
            CHECK (status IN (
                'pending',
                'completed',
                'validated',
                'cancelled'
            ));
        """)
        )

    # ── 3. DB-level state machine trigger ─────────────────────────────────────
    # Even if the application bypasses domain/order_state.py, the DB rejects
    # illegal transitions and mutations to locked orders.
    if _pg():
        op.execute(
            text("""
            CREATE OR REPLACE FUNCTION enforce_order_state_machine()
            RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN
                -- Hard lock: validated or locked orders are immutable
                IF OLD.locked_at IS NOT NULL THEN
                    RAISE EXCEPTION
                        'ORDER_LOCKED: order % was validated at % and is immutable',
                        OLD.id, OLD.locked_at
                    USING ERRCODE = 'P0001';
                END IF;

                -- Status-only changes: enforce valid transitions
                IF OLD.status IS DISTINCT FROM NEW.status THEN
                    IF OLD.status = 'validated' OR OLD.status = 'cancelled' THEN
                        RAISE EXCEPTION
                            'INVALID_TRANSITION: % is a terminal state for order %',
                            OLD.status, OLD.id
                        USING ERRCODE = 'P0001';
                    END IF;

                    IF OLD.status = 'pending'
                        AND NEW.status NOT IN ('completed', 'cancelled') THEN
                        RAISE EXCEPTION
                            'INVALID_TRANSITION: order % cannot go from pending to %',
                            OLD.id, NEW.status
                        USING ERRCODE = 'P0001';
                    END IF;

                    IF OLD.status = 'completed'
                        AND NEW.status NOT IN ('validated', 'cancelled') THEN
                        RAISE EXCEPTION
                            'INVALID_TRANSITION: order % cannot go from completed to %',
                            OLD.id, NEW.status
                        USING ERRCODE = 'P0001';
                    END IF;
                END IF;

                RETURN NEW;
            END;
            $$;
        """)
        )

        op.execute(text("DROP TRIGGER IF EXISTS trg_order_state_machine ON lab_orders;"))
        op.execute(
            text("""
            CREATE TRIGGER trg_order_state_machine
            BEFORE UPDATE ON lab_orders
            FOR EACH ROW
            EXECUTE FUNCTION enforce_order_state_machine();
        """)
        )

    # ── 4. Idempotency keys table ──────────────────────────────────────────────
    # Prevents double-processing of API requests that carry an Idempotency-Key
    # header (create order, enter results, validate, etc.).
    if not _table_exists("idempotency_keys"):
        op.create_table(
            "idempotency_keys",
            sa.Column("key", sa.String(255), primary_key=True),
            sa.Column(
                "lab_id",
                sa.Integer(),
                sa.ForeignKey("labs.id", ondelete="CASCADE"),
                nullable=True,
                index=True,
            ),
            sa.Column("endpoint", sa.String(255), nullable=True),
            sa.Column("status_code", sa.Integer(), nullable=True),
            sa.Column("response_body", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )
        # Auto-expire: keys older than 24 h are irrelevant (CRON cleans them up)
        if _pg():
            op.execute(
                text("""
                CREATE INDEX ix_idempotency_keys_created_at
                ON idempotency_keys (created_at);
            """)
            )

    # ── 5. Outbox events table ────────────────────────────────────────────────
    # Outbox Pattern: events are written IN THE SAME TRANSACTION as the business
    # operation.  A background worker picks them up and delivers them reliably.
    # Even if the broker/email/SMS service is down, nothing is lost.
    if not _table_exists("outbox_events"):
        op.create_table(
            "outbox_events",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("event_type", sa.String(100), nullable=False, index=True),
            sa.Column("aggregate_type", sa.String(100), nullable=True),  # e.g. "order"
            sa.Column("aggregate_id", sa.Integer(), nullable=True, index=True),
            sa.Column("payload", sa.Text(), nullable=False),  # JSON string
            sa.Column(
                "status", sa.String(20), nullable=False, server_default="pending"
            ),  # pending | processing | done | failed
            sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("last_error", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
                index=True,
            ),
            sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        )
        if _pg():
            # Partial index: worker only scans pending/failed rows
            op.execute(
                text("""
                CREATE INDEX ix_outbox_events_pending
                ON outbox_events (created_at ASC)
                WHERE status IN ('pending', 'failed');
            """)
            )


# ─── Downgrade ────────────────────────────────────────────────────────────────


def downgrade() -> None:
    if _pg():
        op.execute(text("DROP TRIGGER IF EXISTS trg_order_state_machine ON lab_orders;"))
        op.execute(text("DROP FUNCTION IF EXISTS enforce_order_state_machine();"))
        op.execute(text("ALTER TABLE lab_orders DROP CONSTRAINT IF EXISTS ck_lab_orders_status;"))

    if _table_exists("outbox_events"):
        op.execute(text("DROP INDEX IF EXISTS ix_outbox_events_pending;"))
        op.drop_table("outbox_events")

    if _table_exists("idempotency_keys"):
        op.execute(text("DROP INDEX IF EXISTS ix_idempotency_keys_created_at;"))
        op.drop_table("idempotency_keys")

    if _has_column("lab_orders", "version"):
        op.drop_column("lab_orders", "version")
