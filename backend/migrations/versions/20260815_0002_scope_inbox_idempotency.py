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
down_revision: Union[str, None] = "20260815_0001"
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
    if _OLD_CONSTRAINT in constraints:
        op.drop_constraint(_OLD_CONSTRAINT, _TABLE, type_="unique")

    constraints = {item["name"] for item in sa.inspect(bind).get_unique_constraints(_TABLE)}
    if _NEW_CONSTRAINT not in constraints:
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
    if _NEW_CONSTRAINT in constraints:
        op.drop_constraint(_NEW_CONSTRAINT, _TABLE, type_="unique")
    constraints = {item["name"] for item in sa.inspect(bind).get_unique_constraints(_TABLE)}
    if _OLD_CONSTRAINT not in constraints:
        op.create_unique_constraint(_OLD_CONSTRAINT, _TABLE, ["idempotency_key"])
