"""Vaccine inventory, stock movements, and cold-chain readings.

Revision ID: 20260816_0028
Revises: 20260816_0027

Prepared locally; not executed by this change set.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import context, op

revision = "20260816_0028"
down_revision = "20260816_0027"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    if context.is_offline_mode():
        return False
    return bool(sa.inspect(op.get_bind()).has_table(name))


def _audit_columns() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
    ]


def upgrade() -> None:
    if not _has_table("ph_vaccine_catalog"):
        op.create_table(
            "ph_vaccine_catalog",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            *_audit_columns(),
            sa.Column("vaccine_code", sa.String(40), nullable=False),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("name_ar", sa.String(200), nullable=True),
            sa.Column("unit", sa.String(24), nullable=False, server_default="dose"),
            sa.Column("manufacturer", sa.String(200), nullable=True),
            sa.Column("storage_min_c", sa.Float(), nullable=True),
            sa.Column("storage_max_c", sa.Float(), nullable=True),
            sa.Column("source_reference", sa.String(500), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.UniqueConstraint("lab_id", "vaccine_code", name="uq_ph_vaccine_catalog_lab_code"),
        )
    if not _has_table("ph_vaccine_lots"):
        op.create_table(
            "ph_vaccine_lots",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            *_audit_columns(),
            sa.Column("catalog_id", sa.String(26), nullable=False),
            sa.Column("lot_number", sa.String(100), nullable=False),
            sa.Column("expiry_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("received_quantity", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("available_quantity", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("quarantined", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("quarantine_reason", sa.Text(), nullable=True),
            sa.Column("storage_equipment_id", sa.String(100), nullable=True),
            sa.UniqueConstraint("lab_id", "catalog_id", "lot_number", name="uq_ph_vaccine_lot_lab_catalog_lot"),
        )
    if not _has_table("ph_vaccine_stock_movements"):
        op.create_table(
            "ph_vaccine_stock_movements",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            *_audit_columns(),
            sa.Column("lot_id", sa.String(26), nullable=False),
            sa.Column("movement_type", sa.String(24), nullable=False),
            sa.Column("quantity", sa.Integer(), nullable=False),
            sa.Column("reference_type", sa.String(40), nullable=True),
            sa.Column("reference_id", sa.String(100), nullable=True),
            sa.Column("idempotency_key", sa.String(160), nullable=False),
            sa.Column("reason", sa.Text(), nullable=True),
            sa.Column("performed_by", sa.String(100), nullable=False),
            sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("idempotency_key", name="uq_ph_vaccine_movement_idempotency"),
        )
    if not _has_table("ph_cold_chain_readings"):
        op.create_table(
            "ph_cold_chain_readings",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            *_audit_columns(),
            sa.Column("equipment_id", sa.String(100), nullable=False),
            sa.Column("reading_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("temperature_c", sa.Float(), nullable=False),
            sa.Column("minimum_allowed_c", sa.Float(), nullable=True),
            sa.Column("maximum_allowed_c", sa.Float(), nullable=True),
            sa.Column("status", sa.String(24), nullable=False, server_default="within_range"),
            sa.Column("source", sa.String(24), nullable=False, server_default="manual"),
            sa.Column("recorded_by", sa.String(100), nullable=False),
            sa.Column("alert_acknowledged", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("notes", sa.Text(), nullable=True),
        )
    for table, name, columns in (
        ("ph_vaccine_catalog", "ix_ph_vaccine_catalog_lab_code", ["lab_id", "vaccine_code"]),
        ("ph_vaccine_lots", "ix_ph_vaccine_lots_lab_expiry", ["lab_id", "expiry_date"]),
        ("ph_vaccine_lots", "ix_ph_vaccine_lots_equipment", ["storage_equipment_id"]),
        ("ph_vaccine_stock_movements", "ix_ph_vaccine_movements_lab_lot", ["lab_id", "lot_id"]),
        ("ph_vaccine_stock_movements", "ix_ph_vaccine_movements_reference", ["reference_type", "reference_id"]),
        ("ph_cold_chain_readings", "ix_ph_cold_chain_lab_status", ["lab_id", "status"]),
        ("ph_cold_chain_readings", "ix_ph_cold_chain_equipment_time", ["equipment_id", "reading_at"]),
    ):
        if _has_table(table) and name not in {item["name"] for item in sa.inspect(op.get_bind()).get_indexes(table)}:
            op.create_index(name, table, columns)


def downgrade() -> None:
    for table in ("ph_cold_chain_readings", "ph_vaccine_stock_movements", "ph_vaccine_lots", "ph_vaccine_catalog"):
        if _has_table(table):
            op.drop_table(table)
