"""Create canonical_patients, patient_links, citizen_links tables

Revision ID: 20260716_0016
Revises: 20260716_0015
Create Date: 2026-07-16

Tables:
  - canonical_patients  — unified identity bridging LIMS patients and national citizens
  - patient_links       — bridge from patients → canonical_patients
  - citizen_links       — bridge from citizens → canonical_patients
"""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260716_0016"
down_revision: str | None = "20260716_0015"


def _table_exists(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def _has_column(table: str, column: str) -> bool:
    conn = op.get_bind()
    if not conn.dialect.has_table(conn, table):
        return False
    insp = sa.inspect(conn)
    cols = [c["name"] for c in insp.get_columns(table)]
    return column in cols


def upgrade() -> None:
    if not _table_exists("canonical_patients"):
        op.create_table(
            "canonical_patients",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("lab_id", sa.Integer(), nullable=True),
            sa.Column("national_id_hash", sa.String(length=255), nullable=True),
            sa.Column("health_id", sa.String(length=20), nullable=True),
            sa.Column("full_name", sa.String(length=300), nullable=False),
            sa.Column("full_name_ar", sa.String(length=300), nullable=True),
            sa.Column("date_of_birth", sa.DateTime(timezone=True), nullable=True),
            sa.Column("gender", sa.String(length=1), nullable=True),
            sa.Column("phone", sa.String(length=30), nullable=True),
            sa.Column("email", sa.String(length=200), nullable=True),
            sa.Column("address", sa.String(length=500), nullable=True),
            sa.Column("province", sa.String(length=100), nullable=True),
            sa.Column("district", sa.String(length=100), nullable=True),
            sa.Column("blood_type", sa.String(length=5), nullable=True),
            sa.Column("mpi_score", sa.Float(), nullable=True),
            sa.Column("is_verified", sa.Boolean(), nullable=True, server_default=sa.text("false")),
            sa.Column("is_deceased", sa.Boolean(), nullable=True, server_default=sa.text("false")),
            sa.Column("source_system", sa.String(length=50), nullable=True),
            sa.Column("source_id", sa.String(length=100), nullable=True),
            sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(
                ["lab_id"], ["labs.id"], ondelete="SET NULL",
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_canonical_patients_nid_hash",
            "canonical_patients",
            ["national_id_hash"],
        )
        op.create_index(
            "ix_canonical_patients_health_id",
            "canonical_patients",
            ["health_id"],
        )
        op.create_index(
            "ix_canonical_patients_name",
            "canonical_patients",
            ["full_name"],
        )
        op.create_index(
            "ix_canonical_patients_lab_id",
            "canonical_patients",
            ["lab_id"],
        )
        op.create_index(
            "ix_canonical_patients_source",
            "canonical_patients",
            ["source_system", "source_id"],
        )

    if not _table_exists("patient_links"):
        op.create_table(
            "patient_links",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("patient_id", sa.Integer(), nullable=False),
            sa.Column("canonical_id", sa.BigInteger(), nullable=False),
            sa.Column("linkage_method", sa.String(length=30), nullable=False),
            sa.Column("confidence", sa.Float(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(
                ["patient_id"], ["patients.id"], ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["canonical_id"], ["canonical_patients.id"], ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_patient_links_patient", "patient_links", ["patient_id"],
        )
        op.create_index(
            "ix_patient_links_canonical", "patient_links", ["canonical_id"],
        )
        op.create_index(
            "ix_patient_links_method", "patient_links", ["linkage_method"],
        )

    if not _table_exists("citizen_links"):
        op.create_table(
            "citizen_links",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("citizen_id", sa.BigInteger(), nullable=False),
            sa.Column("canonical_id", sa.BigInteger(), nullable=False),
            sa.Column("linkage_method", sa.String(length=30), nullable=False),
            sa.Column("confidence", sa.Float(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(
                ["citizen_id"], ["citizens.id"], ondelete="RESTRICT",
            ),
            sa.ForeignKeyConstraint(
                ["canonical_id"], ["canonical_patients.id"], ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_citizen_links_citizen", "citizen_links", ["citizen_id"],
        )
        op.create_index(
            "ix_citizen_links_canonical", "citizen_links", ["canonical_id"],
        )
        op.create_index(
            "ix_citizen_links_method", "citizen_links", ["linkage_method"],
        )


def downgrade() -> None:
    if _table_exists("citizen_links"):
        op.drop_table("citizen_links")
    if _table_exists("patient_links"):
        op.drop_table("patient_links")
    if _table_exists("canonical_patients"):
        op.drop_table("canonical_patients")
