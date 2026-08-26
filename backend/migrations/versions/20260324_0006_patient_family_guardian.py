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

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

revision      = "20260324_0006"
down_revision = "20250323_0005"
branch_labels = None
depends_on    = None


def _col_exists(table: str, col: str) -> bool:
    cols = [c["name"] for c in inspect(op.get_bind()).get_columns(table)]
    return col in cols


def _table_exists(table: str) -> bool:
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
    bind = op.get_bind()
    guardian_exists = _col_exists("patients", "guardian_id")
    guardian_fk_exists = any(
        foreign_key.get("name") == "fk_patients_guardian_id"
        for foreign_key in inspect(bind).get_foreign_keys("patients")
    )
    if not guardian_exists:
        if bind.dialect.name == "sqlite":
            with op.batch_alter_table("patients", recreate="always") as batch_op:
                batch_op.add_column(sa.Column("guardian_id", sa.Integer(), nullable=True))
                batch_op.create_foreign_key(
                    "fk_patients_guardian_id",
                    "patients",
                    ["guardian_id"],
                    ["id"],
                    ondelete="SET NULL",
                )
        else:
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
        op.create_index("ix_patients_guardian_id", "patients", ["guardian_id"])
    elif not guardian_fk_exists:
        if bind.dialect.name == "sqlite":
            with op.batch_alter_table("patients", recreate="always") as batch_op:
                batch_op.create_foreign_key(
                    "fk_patients_guardian_id",
                    "patients",
                    ["guardian_id"],
                    ["id"],
                    ondelete="SET NULL",
                )
        else:
            op.create_foreign_key(
                "fk_patients_guardian_id",
                "patients", "patients",
                ["guardian_id"], ["id"],
                ondelete="SET NULL",
            )
    if "ix_patients_guardian_id" not in {
        index["name"] for index in inspect(bind).get_indexes("patients")
    }:
        op.create_index("ix_patients_guardian_id", "patients", ["guardian_id"])


def downgrade() -> None:
    if not _table_exists("patients"):
        return

    bind = op.get_bind()
    inspector = inspect(bind)
    patient_columns = {
        column["name"] for column in inspector.get_columns("patients")
    }
    index_names = {index["name"] for index in inspector.get_indexes("patients")}
    foreign_keys = inspector.get_foreign_keys("patients")
    guardian_fk = next(
        (
            foreign_key
            for foreign_key in foreign_keys
            if foreign_key.get("name") == "fk_patients_guardian_id"
        ),
        None,
    )
    if "ix_patients_guardian_id" in index_names:
        op.drop_index("ix_patients_guardian_id", table_name="patients")
    if "ix_patients_family_id_hash" in index_names:
        op.drop_index("ix_patients_family_id_hash", table_name="patients")

    if bind.dialect.name == "sqlite":
        if "guardian_id" in patient_columns or "family_id_hash" in patient_columns:
            with op.batch_alter_table("patients", recreate="always") as batch_op:
                if guardian_fk and guardian_fk.get("name"):
                    batch_op.drop_constraint(
                        guardian_fk["name"],
                        type_="foreignkey",
                    )
                if "guardian_id" in patient_columns:
                    batch_op.drop_column("guardian_id")
                if "family_id_hash" in patient_columns:
                    batch_op.drop_column("family_id_hash")
    else:
        if guardian_fk and guardian_fk.get("name"):
            op.drop_constraint(guardian_fk["name"], "patients", type_="foreignkey")
        if "guardian_id" in patient_columns:
            op.drop_column("patients", "guardian_id")
        if "family_id_hash" in patient_columns:
            op.drop_column("patients", "family_id_hash")
