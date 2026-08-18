"""Add family_id_hash and guardian_id to patients table.

family_id_hash — HMAC of the civil-registry family number; links all
                 family members for the GET /patients/family/{id} endpoint.

guardian_id    — FK → patients.id; links a minor (< 18 yrs) to their
                 parent/guardian so paediatric records are browsable from
                 the guardian's profile via GET /patients/{id}/children.

Changes:
  patients:
    + family_id_hash  VARCHAR(255) NULL, INDEXED
    + guardian_id     INTEGER NULL, FK → patients.id, INDEXED

Revision ID : 20260324_0006
Revises     : 20250323_0005
Create Date : 2026-03-24
"""

from alembic import context, op
import sqlalchemy as sa
from sqlalchemy import inspect, text

revision      = "20260324_0006"
down_revision = "20250323_0005"
branch_labels = None
depends_on    = None


def _col_exists(table: str, col: str) -> bool:
    if context.is_offline_mode():
        return False
    cols = [c["name"] for c in inspect(op.get_bind()).get_columns(table)]
    return col in cols


def _table_exists(table: str) -> bool:
    if context.is_offline_mode():
        return True
    return inspect(op.get_bind()).has_table(table)


def upgrade() -> None:
    if not _table_exists("patients"):
        return

    # --- family_id_hash -------------------------------------------------------
    if not _col_exists("patients", "family_id_hash"):
        op.add_column(
            "patients",
            sa.Column("family_id_hash", sa.String(255), nullable=True),
        )
        op.create_index(
            "ix_patients_family_id_hash",
            "patients",
            ["family_id_hash"],
        )

    # --- guardian_id ----------------------------------------------------------
    if not _col_exists("patients", "guardian_id"):
        op.add_column(
            "patients",
            sa.Column("guardian_id", sa.Integer(), nullable=True),
        )
        # FK with SET NULL on delete — removing a guardian keeps the child record
        op.create_foreign_key(
            "fk_patients_guardian_id",
            "patients", "patients",
            ["guardian_id"], ["id"],
            ondelete="SET NULL",
        )
        op.create_index(
            "ix_patients_guardian_id",
            "patients",
            ["guardian_id"],
        )


def downgrade() -> None:
    if not _table_exists("patients"):
        return

    if _col_exists("patients", "guardian_id"):
        op.drop_index("ix_patients_guardian_id", table_name="patients")
        op.drop_constraint("fk_patients_guardian_id", "patients", type_="foreignkey")
        op.drop_column("patients", "guardian_id")

    if _col_exists("patients", "family_id_hash"):
        op.drop_index("ix_patients_family_id_hash", table_name="patients")
        op.drop_column("patients", "family_id_hash")
