"""Add explicit government-hospital scope and idempotency to appointments.

Revision ID: 20260817_0023
Revises: 20260815_0022
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260817_0023"
down_revision: str | None = "20260815_0022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _column_exists(table: str, column: str) -> bool:
    inspector = inspect(op.get_bind())
    return any(item["name"] == column for item in inspector.get_columns(table))


def _index_exists(table: str, index_name: str) -> bool:
    inspector = inspect(op.get_bind())
    return any(item["name"] == index_name for item in inspector.get_indexes(table))


def upgrade() -> None:
    if not _column_exists("national_appointments", "hospital_id"):
        op.add_column("national_appointments", sa.Column("hospital_id", sa.Integer(), nullable=True))
    if not _column_exists("national_appointments", "idempotency_key"):
        op.add_column("national_appointments", sa.Column("idempotency_key", sa.String(length=64), nullable=True))
    if not _index_exists("national_appointments", "ix_national_appointments_hospital_date"):
        op.create_index(
            "ix_national_appointments_hospital_date",
            "national_appointments",
            ["hospital_id", "scheduled_date"],
        )
    if not _index_exists("national_appointments", "ix_national_appointments_idempotency"):
        op.create_index(
            "ix_national_appointments_idempotency",
            "national_appointments",
            ["lab_id", "hospital_id", "idempotency_key"],
            unique=True,
        )


def downgrade() -> None:
    if _index_exists("national_appointments", "ix_national_appointments_idempotency"):
        op.drop_index("ix_national_appointments_idempotency", table_name="national_appointments")
    if _index_exists("national_appointments", "ix_national_appointments_hospital_date"):
        op.drop_index("ix_national_appointments_hospital_date", table_name="national_appointments")
    if _column_exists("national_appointments", "idempotency_key"):
        op.drop_column("national_appointments", "idempotency_key")
    if _column_exists("national_appointments", "hospital_id"):
        op.drop_column("national_appointments", "hospital_id")
