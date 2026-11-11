"""Create the three hospital tables 20260820_0004's foreign keys require.

IA-054. A fresh deployment of this platform could not exist. `alembic upgrade
head` on an empty database died at `20260820_0004`:

    sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedTable)
    relation "hospital_operation_theaters" does not exist

That revision creates `hospital_surgical_safety_checklists` with a foreign key
to `hospital_operation_theaters`, and **no migration ever created that table**.
It is the deterministic failure point of every fresh deploy, which is why the
PostgreSQL migration gate on this branch fails at `Apply migration head`.

SCOPE. This creates the exact transitive closure the checklist needs and
nothing more:

    hospitals                      the FK root
    hospital_departments           self-referencing via parent_id
    hospital_operation_theaters    what 20260820_0004 points at

The hospital module declares thirteen tables; only the checklist had a
migration. The other nine are **deliberately not created here**: no migration
references them, so they block nothing, and authoring them would be a larger
schema change made on the way past.

PROVENANCE. Every column, type, foreign key and index below was derived by
compiling `CreateTable`/`CreateIndex` from the ORM models in
`app/hospital/models/__init__.py` against the PostgreSQL dialect, not
transcribed by hand. `HospitalBaseEntity` contributes the audit, tenancy and
optimistic-lock columns (`created_by`, `updated_by`, `created_at`,
`updated_at`, `is_deleted`, `deleted_at`, `lab_id`, `version`).

ONE RULE DELIBERATELY BROKEN, and recorded rather than hidden.
`20260820_0004`'s `down_revision` is changed from `20260819_0003` to this
revision. CLAUDE.md says never to modify an existing migration, because an
existing database may already have run it. That cannot be true of this one:
it is the point at which every fresh upgrade dies, so it has never succeeded
anywhere. Only the linkage changed; not one line of its schema was touched.
`20260819_0003` keeps its other child (`20260819_0004`), so the revision graph
gains no new branch.

Revision ID : 20260820_0003
Revises     : 20260819_0003
Create Date : 2026-08-20
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20260820_0003"
down_revision = "20260819_0003"
branch_labels = None
depends_on = None


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _table_exists(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def _audit_columns() -> list[sa.Column]:
    """The HospitalBaseEntity tail, shared by all three tables.

    Returned fresh each call: a sa.Column instance may only belong to one
    table, so reusing a module-level list silently corrupts the second table.
    """
    return [
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    ]


# ─── Upgrade ─────────────────────────────────────────────────────────────────

def upgrade() -> None:
    if not _table_exists("hospitals"):
        op.create_table(
            "hospitals",
            sa.Column("id", sa.Integer(), nullable=False),
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
            sa.Column("country", sa.String(length=10), nullable=True),
            *_audit_columns(),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_hospitals_id", "hospitals", ["id"])
        op.create_index("ix_hospitals_code", "hospitals", ["code"], unique=True)
        op.create_index("ix_hospitals_hospital_type", "hospitals", ["hospital_type"])
        op.create_index("ix_hospitals_is_active", "hospitals", ["is_active"])
        op.create_index("ix_hospitals_lab_id", "hospitals", ["lab_id"])

    if not _table_exists("hospital_departments"):
        op.create_table(
            "hospital_departments",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("hospital_id", sa.Integer(), nullable=False),
            sa.Column("parent_id", sa.Integer(), nullable=True),
            sa.Column("code", sa.String(length=50), nullable=False),
            sa.Column("name", sa.String(length=300), nullable=False),
            sa.Column("name_ar", sa.String(length=300), nullable=True),
            sa.Column("department_type", sa.String(length=50), nullable=True),
            sa.Column("phone", sa.String(length=20), nullable=True),
            *_audit_columns(),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(
                ["hospital_id"], ["hospitals.id"], ondelete="CASCADE",
            ),
            # self-referencing: a department may sit under another
            sa.ForeignKeyConstraint(
                ["parent_id"], ["hospital_departments.id"], ondelete="SET NULL",
            ),
        )
        op.create_index("ix_hospital_departments_id", "hospital_departments", ["id"])
        op.create_index("ix_hospital_departments_code", "hospital_departments", ["code"])
        op.create_index(
            "ix_hospital_departments_hospital_id", "hospital_departments", ["hospital_id"],
        )
        op.create_index(
            "ix_hospital_departments_parent_id", "hospital_departments", ["parent_id"],
        )
        op.create_index(
            "ix_hospital_departments_department_type",
            "hospital_departments",
            ["department_type"],
        )
        op.create_index(
            "ix_hospital_departments_is_active", "hospital_departments", ["is_active"],
        )
        op.create_index(
            "ix_hospital_departments_lab_id", "hospital_departments", ["lab_id"],
        )

    if not _table_exists("hospital_operation_theaters"):
        op.create_table(
            "hospital_operation_theaters",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("hospital_id", sa.Integer(), nullable=False),
            sa.Column("department_id", sa.Integer(), nullable=True),
            sa.Column("code", sa.String(length=50), nullable=False),
            sa.Column("name", sa.String(length=300), nullable=False),
            sa.Column("name_ar", sa.String(length=300), nullable=True),
            sa.Column("theater_type", sa.String(length=50), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            # No FK: the ORM declares no relationship here, and the surgery
            # table it would point at has no migration either. Adding one
            # would create a second uncreated-target failure of exactly the
            # kind this revision exists to repair.
            sa.Column("current_surgery_id", sa.Integer(), nullable=True),
            *_audit_columns(),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(
                ["hospital_id"], ["hospitals.id"], ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["department_id"], ["hospital_departments.id"], ondelete="SET NULL",
            ),
        )
        for column in (
            "id", "code", "hospital_id", "department_id",
            "theater_type", "status", "is_active", "lab_id",
        ):
            op.create_index(
                f"ix_hospital_operation_theaters_{column}",
                "hospital_operation_theaters",
                [column],
            )


# ─── Downgrade ───────────────────────────────────────────────────────────────

def downgrade() -> None:
    # Reverse FK order. Guarded, so a partially-applied upgrade downgrades
    # cleanly and the round-trip the CI gate runs stays green.
    for table in (
        "hospital_operation_theaters",
        "hospital_departments",
        "hospitals",
    ):
        if _table_exists(table):
            op.drop_table(table)
