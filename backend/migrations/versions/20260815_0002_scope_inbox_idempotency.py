"""Scope integration inbox idempotency keys by tenant.

The inbox is multi-tenant. A source idempotency key must be reusable by a
separate recipient organisation without exposing or colliding with another
organisation's inbox event.
"""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260815_0002"
down_revision: str | None = "20260815_0001"
branch_labels = None
depends_on = None

_TABLE = "integration_inbox_events"
_OLD_CONSTRAINT = "uq_integration_inbox_idempotency_key"
_NEW_CONSTRAINT = "uq_integration_inbox_tenant_idempotency_key"


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if _TABLE not in inspector.get_table_names():
        return

    constraints = {item["name"] for item in inspector.get_unique_constraints(_TABLE)}
    has_old = _OLD_CONSTRAINT in constraints
    has_new = _NEW_CONSTRAINT in constraints
    if bind.dialect.name == "sqlite":
        if has_old or not has_new:
            with op.batch_alter_table(_TABLE, recreate="always") as batch_op:
                if has_old:
                    batch_op.drop_constraint(_OLD_CONSTRAINT, type_="unique")
                if not has_new:
                    batch_op.create_unique_constraint(
                        _NEW_CONSTRAINT,
                        ["tenant_id", "idempotency_key"],
                    )
    else:
        if has_old:
            op.drop_constraint(_OLD_CONSTRAINT, _TABLE, type_="unique")
        if not has_new:
            op.create_unique_constraint(
                _NEW_CONSTRAINT,
                _TABLE,
                ["tenant_id", "idempotency_key"],
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if _TABLE not in inspector.get_table_names():
        return

    constraints = {item["name"] for item in inspector.get_unique_constraints(_TABLE)}
    has_old = _OLD_CONSTRAINT in constraints
    has_new = _NEW_CONSTRAINT in constraints
    if bind.dialect.name == "sqlite":
        if has_new or not has_old:
            with op.batch_alter_table(_TABLE, recreate="always") as batch_op:
                if has_new:
                    batch_op.drop_constraint(_NEW_CONSTRAINT, type_="unique")
                if not has_old:
                    batch_op.create_unique_constraint(_OLD_CONSTRAINT, ["idempotency_key"])
    else:
        if has_new:
            op.drop_constraint(_NEW_CONSTRAINT, _TABLE, type_="unique")
        if not has_old:
            op.create_unique_constraint(_OLD_CONSTRAINT, _TABLE, ["idempotency_key"])
