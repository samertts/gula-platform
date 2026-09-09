"""Create the Hospital core schema required by the surgical safety checklist.

P0-1.  ``20260820_0004`` declares a foreign key to ``hospital_operation_theaters``,
but no migration ever created that table — the entire Hospital domain existed only
in the ORM.  On a clean database ``20260820_0004`` therefore aborted with
``UndefinedTable`` and the transaction rolled back to ``20260505_0005``, so the
revision never recorded and no migration ordered after it could run.

Scope is deliberately the **minimum dependency closure** of the failure, not the
Hospital domain:

    hospitals  ->  hospital_departments  ->  hospital_operation_theaters

Those three are exactly what ``hospital_operation_theaters`` transitively requires.
The remaining Hospital ORM tables (campuses, buildings, floors, clinics, rooms,
beds, units, medical equipment, cost centres, bed assignments) block nothing and
are deliberately **not** created here; they remain a known ORM/migration gap.

Column definitions are taken from ``app/hospital/models`` and its shared mixins
(``AuditMixin``, ``SoftDeleteMixin``, ``TenantMixin``, ``OptimisticLockMixin``),
and follow the conventions already used by ``20260820_0004`` — notably ``lab_id``
as an indexed column without a foreign key.

Every step is existence-guarded, so the migration is a no-op against a database
that already has these objects and never drops or recreates a data-bearing table.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260820_0003"
down_revision: str | None = "20260819_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def _audit_columns() -> list[sa.Column]:
    """The shared mixin columns every HospitalBaseEntity carries."""
    return [
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        # Indexed explicitly per table below, so that each index carries a
        # table-specific name; index=True here would auto-create a colliding one.
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    ]


def upgrade() -> None:
    if not _table_exists("hospitals"):
        op.create_table(
            "hospitals",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("code", sa.String(length=50), nullable=False),
            sa.Column("name", sa.String(length=300), nullable=False),
            sa.Column("name_ar", sa.String(length=300), nullable=True),
            sa.Column("hospital_type", sa.String(length=50), nullable=False),
            sa.Column("license_number", sa.String(length=100), nullable=True),
            sa.Column("phone", sa.String(length=20), nullable=True),
            sa.Column("email", sa.String(length=200), nullable=True),
            sa.Column("website", sa.String(length=300), nullable=True),
            sa.Column("address", sa.String(length=500), nullable=True),
            sa.Column("city", sa.String(length=100), nullable=True),
            sa.Column("province", sa.String(length=100), nullable=True),
            sa.Column("country", sa.String(length=10), nullable=True, server_default="IQ"),
            *_audit_columns(),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("code", name="uq_hospitals_code"),
        )
        op.create_index("ix_hospitals_code", "hospitals", ["code"])
        op.create_index("ix_hospitals_hospital_type", "hospitals", ["hospital_type"])
        op.create_index("ix_hospitals_lab_id", "hospitals", ["lab_id"])

    if not _table_exists("hospital_departments"):
        op.create_table(
            "hospital_departments",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("hospital_id", sa.Integer(), nullable=False),
            sa.Column("parent_id", sa.Integer(), nullable=True),
            sa.Column("code", sa.String(length=50), nullable=False),
            sa.Column("name", sa.String(length=300), nullable=False),
            sa.Column("name_ar", sa.String(length=300), nullable=True),
            sa.Column("department_type", sa.String(length=50), nullable=True),
            sa.Column("phone", sa.String(length=20), nullable=True),
            *_audit_columns(),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["hospital_id"], ["hospitals.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(
                ["parent_id"], ["hospital_departments.id"], ondelete="SET NULL"
            ),
        )
        op.create_index("ix_hospital_departments_hospital_id", "hospital_departments", ["hospital_id"])
        op.create_index("ix_hospital_departments_parent_id", "hospital_departments", ["parent_id"])
        op.create_index("ix_hospital_departments_code", "hospital_departments", ["code"])
        op.create_index("ix_hospital_departments_type", "hospital_departments", ["department_type"])
        op.create_index("ix_hospital_departments_lab_id", "hospital_departments", ["lab_id"])

    if not _table_exists("hospital_operation_theaters"):
        op.create_table(
            "hospital_operation_theaters",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("hospital_id", sa.Integer(), nullable=False),
            sa.Column("department_id", sa.Integer(), nullable=True),
            sa.Column("code", sa.String(length=50), nullable=False),
            sa.Column("name", sa.String(length=300), nullable=False),
            sa.Column("name_ar", sa.String(length=300), nullable=True),
            sa.Column("theater_type", sa.String(length=50), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="available"),
            sa.Column("current_surgery_id", sa.Integer(), nullable=True),
            *_audit_columns(),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["hospital_id"], ["hospitals.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(
                ["department_id"], ["hospital_departments.id"], ondelete="SET NULL"
            ),
        )
        op.create_index("ix_hospital_theaters_hospital_id", "hospital_operation_theaters", ["hospital_id"])
        op.create_index("ix_hospital_theaters_department_id", "hospital_operation_theaters", ["department_id"])
        op.create_index("ix_hospital_theaters_code", "hospital_operation_theaters", ["code"])
        op.create_index("ix_hospital_theaters_type", "hospital_operation_theaters", ["theater_type"])
        op.create_index("ix_hospital_theaters_status", "hospital_operation_theaters", ["status"])
        op.create_index("ix_hospital_theaters_lab_id", "hospital_operation_theaters", ["lab_id"])


def downgrade() -> None:
    # Dropped in reverse dependency order, and only if present.
    for table in (
        "hospital_operation_theaters",
        "hospital_departments",
        "hospitals",
    ):
        if _table_exists(table):
            op.drop_table(table)
