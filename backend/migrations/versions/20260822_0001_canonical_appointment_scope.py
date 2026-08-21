"""Add canonical clinical scope to national scheduling appointments.

Revision ID: 20260822_0001
Revises: 20260821_0001
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any, cast

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Inspector

revision: str = "20260822_0001"
down_revision: str = "20260821_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = "national_scheduling_appointments"
_COLUMNS: dict[str, Any] = {
    "organization_id": sa.String(length=26),
    "workspace_id": sa.String(length=26),
    "department_id": sa.String(length=26),
    "tenant_id": sa.Integer(),
    "legacy_lab_id": sa.Integer(),
    "idempotency_key": sa.String(length=128),
}


def _existing_columns() -> set[str]:
    bind = op.get_bind()
    inspector = cast(Inspector, sa.inspect(bind))
    return {column["name"] for column in inspector.get_columns(_TABLE)}


def _existing_indexes() -> set[str]:
    bind = op.get_bind()
    inspector = cast(Inspector, sa.inspect(bind))
    return {index["name"] for index in inspector.get_indexes(_TABLE) if index["name"]}


def upgrade() -> None:
    existing_columns = _existing_columns()
    for name, column_type in _COLUMNS.items():
        if name not in existing_columns:
            op.add_column(_TABLE, sa.Column(name, column_type, nullable=True))

    existing_indexes = _existing_indexes()
    indexes = {
        "ix_nat_sched_appt_org_workspace": ["organization_id", "workspace_id"],
        "ix_nat_sched_appt_tenant_scope": ["tenant_id", "facility_id", "workspace_id"],
        "ix_nat_sched_appt_idempotency_scope": ["organization_id", "workspace_id", "idempotency_key"],
    }
    for name, columns in indexes.items():
        if name not in existing_indexes:
            op.create_index(name, _TABLE, columns, unique=False)


def downgrade() -> None:
    # Additive-only policy: do not drop production columns or indexes.
    return None
