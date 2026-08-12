"""Create Pharmacy Platform tables.

Creates all Pharmacy domain entities:
  - pharmacy_drug_catalog (global reference data — no lab_id)
  - pharmacy_drug_batches, pharmacy_drug_suppliers
  - pharmacy_prescriptions, pharmacy_prescription_items
  - pharmacy_dispense_records, pharmacy_dispense_queue
  - pharmacy_warehouses, pharmacy_stores, pharmacy_stock_levels
  - pharmacy_stock_movements, pharmacy_inventory_transfers
  - pharmacy_inventory_transfer_items, pharmacy_drug_returns
  - pharmacy_waste_records, pharmacy_recalls
  - pharmacy_inventory_forecasts
  - pharmacy_drug_interaction_rules, pharmacy_contraindication_rules
  - pharmacy_allergy_rules, pharmacy_dose_guidelines
  - pharmacy_drug_monitoring, pharmacy_clinical_guidelines

Revision ID: 20260716_0003
Revises: 20260716_0002
Create Date: 2026-07-16
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import inspect

revision: str = "20260716_0003"
down_revision: Union[str, None] = "20260716_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def _index_exists(idx_name: str) -> bool:
    insp = inspect(op.get_bind())
    for table in insp.get_table_names():
        for idx in insp.get_indexes(table):
            if idx["name"] == idx_name:
                return True
    return False


def upgrade() -> None:
    # ── Drug Catalog (global reference) ───────────────────────────────────────
    if not _table_exists("pharmacy_drug_catalog"):
        op.create_table(
            "pharmacy_drug_catalog",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("drug_code", sa.String(50), nullable=False),
            sa.Column("drug_name", sa.String(300), nullable=False),
            sa.Column("drug_name_ar", sa.String(300), nullable=True),
            sa.Column("generic_name", sa.String(300), nullable=True),
            sa.Column("drug_class", sa.String(100), nullable=True),
            sa.Column("therapeutic_category", sa.String(100), nullable=True),
            sa.Column("atc_code", sa.String(20), nullable=True),
            sa.Column("dosage_form", sa.String(50), nullable=False),
            sa.Column("strength", sa.String(50), nullable=True),
            sa.Column("unit", sa.String(20), nullable=True),
            sa.Column("route_of_administration", sa.String(50), nullable=True),
            sa.Column("is_controlled_substance", sa.Boolean(), default=False),
            sa.Column("controlled_substance_schedule", sa.String(10), nullable=True),
            sa.Column("requires_prescription", sa.Boolean(), default=True),
            sa.Column("is_antibiotic", sa.Boolean(), default=False),
            sa.Column("is_refrigerated", sa.Boolean(), default=False),
            sa.Column("max_daily_dosage", sa.String(100), nullable=True),
            sa.Column("max_daily_dosage_mg", sa.Float(), nullable=True),
            sa.Column("package_description", sa.String(200), nullable=True),
            sa.Column("manufacturer", sa.String(200), nullable=True),
            sa.Column("country_of_origin", sa.String(100), nullable=True),
            sa.Column("is_active", sa.Boolean(), default=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("drug_code", name="uq_pharmacy_drug_code"),
        )
        op.create_index("ix_pharmacy_drug_catalog_drug_code", "pharmacy_drug_catalog", ["drug_code"])
        op.create_index("ix_pharmacy_drug_catalog_atc_code", "pharmacy_drug_catalog", ["atc_code"])
        op.create_index("ix_pharmacy_drug_catalog_generic_name", "pharmacy_drug_catalog", ["generic_name"])

    # ── Drug Suppliers ────────────────────────────────────────────────────────
    if not _table_exists("pharmacy_drug_suppliers"):
        op.create_table(
            "pharmacy_drug_suppliers",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("supplier_code", sa.String(50), nullable=False),
            sa.Column("supplier_name", sa.String(200), nullable=False),
            sa.Column("supplier_name_ar", sa.String(200), nullable=True),
            sa.Column("contact_person", sa.String(200), nullable=True),
            sa.Column("phone", sa.String(20), nullable=True),
            sa.Column("email", sa.String(100), nullable=True),
            sa.Column("address", sa.String(500), nullable=True),
            sa.Column("license_number", sa.String(100), nullable=True),
            sa.Column("contract_start", sa.Date(), nullable=True),
            sa.Column("contract_end", sa.Date(), nullable=True),
            sa.Column("payment_terms", sa.String(200), nullable=True),
            sa.Column("is_active", sa.Boolean(), default=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("lab_id", "supplier_code", name="uq_pharmacy_supplier_code"),
        )
        op.create_index("ix_pharmacy_drug_suppliers_lab_id", "pharmacy_drug_suppliers", ["lab_id"])

    # ── Drug Batches ──────────────────────────────────────────────────────────
    if not _table_exists("pharmacy_drug_batches"):
        op.create_table(
            "pharmacy_drug_batches",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("drug_id", sa.Integer(), sa.ForeignKey("pharmacy_drug_catalog.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("pharmacy_drug_suppliers.id", ondelete="SET NULL"), nullable=True),
            sa.Column("batch_number", sa.String(100), nullable=False),
            sa.Column("manufacturing_date", sa.Date(), nullable=True),
            sa.Column("expiry_date", sa.Date(), nullable=False),
            sa.Column("quantity_received", sa.Float(), nullable=False),
            sa.Column("quantity_remaining", sa.Float(), nullable=False),
            sa.Column("unit_cost", sa.Numeric(12, 4), nullable=True),
            sa.Column("selling_price", sa.Numeric(12, 4), nullable=True),
            sa.Column("storage_condition", sa.String(100), nullable=True),
            sa.Column("location", sa.String(100), nullable=True),
            sa.Column("received_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("received_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("is_quarantined", sa.Boolean(), default=False),
            sa.Column("quarantine_reason", sa.Text(), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="active"),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("lab_id", "batch_number", "drug_id", name="uq_pharmacy_batch"),
        )
        op.create_index("ix_pharmacy_drug_batches_lab_id", "pharmacy_drug_batches", ["lab_id"])
        op.create_index("ix_pharmacy_drug_batches_drug_id", "pharmacy_drug_batches", ["drug_id"])
        op.create_index("ix_pharmacy_drug_batches_expiry", "pharmacy_drug_batches", ["expiry_date"])
        op.create_index("ix_pharmacy_batch_expiry_active", "pharmacy_drug_batches", ["expiry_date", "status"])

    # ── Prescriptions ─────────────────────────────────────────────────────────
    if not _table_exists("pharmacy_prescriptions"):
        op.create_table(
            "pharmacy_prescriptions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="SET NULL"), nullable=True),
            sa.Column("prescription_number", sa.String(30), nullable=False),
            sa.Column("prescribed_by", sa.String(200), nullable=False),
            sa.Column("prescriber_license", sa.String(100), nullable=True),
            sa.Column("prescribed_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("prescription_type", sa.String(30), default="outpatient"),
            sa.Column("status", sa.String(20), nullable=False, server_default="active"),
            sa.Column("diagnosis_code", sa.String(20), nullable=True),
            sa.Column("diagnosis_description", sa.Text(), nullable=True),
            sa.Column("clinical_notes", sa.Text(), nullable=True),
            sa.Column("is_stat", sa.Boolean(), default=False),
            sa.Column("is_verbal", sa.Boolean(), default=False),
            sa.Column("is_emergency", sa.Boolean(), default=False),
            sa.Column("refills_allowed", sa.Integer(), default=0),
            sa.Column("refills_used", sa.Integer(), default=0),
            sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("lab_id", "prescription_number", name="uq_pharmacy_rx_number"),
        )
        op.create_index("ix_pharmacy_prescriptions_lab_id", "pharmacy_prescriptions", ["lab_id"])
        op.create_index("ix_pharmacy_prescriptions_patient_id", "pharmacy_prescriptions", ["patient_id"])
        op.create_index("ix_pharmacy_prescriptions_status", "pharmacy_prescriptions", ["lab_id", "status"])

    # ── Prescription Items ────────────────────────────────────────────────────
    if not _table_exists("pharmacy_prescription_items"):
        op.create_table(
            "pharmacy_prescription_items",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("prescription_id", sa.Integer(), sa.ForeignKey("pharmacy_prescriptions.id", ondelete="CASCADE"), nullable=False),
            sa.Column("drug_id", sa.Integer(), sa.ForeignKey("pharmacy_drug_catalog.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("batch_id", sa.Integer(), sa.ForeignKey("pharmacy_drug_batches.id", ondelete="SET NULL"), nullable=True),
            sa.Column("drug_name", sa.String(300), nullable=False),
            sa.Column("dosage", sa.String(100), nullable=False),
            sa.Column("frequency", sa.String(100), nullable=False),
            sa.Column("route", sa.String(50), nullable=True),
            sa.Column("duration", sa.String(100), nullable=True),
            sa.Column("quantity", sa.Float(), nullable=False),
            sa.Column("quantity_unit", sa.String(20), nullable=True),
            sa.Column("refill_quantity", sa.Float(), nullable=True),
            sa.Column("instructions", sa.Text(), nullable=True),
            sa.Column("patient_education", sa.Text(), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
            sa.Column("is_substitution_allowed", sa.Boolean(), default=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_pharmacy_rx_items_prescription_id", "pharmacy_prescription_items", ["prescription_id"])
        op.create_index("ix_pharmacy_rx_items_drug_id", "pharmacy_prescription_items", ["drug_id"])
        op.create_index("ix_pharmacy_rx_items_status", "pharmacy_prescription_items", ["prescription_id", "status"])

    # ── Dispense Records ──────────────────────────────────────────────────────
    if not _table_exists("pharmacy_dispense_records"):
        op.create_table(
            "pharmacy_dispense_records",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("prescription_id", sa.Integer(), sa.ForeignKey("pharmacy_prescriptions.id", ondelete="SET NULL"), nullable=True),
            sa.Column("prescription_item_id", sa.Integer(), sa.ForeignKey("pharmacy_prescription_items.id", ondelete="SET NULL"), nullable=True),
            sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="SET NULL"), nullable=True),
            sa.Column("drug_id", sa.Integer(), sa.ForeignKey("pharmacy_drug_catalog.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("batch_id", sa.Integer(), sa.ForeignKey("pharmacy_drug_batches.id", ondelete="SET NULL"), nullable=True),
            sa.Column("dispense_number", sa.String(30), nullable=False),
            sa.Column("dispensed_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=False),
            sa.Column("dispensed_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("quantity_dispensed", sa.Float(), nullable=False),
            sa.Column("quantity_unit", sa.String(20), nullable=True),
            sa.Column("days_supply", sa.Integer(), nullable=True),
            sa.Column("dosage_dispensed", sa.String(100), nullable=True),
            sa.Column("instructions", sa.Text(), nullable=True),
            sa.Column("label_notes", sa.Text(), nullable=True),
            sa.Column("is_verified", sa.Boolean(), default=False),
            sa.Column("verified_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_counselled", sa.Boolean(), default=False),
            sa.Column("counselled_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("counselled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("lab_id", "dispense_number", name="uq_pharmacy_dispense_number"),
        )
        op.create_index("ix_pharmacy_dispense_lab_id", "pharmacy_dispense_records", ["lab_id"])
        op.create_index("ix_pharmacy_dispense_prescription_id", "pharmacy_dispense_records", ["prescription_id"])
        op.create_index("ix_pharmacy_dispense_patient_id", "pharmacy_dispense_records", ["patient_id"])
        op.create_index("ix_pharmacy_dispense_drug_id", "pharmacy_dispense_records", ["drug_id"])
        op.create_index("ix_pharmacy_dispense_dispensed_at", "pharmacy_dispense_records", ["dispensed_at"])

    # ── Dispense Queue ────────────────────────────────────────────────────────
    if not _table_exists("pharmacy_dispense_queue"):
        op.create_table(
            "pharmacy_dispense_queue",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("prescription_id", sa.Integer(), sa.ForeignKey("pharmacy_prescriptions.id", ondelete="CASCADE"), nullable=False),
            sa.Column("prescription_item_id", sa.Integer(), sa.ForeignKey("pharmacy_prescription_items.id", ondelete="SET NULL"), nullable=True),
            sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="SET NULL"), nullable=True),
            sa.Column("queue_number", sa.String(20), nullable=False),
            sa.Column("priority", sa.Integer(), default=0),
            sa.Column("status", sa.String(20), nullable=False, server_default="waiting"),
            sa.Column("entered_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("assigned_to", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("estimated_wait_minutes", sa.Integer(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_pharmacy_dispense_queue_lab_id", "pharmacy_dispense_queue", ["lab_id"])
        op.create_index("ix_pharmacy_dispense_queue_status", "pharmacy_dispense_queue", ["lab_id", "status"])
        op.create_index("ix_pharmacy_dispense_queue_assigned", "pharmacy_dispense_queue", ["assigned_to"])

    # ── Warehouses ────────────────────────────────────────────────────────────
    if not _table_exists("pharmacy_warehouses"):
        op.create_table(
            "pharmacy_warehouses",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("warehouse_code", sa.String(30), nullable=False),
            sa.Column("warehouse_name", sa.String(200), nullable=False),
            sa.Column("warehouse_name_ar", sa.String(200), nullable=True),
            sa.Column("warehouse_type", sa.String(30), nullable=True),
            sa.Column("location", sa.String(300), nullable=True),
            sa.Column("capacity", sa.Float(), nullable=True),
            sa.Column("capacity_unit", sa.String(20), nullable=True),
            sa.Column("temperature_min", sa.Float(), nullable=True),
            sa.Column("temperature_max", sa.Float(), nullable=True),
            sa.Column("humidity_min", sa.Float(), nullable=True),
            sa.Column("humidity_max", sa.Float(), nullable=True),
            sa.Column("is_active", sa.Boolean(), default=True),
            sa.Column("is_refrigerated", sa.Boolean(), default=False),
            sa.Column("is_controlled_substance_storage", sa.Boolean(), default=False),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("lab_id", "warehouse_code", name="uq_pharmacy_warehouse_code"),
        )
        op.create_index("ix_pharmacy_warehouses_lab_id", "pharmacy_warehouses", ["lab_id"])

    # ── Stores ────────────────────────────────────────────────────────────────
    if not _table_exists("pharmacy_stores"):
        op.create_table(
            "pharmacy_stores",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("warehouse_id", sa.Integer(), sa.ForeignKey("pharmacy_warehouses.id", ondelete="CASCADE"), nullable=True),
            sa.Column("store_code", sa.String(30), nullable=False),
            sa.Column("store_name", sa.String(200), nullable=False),
            sa.Column("store_name_ar", sa.String(200), nullable=True),
            sa.Column("store_type", sa.String(30), nullable=True),
            sa.Column("location", sa.String(300), nullable=True),
            sa.Column("is_active", sa.Boolean(), default=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("lab_id", "store_code", name="uq_pharmacy_store_code"),
        )
        op.create_index("ix_pharmacy_stores_lab_id", "pharmacy_stores", ["lab_id"])
        op.create_index("ix_pharmacy_stores_warehouse_id", "pharmacy_stores", ["warehouse_id"])

    # ── Stock Levels ──────────────────────────────────────────────────────────
    if not _table_exists("pharmacy_stock_levels"):
        op.create_table(
            "pharmacy_stock_levels",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("drug_id", sa.Integer(), sa.ForeignKey("pharmacy_drug_catalog.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("batch_id", sa.Integer(), sa.ForeignKey("pharmacy_drug_batches.id", ondelete="SET NULL"), nullable=True),
            sa.Column("store_id", sa.Integer(), sa.ForeignKey("pharmacy_stores.id", ondelete="SET NULL"), nullable=True),
            sa.Column("warehouse_id", sa.Integer(), sa.ForeignKey("pharmacy_warehouses.id", ondelete="SET NULL"), nullable=True),
            sa.Column("quantity_on_hand", sa.Float(), nullable=False, default=0),
            sa.Column("quantity_reserved", sa.Float(), default=0),
            sa.Column("quantity_available", sa.Float(), nullable=False, default=0),
            sa.Column("quantity_on_order", sa.Float(), default=0),
            sa.Column("reorder_point", sa.Float(), nullable=True),
            sa.Column("reorder_quantity", sa.Float(), nullable=True),
            sa.Column("maximum_level", sa.Float(), nullable=True),
            sa.Column("unit", sa.String(20), nullable=False),
            sa.Column("location", sa.String(100), nullable=True),
            sa.Column("last_counted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_counted_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("lab_id", "drug_id", "batch_id", "store_id", name="uq_pharmacy_stock"),
        )
        op.create_index("ix_pharmacy_stock_levels_lab_id", "pharmacy_stock_levels", ["lab_id"])
        op.create_index("ix_pharmacy_stock_levels_drug_id", "pharmacy_stock_levels", ["drug_id"])
        op.create_index("ix_pharmacy_stock_levels_store_id", "pharmacy_stock_levels", ["store_id"])
        op.create_index("ix_pharmacy_stock_levels_low_stock", "pharmacy_stock_levels", ["lab_id", "quantity_available"])
        op.create_index("ix_pharmacy_stock_levels_batch_id", "pharmacy_stock_levels", ["batch_id"])

    # ── Stock Movements ───────────────────────────────────────────────────────
    if not _table_exists("pharmacy_stock_movements"):
        op.create_table(
            "pharmacy_stock_movements",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("drug_id", sa.Integer(), sa.ForeignKey("pharmacy_drug_catalog.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("batch_id", sa.Integer(), sa.ForeignKey("pharmacy_drug_batches.id", ondelete="SET NULL"), nullable=True),
            sa.Column("movement_type", sa.String(30), nullable=False),
            sa.Column("quantity", sa.Float(), nullable=False),
            sa.Column("unit", sa.String(20), nullable=False),
            sa.Column("from_location", sa.String(100), nullable=True),
            sa.Column("to_location", sa.String(100), nullable=True),
            sa.Column("reference_type", sa.String(50), nullable=True),
            sa.Column("reference_id", sa.Integer(), nullable=True),
            sa.Column("reason", sa.String(200), nullable=True),
            sa.Column("performed_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=False),
            sa.Column("performed_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_pharmacy_stock_movements_lab_id", "pharmacy_stock_movements", ["lab_id"])
        op.create_index("ix_pharmacy_stock_movements_drug_id", "pharmacy_stock_movements", ["drug_id"])
        op.create_index("ix_pharmacy_stock_movements_batch_id", "pharmacy_stock_movements", ["batch_id"])
        op.create_index("ix_pharmacy_stock_movements_performed_at", "pharmacy_stock_movements", ["performed_at"])

    # ── Inventory Transfers ───────────────────────────────────────────────────
    if not _table_exists("pharmacy_inventory_transfers"):
        op.create_table(
            "pharmacy_inventory_transfers",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("from_store_id", sa.Integer(), sa.ForeignKey("pharmacy_stores.id", ondelete="SET NULL"), nullable=True),
            sa.Column("to_store_id", sa.Integer(), sa.ForeignKey("pharmacy_stores.id", ondelete="SET NULL"), nullable=True),
            sa.Column("from_warehouse_id", sa.Integer(), sa.ForeignKey("pharmacy_warehouses.id", ondelete="SET NULL"), nullable=True),
            sa.Column("to_warehouse_id", sa.Integer(), sa.ForeignKey("pharmacy_warehouses.id", ondelete="SET NULL"), nullable=True),
            sa.Column("transfer_number", sa.String(30), nullable=False),
            sa.Column("transfer_type", sa.String(30), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
            sa.Column("requested_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("requested_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("approved_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("dispatched_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("received_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("cancelled_reason", sa.Text(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("lab_id", "transfer_number", name="uq_pharmacy_transfer_number"),
        )
        op.create_index("ix_pharmacy_inv_transfers_lab_id", "pharmacy_inventory_transfers", ["lab_id"])
        op.create_index("ix_pharmacy_inv_transfers_from_store", "pharmacy_inventory_transfers", ["from_store_id"])
        op.create_index("ix_pharmacy_inv_transfers_to_store", "pharmacy_inventory_transfers", ["to_store_id"])
        op.create_index("ix_pharmacy_inv_transfers_status", "pharmacy_inventory_transfers", ["lab_id", "status"])

    # ── Inventory Transfer Items ──────────────────────────────────────────────
    if not _table_exists("pharmacy_inventory_transfer_items"):
        op.create_table(
            "pharmacy_inventory_transfer_items",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("transfer_id", sa.Integer(), sa.ForeignKey("pharmacy_inventory_transfers.id", ondelete="CASCADE"), nullable=False),
            sa.Column("drug_id", sa.Integer(), sa.ForeignKey("pharmacy_drug_catalog.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("batch_id", sa.Integer(), sa.ForeignKey("pharmacy_drug_batches.id", ondelete="SET NULL"), nullable=True),
            sa.Column("quantity", sa.Float(), nullable=False),
            sa.Column("unit", sa.String(20), nullable=False),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_pharmacy_transfer_items_transfer_id", "pharmacy_inventory_transfer_items", ["transfer_id"])
        op.create_index("ix_pharmacy_transfer_items_drug_id", "pharmacy_inventory_transfer_items", ["drug_id"])

    # ── Drug Returns ──────────────────────────────────────────────────────────
    if not _table_exists("pharmacy_drug_returns"):
        op.create_table(
            "pharmacy_drug_returns",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("drug_id", sa.Integer(), sa.ForeignKey("pharmacy_drug_catalog.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("batch_id", sa.Integer(), sa.ForeignKey("pharmacy_drug_batches.id", ondelete="SET NULL"), nullable=True),
            sa.Column("return_type", sa.String(30), nullable=False),
            sa.Column("return_reason", sa.Text(), nullable=False),
            sa.Column("quantity", sa.Float(), nullable=False),
            sa.Column("unit", sa.String(20), nullable=False),
            sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="SET NULL"), nullable=True),
            sa.Column("returned_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("returned_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("approved_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("disposition", sa.String(30), nullable=True),
            sa.Column("disposition_notes", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_pharmacy_drug_returns_lab_id", "pharmacy_drug_returns", ["lab_id"])
        op.create_index("ix_pharmacy_drug_returns_drug_id", "pharmacy_drug_returns", ["drug_id"])
        op.create_index("ix_pharmacy_drug_returns_returned_at", "pharmacy_drug_returns", ["returned_at"])

    # ── Waste Records ─────────────────────────────────────────────────────────
    if not _table_exists("pharmacy_waste_records"):
        op.create_table(
            "pharmacy_waste_records",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("drug_id", sa.Integer(), sa.ForeignKey("pharmacy_drug_catalog.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("batch_id", sa.Integer(), sa.ForeignKey("pharmacy_drug_batches.id", ondelete="SET NULL"), nullable=True),
            sa.Column("waste_type", sa.String(30), nullable=False),
            sa.Column("waste_reason", sa.Text(), nullable=False),
            sa.Column("quantity", sa.Float(), nullable=False),
            sa.Column("unit", sa.String(20), nullable=False),
            sa.Column("witnessed_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("wasted_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=False),
            sa.Column("wasted_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("disposal_method", sa.String(100), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_pharmacy_waste_lab_id", "pharmacy_waste_records", ["lab_id"])
        op.create_index("ix_pharmacy_waste_drug_id", "pharmacy_waste_records", ["drug_id"])
        op.create_index("ix_pharmacy_waste_batch_id", "pharmacy_waste_records", ["batch_id"])
        op.create_index("ix_pharmacy_waste_wasted_at", "pharmacy_waste_records", ["wasted_at"])

    # ── Recalls ───────────────────────────────────────────────────────────────
    if not _table_exists("pharmacy_recalls"):
        op.create_table(
            "pharmacy_recalls",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("drug_id", sa.Integer(), sa.ForeignKey("pharmacy_drug_catalog.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("batch_id", sa.Integer(), sa.ForeignKey("pharmacy_drug_batches.id", ondelete="SET NULL"), nullable=True),
            sa.Column("recall_number", sa.String(50), nullable=False),
            sa.Column("recall_reason", sa.Text(), nullable=False),
            sa.Column("recall_source", sa.String(200), nullable=True),
            sa.Column("severity", sa.String(20), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="active"),
            sa.Column("initiated_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("initiated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("affected_quantity", sa.Float(), nullable=True),
            sa.Column("recovered_quantity", sa.Float(), nullable=True),
            sa.Column("patient_notification_required", sa.Boolean(), default=False),
            sa.Column("notified_patients_count", sa.Integer(), nullable=True),
            sa.Column("actions_taken", sa.Text(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_pharmacy_recalls_lab_id", "pharmacy_recalls", ["lab_id"])
        op.create_index("ix_pharmacy_recalls_drug_id", "pharmacy_recalls", ["drug_id"])
        op.create_index("ix_pharmacy_recalls_batch_id", "pharmacy_recalls", ["batch_id"])
        op.create_index("ix_pharmacy_recalls_lab_status", "pharmacy_recalls", ["lab_id", "status"])

    # ── Inventory Forecasts ───────────────────────────────────────────────────
    if not _table_exists("pharmacy_inventory_forecasts"):
        op.create_table(
            "pharmacy_inventory_forecasts",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("drug_id", sa.Integer(), sa.ForeignKey("pharmacy_drug_catalog.id", ondelete="CASCADE"), nullable=False),
            sa.Column("forecast_date", sa.Date(), nullable=False),
            sa.Column("forecast_period_start", sa.Date(), nullable=False),
            sa.Column("forecast_period_end", sa.Date(), nullable=False),
            sa.Column("predicted_consumption", sa.Float(), nullable=False),
            sa.Column("predicted_consumption_unit", sa.String(20), nullable=False),
            sa.Column("confidence_lower", sa.Float(), nullable=True),
            sa.Column("confidence_upper", sa.Float(), nullable=True),
            sa.Column("recommended_reorder_quantity", sa.Float(), nullable=True),
            sa.Column("current_stock", sa.Float(), nullable=True),
            sa.Column("days_until_stockout", sa.Integer(), nullable=True),
            sa.Column("seasonal_factor", sa.Float(), nullable=True),
            sa.Column("trend_factor", sa.Float(), nullable=True),
            sa.Column("model_used", sa.String(100), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_pharmacy_forecasts_lab_id", "pharmacy_inventory_forecasts", ["lab_id"])
        op.create_index("ix_pharmacy_forecasts_drug_id", "pharmacy_inventory_forecasts", ["drug_id"])
        op.create_index("ix_pharmacy_forecasts_period", "pharmacy_inventory_forecasts", ["lab_id", "drug_id", "forecast_period_start"])

    # ── Drug Interaction Rules ────────────────────────────────────────────────
    if not _table_exists("pharmacy_drug_interaction_rules"):
        op.create_table(
            "pharmacy_drug_interaction_rules",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("drug_id_a", sa.Integer(), sa.ForeignKey("pharmacy_drug_catalog.id", ondelete="CASCADE"), nullable=False),
            sa.Column("drug_id_b", sa.Integer(), sa.ForeignKey("pharmacy_drug_catalog.id", ondelete="CASCADE"), nullable=False),
            sa.Column("severity", sa.String(20), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("clinical_consequence", sa.Text(), nullable=True),
            sa.Column("recommendation", sa.Text(), nullable=True),
            sa.Column("evidence_level", sa.String(20), nullable=True),
            sa.Column("source", sa.String(200), nullable=True),
            sa.Column("is_active", sa.Boolean(), default=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("drug_id_a", "drug_id_b", name="uq_pharmacy_interaction_pair"),
        )
        op.create_index("ix_pharmacy_interaction_drug_a", "pharmacy_drug_interaction_rules", ["drug_id_a"])
        op.create_index("ix_pharmacy_interaction_drug_b", "pharmacy_drug_interaction_rules", ["drug_id_b"])
        op.create_index("ix_pharmacy_interaction_severity", "pharmacy_drug_interaction_rules", ["severity"])

    # ── Contraindication Rules ────────────────────────────────────────────────
    if not _table_exists("pharmacy_contraindication_rules"):
        op.create_table(
            "pharmacy_contraindication_rules",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("drug_id", sa.Integer(), sa.ForeignKey("pharmacy_drug_catalog.id", ondelete="CASCADE"), nullable=False),
            sa.Column("contraindication_type", sa.String(50), nullable=False),
            sa.Column("contraindication_value", sa.String(300), nullable=False),
            sa.Column("severity", sa.String(20), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("clinical_consequence", sa.Text(), nullable=True),
            sa.Column("recommendation", sa.Text(), nullable=True),
            sa.Column("evidence_level", sa.String(20), nullable=True),
            sa.Column("source", sa.String(200), nullable=True),
            sa.Column("is_active", sa.Boolean(), default=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_pharmacy_contraindication_drug_id", "pharmacy_contraindication_rules", ["drug_id"])
        op.create_index("ix_pharmacy_contraindication_type", "pharmacy_contraindication_rules", ["contraindication_type"])

    # ── Allergy Rules ─────────────────────────────────────────────────────────
    if not _table_exists("pharmacy_allergy_rules"):
        op.create_table(
            "pharmacy_allergy_rules",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("drug_id", sa.Integer(), sa.ForeignKey("pharmacy_drug_catalog.id", ondelete="CASCADE"), nullable=False),
            sa.Column("allergen", sa.String(200), nullable=False),
            sa.Column("allergen_code", sa.String(50), nullable=True),
            sa.Column("reaction_type", sa.String(100), nullable=True),
            sa.Column("severity", sa.String(20), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("recommendation", sa.Text(), nullable=True),
            sa.Column("evidence_level", sa.String(20), nullable=True),
            sa.Column("source", sa.String(200), nullable=True),
            sa.Column("is_active", sa.Boolean(), default=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_pharmacy_allergy_rules_drug_id", "pharmacy_allergy_rules", ["drug_id"])
        op.create_index("ix_pharmacy_allergy_rules_allergen", "pharmacy_allergy_rules", ["allergen"])

    # ── Dose Guidelines ───────────────────────────────────────────────────────
    if not _table_exists("pharmacy_dose_guidelines"):
        op.create_table(
            "pharmacy_dose_guidelines",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("drug_id", sa.Integer(), sa.ForeignKey("pharmacy_drug_catalog.id", ondelete="CASCADE"), nullable=False),
            sa.Column("route", sa.String(50), nullable=True),
            sa.Column("indication", sa.String(300), nullable=True),
            sa.Column("age_min_years", sa.Float(), nullable=True),
            sa.Column("age_max_years", sa.Float(), nullable=True),
            sa.Column("weight_min_kg", sa.Float(), nullable=True),
            sa.Column("weight_max_kg", sa.Float(), nullable=True),
            sa.Column("dose_min", sa.Float(), nullable=False),
            sa.Column("dose_max", sa.Float(), nullable=True),
            sa.Column("dose_unit", sa.String(30), nullable=False),
            sa.Column("frequency", sa.String(100), nullable=False),
            sa.Column("max_daily_dose", sa.Float(), nullable=True),
            sa.Column("duration", sa.String(100), nullable=True),
            sa.Column("renal_adjustment", sa.Text(), nullable=True),
            sa.Column("hepatic_adjustment", sa.Text(), nullable=True),
            sa.Column("pediatric_note", sa.Text(), nullable=True),
            sa.Column("geriatric_note", sa.Text(), nullable=True),
            sa.Column("pregnancy_category", sa.String(10), nullable=True),
            sa.Column("evidence_level", sa.String(20), nullable=True),
            sa.Column("source", sa.String(200), nullable=True),
            sa.Column("is_active", sa.Boolean(), default=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_pharmacy_dose_guidelines_drug_id", "pharmacy_dose_guidelines", ["drug_id"])
        op.create_index("ix_pharmacy_dose_guidelines_indication", "pharmacy_dose_guidelines", ["drug_id", "indication"])

    # ── Drug Monitoring ───────────────────────────────────────────────────────
    if not _table_exists("pharmacy_drug_monitoring"):
        op.create_table(
            "pharmacy_drug_monitoring",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
            sa.Column("drug_id", sa.Integer(), sa.ForeignKey("pharmacy_drug_catalog.id", ondelete="CASCADE"), nullable=False),
            sa.Column("prescription_id", sa.Integer(), sa.ForeignKey("pharmacy_prescriptions.id", ondelete="SET NULL"), nullable=True),
            sa.Column("monitoring_type", sa.String(50), nullable=False),
            sa.Column("monitoring_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("value", sa.String(200), nullable=True),
            sa.Column("value_numeric", sa.Float(), nullable=True),
            sa.Column("unit", sa.String(20), nullable=True),
            sa.Column("therapeutic_range_low", sa.Float(), nullable=True),
            sa.Column("therapeutic_range_high", sa.Float(), nullable=True),
            sa.Column("is_within_range", sa.Boolean(), nullable=True),
            sa.Column("adverse_reaction", sa.Text(), nullable=True),
            sa.Column("severity", sa.String(20), nullable=True),
            sa.Column("action_taken", sa.Text(), nullable=True),
            sa.Column("performed_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("next_monitoring_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_pharmacy_drug_monitoring_lab_id", "pharmacy_drug_monitoring", ["lab_id"])
        op.create_index("ix_pharmacy_drug_monitoring_patient_id", "pharmacy_drug_monitoring", ["patient_id"])
        op.create_index("ix_pharmacy_drug_monitoring_drug_id", "pharmacy_drug_monitoring", ["drug_id"])
        op.create_index("ix_pharmacy_drug_monitoring_patient_drug", "pharmacy_drug_monitoring", ["patient_id", "drug_id", "monitoring_date"])

    # ── Clinical Guidelines ──────────────────────────────────────────────────
    if not _table_exists("pharmacy_clinical_guidelines"):
        op.create_table(
            "pharmacy_clinical_guidelines",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("guideline_code", sa.String(50), nullable=False),
            sa.Column("title", sa.String(300), nullable=False),
            sa.Column("title_ar", sa.String(300), nullable=True),
            sa.Column("guideline_type", sa.String(50), nullable=False),
            sa.Column("condition", sa.String(200), nullable=True),
            sa.Column("icd_code", sa.String(20), nullable=True),
            sa.Column("summary", sa.Text(), nullable=True),
            sa.Column("content", sa.Text(), nullable=True),
            sa.Column("drug_recommendations", JSON(), nullable=True),
            sa.Column("algorithms", JSON(), nullable=True),
            sa.Column("version", sa.String(20), nullable=False),
            sa.Column("effective_from", sa.Date(), nullable=True),
            sa.Column("effective_until", sa.Date(), nullable=True),
            sa.Column("source", sa.String(200), nullable=True),
            sa.Column("is_active", sa.Boolean(), default=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("guideline_code", name="uq_pharmacy_guideline_code"),
        )
        op.create_index("ix_pharmacy_clinical_guidelines_code", "pharmacy_clinical_guidelines", ["guideline_code"])
        op.create_index("ix_pharmacy_clinical_guidelines_type", "pharmacy_clinical_guidelines", ["guideline_type"])


def downgrade() -> None:
    tables = [
        "pharmacy_clinical_guidelines",
        "pharmacy_drug_monitoring",
        "pharmacy_dose_guidelines",
        "pharmacy_allergy_rules",
        "pharmacy_contraindication_rules",
        "pharmacy_drug_interaction_rules",
        "pharmacy_inventory_forecasts",
        "pharmacy_recalls",
        "pharmacy_waste_records",
        "pharmacy_drug_returns",
        "pharmacy_inventory_transfer_items",
        "pharmacy_inventory_transfers",
        "pharmacy_stock_movements",
        "pharmacy_stock_levels",
        "pharmacy_stores",
        "pharmacy_warehouses",
        "pharmacy_dispense_queue",
        "pharmacy_dispense_records",
        "pharmacy_prescription_items",
        "pharmacy_prescriptions",
        "pharmacy_drug_suppliers",
        "pharmacy_drug_batches",
        "pharmacy_drug_catalog",
    ]
    for table in tables:
        if _table_exists(table):
            op.drop_table(table)
