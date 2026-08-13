"""Add explicit operational scope references to NIAM assignments.

Revision ID: 20260813_0003
Revises: 20260813_0002
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260813_0003"
down_revision = "20260813_0002"
branch_labels = None
depends_on = None


_TABLE = "niam_assignments"
_ORG_COLUMN = "clinical_organization_resource_id"
_FACILITY_COLUMN = "clinical_facility_resource_id"


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if _TABLE not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns(_TABLE)}
    if _ORG_COLUMN not in existing_columns:
        op.add_column(_TABLE, sa.Column(_ORG_COLUMN, sa.Integer(), nullable=True))
        op.create_index(f"ix_{_TABLE}_{_ORG_COLUMN}", _TABLE, [_ORG_COLUMN])
    if _FACILITY_COLUMN not in existing_columns:
        op.add_column(_TABLE, sa.Column(_FACILITY_COLUMN, sa.Integer(), nullable=True))
        op.create_index(f"ix_{_TABLE}_{_FACILITY_COLUMN}", _TABLE, [_FACILITY_COLUMN])

    # SQLite cannot add foreign-key constraints after table creation. The ORM model
    # still declares them for new schemas; production databases receive the named
    # constraints through this migration.
    if bind.dialect.name != "sqlite":
        foreign_keys = {foreign_key["name"] for foreign_key in inspector.get_foreign_keys(_TABLE)}
        if "fk_niam_assignments_clinical_org_resource" not in foreign_keys:
            op.create_foreign_key(
                "fk_niam_assignments_clinical_org_resource",
                _TABLE,
                "organizations",
                [_ORG_COLUMN],
                ["id"],
                ondelete="SET NULL",
            )
        if "fk_niam_assignments_clinical_facility_resource" not in foreign_keys:
            op.create_foreign_key(
                "fk_niam_assignments_clinical_facility_resource",
                _TABLE,
                "facilities",
                [_FACILITY_COLUMN],
                ["id"],
                ondelete="SET NULL",
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if _TABLE not in inspector.get_table_names():
        return

    if bind.dialect.name != "sqlite":
        foreign_keys = {foreign_key["name"] for foreign_key in inspector.get_foreign_keys(_TABLE)}
        if "fk_niam_assignments_clinical_facility_resource" in foreign_keys:
            op.drop_constraint("fk_niam_assignments_clinical_facility_resource", _TABLE, type_="foreignkey")
        if "fk_niam_assignments_clinical_org_resource" in foreign_keys:
            op.drop_constraint("fk_niam_assignments_clinical_org_resource", _TABLE, type_="foreignkey")

    existing_columns = {column["name"] for column in inspector.get_columns(_TABLE)}
    if _FACILITY_COLUMN in existing_columns:
        op.drop_index(f"ix_{_TABLE}_{_FACILITY_COLUMN}", table_name=_TABLE)
        op.drop_column(_TABLE, _FACILITY_COLUMN)
    if _ORG_COLUMN in existing_columns:
        op.drop_index(f"ix_{_TABLE}_{_ORG_COLUMN}", table_name=_TABLE)
        op.drop_column(_TABLE, _ORG_COLUMN)
