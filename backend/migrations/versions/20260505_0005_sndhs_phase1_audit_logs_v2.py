"""SNDHS-lite Phase 1 — Step E: append-only ``sndhs_audit_logs``.

The legacy ``audit_logs`` table (Integer PK, hash-chained) remains the
canonical audit log for the existing platform. SNDHS-lite needs a new
audit surface that is:

- UUID-keyed (national-ready),
- purpose-tagged (purpose-based access control),
- append-only at the database level (no UPDATE, no DELETE),
- safe to introduce alongside the existing log.

Rather than mutating ``audit_logs`` (which would break running code
including the chain-hash trigger from migration 0009), this migration
creates a parallel ``sndhs_audit_logs`` table.

Append-only enforcement
-----------------------
A trigger raises an error on UPDATE / DELETE. INSERT remains allowed.
Application code must also avoid UPDATE/DELETE for defence-in-depth;
see ``backend/app/services/sndhs_audit.py`` (added in a follow-up step).

Schema
------
- id          UUID PK   DEFAULT gen_random_uuid()
- user_id     UUID  NULL          (workforce / citizen principal id)
- action      TEXT  NOT NULL
- entity_type TEXT  NOT NULL
- entity_id   UUID  NULL
- purpose     VARCHAR(40) NOT NULL DEFAULT 'unspecified'
- details     JSONB NULL          (free-form metadata)
- created_at  TIMESTAMPTZ DEFAULT now()  NOT NULL

Revision ID : 20260505_0005
Revises     : 20260505_0004
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text
from sqlalchemy.dialects import postgresql


revision = "20260505_0005"
down_revision = "20260505_0004"
branch_labels = None
depends_on = None


def _table_exists(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def _pg() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    if _table_exists("sndhs_audit_logs"):
        return

    if _pg():
        op.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))

    pk_default = sa.text("gen_random_uuid()") if _pg() else None

    op.create_table(
        "sndhs_audit_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True) if _pg() else sa.String(36),
            primary_key=True,
            server_default=pk_default,
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True) if _pg() else sa.String(36),
            nullable=True,
        ),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("entity_type", sa.Text(), nullable=False),
        sa.Column(
            "entity_id",
            postgresql.UUID(as_uuid=True) if _pg() else sa.String(36),
            nullable=True,
        ),
        sa.Column(
            "purpose",
            sa.String(40),
            nullable=False,
            server_default="unspecified",
        ),
        sa.Column(
            "details",
            postgresql.JSONB(astext_type=sa.Text()) if _pg() else sa.JSON(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index("ix_sndhs_audit_logs_user_id", "sndhs_audit_logs", ["user_id"])
    op.create_index("ix_sndhs_audit_logs_entity", "sndhs_audit_logs", ["entity_type", "entity_id"])
    op.create_index("ix_sndhs_audit_logs_action", "sndhs_audit_logs", ["action"])
    op.create_index("ix_sndhs_audit_logs_purpose", "sndhs_audit_logs", ["purpose"])
    op.create_index("ix_sndhs_audit_logs_created_at", "sndhs_audit_logs", ["created_at"])

    if _pg():
        # Append-only enforcement at the database level.
        op.execute(
            text(
                """
            CREATE OR REPLACE FUNCTION sndhs_audit_logs_no_mutation()
            RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION
                    'sndhs_audit_logs is append-only (% blocked)',
                    TG_OP
                    USING ERRCODE = 'P0001';
            END;
            $$ LANGUAGE plpgsql;
            """
            )
        )
        op.execute(
            text("DROP TRIGGER IF EXISTS trg_sndhs_audit_logs_no_update ON sndhs_audit_logs")
        )
        op.execute(
            text(
                "CREATE TRIGGER trg_sndhs_audit_logs_no_update "
                "BEFORE UPDATE ON sndhs_audit_logs "
                "FOR EACH ROW EXECUTE FUNCTION sndhs_audit_logs_no_mutation()"
            )
        )
        op.execute(
            text("DROP TRIGGER IF EXISTS trg_sndhs_audit_logs_no_delete ON sndhs_audit_logs")
        )
        op.execute(
            text(
                "CREATE TRIGGER trg_sndhs_audit_logs_no_delete "
                "BEFORE DELETE ON sndhs_audit_logs "
                "FOR EACH ROW EXECUTE FUNCTION sndhs_audit_logs_no_mutation()"
            )
        )
        # Belt-and-braces: revoke UPDATE / DELETE / TRUNCATE on the role
        # commonly used by the application. The grant must exist; if it
        # doesn't, this REVOKE is a no-op.
        op.execute(
            text(
                "DO $$ BEGIN "
                "  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = current_user) THEN "
                "    EXECUTE format('REVOKE UPDATE, DELETE, TRUNCATE ON sndhs_audit_logs FROM %I', current_user); "
                "  END IF; "
                "EXCEPTION WHEN insufficient_privilege THEN NULL; END $$;"
            )
        )


def downgrade() -> None:
    if not _table_exists("sndhs_audit_logs"):
        return

    if _pg():
        op.execute(
            text("DROP TRIGGER IF EXISTS trg_sndhs_audit_logs_no_delete ON sndhs_audit_logs")
        )
        op.execute(
            text("DROP TRIGGER IF EXISTS trg_sndhs_audit_logs_no_update ON sndhs_audit_logs")
        )
        op.execute(text("DROP FUNCTION IF EXISTS sndhs_audit_logs_no_mutation()"))

    op.drop_index("ix_sndhs_audit_logs_created_at", table_name="sndhs_audit_logs")
    op.drop_index("ix_sndhs_audit_logs_purpose", table_name="sndhs_audit_logs")
    op.drop_index("ix_sndhs_audit_logs_action", table_name="sndhs_audit_logs")
    op.drop_index("ix_sndhs_audit_logs_entity", table_name="sndhs_audit_logs")
    op.drop_index("ix_sndhs_audit_logs_user_id", table_name="sndhs_audit_logs")
    op.drop_table("sndhs_audit_logs")
