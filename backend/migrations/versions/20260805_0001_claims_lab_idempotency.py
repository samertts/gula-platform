"""Scope idempotency keys per lab (composite unique) for insurance claims.

Revision ID: 20260805_0001
Revises: 20260804_0001
Create Date: 2026-08-05

The `claims.idempotency_key` column was created with a GLOBAL unique
constraint (`unique=True`), but the service contract (create_claim) scopes
idempotency per lab: "If a claim with that key already exists for this lab".
Two labs that happen to reuse the same key (e.g. their own `order-123`
numbering) would collide and surface as an IntegrityError 500.

Fix: drop the global constraint and add a composite unique index on
(lab_id, idempotency_key), matching the service query. The composite is
strictly weaker than the global one, so existing data always satisfies it.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20260805_0001"
down_revision = "20260804_0001"
branch_labels = None
depends_on = None

_UNIQUE_INDEX = "uq_claims_lab_idempotency"


def _dialect(bind) -> str:
    return bind.dialect.name


def upgrade() -> None:
    bind = op.get_bind()

    # Drop the GLOBAL unique constraint created by the original migration
    # (`idempotency_key ... unique=True`). Postgres auto-names it
    # `claims_idempotency_key_key`; other dialects bake it into the table
    # definition and are rebuilt through the model on fresh create_all.
    if _dialect(bind) == "postgresql":
        op.execute("ALTER TABLE claims DROP CONSTRAINT IF EXISTS claims_idempotency_key_key")

    if not _index_exists(_UNIQUE_INDEX):
        op.create_index(
            _UNIQUE_INDEX,
            "claims",
            ["lab_id", "idempotency_key"],
            unique=True,
        )


def downgrade() -> None:
    bind = op.get_bind()
    if _index_exists(_UNIQUE_INDEX):
        op.drop_index(_UNIQUE_INDEX, table_name="claims")
    if _dialect(bind) == "postgresql":
        op.execute(
            "ALTER TABLE claims ADD CONSTRAINT claims_idempotency_key_key "
            "UNIQUE (idempotency_key)"
        )


def _index_exists(index: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    for table in inspector.get_table_names():
        idx_names = [i["name"] for i in inspector.get_indexes(table)]
        if index in idx_names:
            return True
    return False
