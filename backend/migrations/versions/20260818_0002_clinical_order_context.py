"""Add durable clinical-order context and state fields to lab_orders.

Revision ID: 20260818_0002
Revises: 20260818_0001
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import cast

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.engine import Inspector

revision: str = "20260818_0002"
down_revision: str | None = "20260818_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_COLUMNS: tuple[tuple[str, sa.types.TypeEngine], ...] = (
    ("clinical_status", sa.String(length=24)),
    ("encounter_id", sa.String(length=80)),
    ("ordering_practitioner_id", sa.String(length=80)),
    ("ordering_account_id", sa.Integer()),
    ("organization_id", sa.String(length=80)),
    ("facility_id", sa.String(length=80)),
    ("department_id", sa.String(length=80)),
    ("workspace_id", sa.String(length=80)),
    ("tenant_id", sa.Integer()),
    ("service", sa.String(length=120)),
    ("priority", sa.String(length=20)),
    ("clinical_indication", sa.Text()),
    ("correlation_id", sa.String(length=36)),
    ("updated_at", sa.DateTime(timezone=True)),
)


def _inspector() -> Inspector:
    return cast(Inspector, inspect(op.get_bind()))


def _has_column(table: str, name: str) -> bool:
    return name in {column["name"] for column in _inspector().get_columns(table)}


def _has_index(table: str, name: str) -> bool:
    return any(index["name"] == name for index in _inspector().get_indexes(table))


def upgrade() -> None:
    for name, column_type in _COLUMNS:
        if not _has_column("lab_orders", name):
            kwargs: dict[str, object] = {"nullable": True}
            if name == "updated_at":
                kwargs["server_default"] = sa.func.now()
            op.add_column("lab_orders", sa.Column(name, column_type, **kwargs))

    indexes = {
        "ix_lab_orders_clinical_status": ["clinical_status"],
        "ix_lab_orders_encounter": ["encounter_id"],
        "ix_lab_orders_ordering_practitioner": ["ordering_practitioner_id"],
        "ix_lab_orders_ordering_account": ["ordering_account_id"],
        "ix_lab_orders_organization": ["organization_id"],
        "ix_lab_orders_facility": ["facility_id"],
        "ix_lab_orders_department": ["department_id"],
        "ix_lab_orders_workspace": ["workspace_id"],
        "ix_lab_orders_tenant": ["tenant_id"],
        "ix_lab_orders_correlation": ["correlation_id"],
        "ix_lab_orders_clinical_scope": ["tenant_id", "organization_id", "facility_id", "workspace_id"],
    }
    for name, columns in indexes.items():
        if not _has_index("lab_orders", name):
            op.create_index(name, "lab_orders", columns)

    # Existing rows may be legacy-only and remain NULL until an explicit, audited
    # backfill is approved. New canonical writes require this state in service code.
    if not any(constraint.get("name") == "ck_lab_orders_clinical_status" for constraint in _inspector().get_check_constraints("lab_orders")):
        op.create_check_constraint(
            "ck_lab_orders_clinical_status",
            "lab_orders",
            "clinical_status IS NULL OR clinical_status IN ('DRAFT', 'PLACED', 'ACCEPTED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'REJECTED', 'FAILED', 'EXPIRED')",
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    constraints = {constraint.get("name") for constraint in inspector.get_check_constraints("lab_orders")}
    if "ck_lab_orders_clinical_status" in constraints:
        op.drop_constraint("ck_lab_orders_clinical_status", "lab_orders", type_="check")
    for name in (
        "ix_lab_orders_clinical_scope",
        "ix_lab_orders_correlation",
        "ix_lab_orders_tenant",
        "ix_lab_orders_workspace",
        "ix_lab_orders_department",
        "ix_lab_orders_facility",
        "ix_lab_orders_organization",
        "ix_lab_orders_ordering_account",
        "ix_lab_orders_ordering_practitioner",
        "ix_lab_orders_encounter",
        "ix_lab_orders_clinical_status",
    ):
        if _has_index("lab_orders", name):
            op.drop_index(name, table_name="lab_orders")
    for name, _column_type in reversed(_COLUMNS):
        if _has_column("lab_orders", name):
            op.drop_column("lab_orders", name)
