"""Create National LIMS domain tables.

Creates all canonical LIMS entities:
  - lims_departments, lims_sections, lims_workstations
  - lims_manufacturers, lims_instrument_models, lims_instruments
  - lims_maintenance, lims_calibrations
  - lims_qc_programs, lims_iqc, lims_eqa
  - lims_lots, lims_reagents, lims_suppliers, lims_consumables
  - lims_storage, lims_temperature_logs, lims_equipment_logs
  - lims_specimen_catalog, lims_containers
  - lims_specimens, lims_transportation, lims_chain_of_custody
  - lims_orders, lims_panels, lims_panel_tests
  - lims_results, lims_reference_ranges
  - lims_auto_validation_rules, lims_delta_check_rules
  - lims_result_validations, lims_result_releases
  - lims_electronic_signatures
  - lims_reports, lims_report_attachments

Revision ID: 20260714_0001
Revises: 20260511_0002
Create Date: 2026-07-14
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import inspect

revision: str = "20260714_0001"
down_revision: Union[str, None] = "20260511_0002"
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
    # ── Departments ──────────────────────────────────────────────────────────
    if not _table_exists("lims_departments"):
        op.create_table(
            "lims_departments",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("code", sa.String(20), nullable=False),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("name_ar", sa.String(200), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), default=True),
            sa.Column("sort_order", sa.Integer(), default=0),
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
        op.create_index("ix_lims_departments_lab_id", "lims_departments", ["lab_id"])
        op.create_index("ix_lims_dept_lab_code", "lims_departments", ["lab_id", "code"], unique=True)
        op.create_index("ix_lims_dept_not_deleted", "lims_departments", ["is_deleted", "lab_id"])

    # ── Sections ─────────────────────────────────────────────────────────────
    if not _table_exists("lims_sections"):
        op.create_table(
            "lims_sections",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("department_id", sa.Integer(), sa.ForeignKey("lims_departments.id", ondelete="CASCADE"), nullable=False),
            sa.Column("code", sa.String(20), nullable=False),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("name_ar", sa.String(200), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
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
            sa.UniqueConstraint("department_id", "code", name="uq_lims_section_dept_code"),
        )
        op.create_index("ix_lims_sections_department_id", "lims_sections", ["department_id"])

    # ── Workstations ─────────────────────────────────────────────────────────
    if not _table_exists("lims_workstations"):
        op.create_table(
            "lims_workstations",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("section_id", sa.Integer(), sa.ForeignKey("lims_sections.id", ondelete="CASCADE"), nullable=False),
            sa.Column("code", sa.String(20), nullable=False),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("workstation_type", sa.String(50), nullable=True),
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
        )
        op.create_index("ix_lims_workstations_section_id", "lims_workstations", ["section_id"])

    # ── Manufacturers ────────────────────────────────────────────────────────
    if not _table_exists("lims_manufacturers"):
        op.create_table(
            "lims_manufacturers",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("code", sa.String(50), unique=True, nullable=False),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("name_ar", sa.String(200), nullable=True),
            sa.Column("website", sa.String(300), nullable=True),
            sa.Column("support_phone", sa.String(20), nullable=True),
            sa.Column("support_email", sa.String(100), nullable=True),
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
        op.create_index("ix_lims_manufacturers_code", "lims_manufacturers", ["code"])

    # ── Instrument Models ────────────────────────────────────────────────────
    if not _table_exists("lims_instrument_models"):
        op.create_table(
            "lims_instrument_models",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("manufacturer_id", sa.Integer(), sa.ForeignKey("lims_manufacturers.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("model_code", sa.String(50), nullable=False),
            sa.Column("model_name", sa.String(200), nullable=False),
            sa.Column("category", sa.String(50), nullable=True),
            sa.Column("interface_type", sa.String(50), nullable=True),
            sa.Column("supports_astm", sa.Boolean(), default=False),
            sa.Column("supports_hl7", sa.Boolean(), default=False),
            sa.Column("supports_fhir", sa.Boolean(), default=False),
            sa.Column("test_menu_capacity", sa.Integer(), nullable=True),
            sa.Column("throughput_per_hour", sa.Integer(), nullable=True),
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
            sa.UniqueConstraint("manufacturer_id", "model_code", name="uq_lims_model_mfr_code"),
        )
        op.create_index("ix_lims_instrument_models_model_code", "lims_instrument_models", ["model_code"])

    # ── Instruments ──────────────────────────────────────────────────────────
    if not _table_exists("lims_instruments"):
        op.create_table(
            "lims_instruments",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("model_id", sa.Integer(), sa.ForeignKey("lims_instrument_models.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("workstation_id", sa.Integer(), sa.ForeignKey("lims_workstations.id", ondelete="SET NULL"), nullable=True),
            sa.Column("instrument_code", sa.String(50), nullable=False),
            sa.Column("serial_number", sa.String(200), nullable=True),
            sa.Column("asset_number", sa.String(100), nullable=True),
            sa.Column("status", sa.String(20), default="online"),
            sa.Column("software_version", sa.String(50), nullable=True),
            sa.Column("installed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_connected_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("ip_address", sa.String(45), nullable=True),
            sa.Column("port", sa.Integer(), nullable=True),
            sa.Column("connection_params", JSON(), nullable=True),
            sa.Column("is_offline_capable", sa.Boolean(), default=False),
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
        op.create_index("ix_lims_instruments_lab_id", "lims_instruments", ["lab_id"])
        op.create_index("ix_lims_instruments_model_id", "lims_instruments", ["model_id"])
        op.create_index("ix_lims_inst_lab_status", "lims_instruments", ["lab_id", "status"])
        op.create_index("ix_lims_instruments_serial_number", "lims_instruments", ["serial_number"])

    # ── Maintenance ──────────────────────────────────────────────────────────
    if not _table_exists("lims_maintenance"):
        op.create_table(
            "lims_maintenance",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("instrument_id", sa.Integer(), sa.ForeignKey("lims_instruments.id", ondelete="CASCADE"), nullable=False),
            sa.Column("maintenance_type", sa.String(30), nullable=False),
            sa.Column("title", sa.String(200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("performed_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("performed_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("next_due_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("cost", sa.Numeric(12, 2), nullable=True),
            sa.Column("parts_replaced", sa.Text(), nullable=True),
            sa.Column("result", sa.String(20), default="completed"),
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
        op.create_index("ix_lims_maintenance_instrument_id", "lims_maintenance", ["instrument_id"])

    # ── Calibrations ─────────────────────────────────────────────────────────
    if not _table_exists("lims_calibrations"):
        op.create_table(
            "lims_calibrations",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("instrument_id", sa.Integer(), sa.ForeignKey("lims_instruments.id", ondelete="CASCADE"), nullable=False),
            sa.Column("calibration_type", sa.String(30), nullable=False),
            sa.Column("performed_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("performed_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("next_due_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("calibrator_lot", sa.String(100), nullable=True),
            sa.Column("calibrator_expiry", sa.Date(), nullable=True),
            sa.Column("results", JSON(), nullable=True),
            sa.Column("passed", sa.Boolean(), nullable=True),
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
        op.create_index("ix_lims_calibrations_instrument_id", "lims_calibrations", ["instrument_id"])

    # ── QC Programs ──────────────────────────────────────────────────────────
    if not _table_exists("lims_qc_programs"):
        op.create_table(
            "lims_qc_programs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("code", sa.String(50), nullable=False),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("program_type", sa.String(20), nullable=False),
            sa.Column("test_code", sa.String(50), nullable=False),
            sa.Column("instrument_id", sa.Integer(), sa.ForeignKey("lims_instruments.id", ondelete="SET NULL"), nullable=True),
            sa.Column("rule_set", sa.String(50), nullable=True),
            sa.Column("rules", JSON(), nullable=True),
            sa.Column("frequency", sa.String(20), nullable=True),
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
            sa.UniqueConstraint("lab_id", "code", name="uq_lims_qc_program_code"),
        )
        op.create_index("ix_lims_qc_programs_lab_id", "lims_qc_programs", ["lab_id"])
        op.create_index("ix_lims_qc_programs_test_code", "lims_qc_programs", ["test_code"])

    # ── IQC ──────────────────────────────────────────────────────────────────
    if not _table_exists("lims_iqc"):
        op.create_table(
            "lims_iqc",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("program_id", sa.Integer(), sa.ForeignKey("lims_qc_programs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("instrument_id", sa.Integer(), sa.ForeignKey("lims_instruments.id", ondelete="SET NULL"), nullable=True),
            sa.Column("test_code", sa.String(50), nullable=False),
            sa.Column("lot_number", sa.String(100), nullable=True),
            sa.Column("level", sa.String(20), nullable=False),
            sa.Column("measured_value", sa.Float(), nullable=False),
            sa.Column("expected_value", sa.Float(), nullable=True),
            sa.Column("sd", sa.Float(), nullable=True),
            sa.Column("mean", sa.Float(), nullable=True),
            sa.Column("unit", sa.String(20), nullable=True),
            sa.Column("status", sa.String(20), default="in_control"),
            sa.Column("violation", sa.String(20), nullable=True),
            sa.Column("performed_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
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
        op.create_index("ix_lims_iqc_lab_id", "lims_iqc", ["lab_id"])
        op.create_index("ix_lims_iqc_program_id", "lims_iqc", ["program_id"])
        op.create_index("ix_lims_iqc_lab_test_date", "lims_iqc", ["lab_id", "test_code", "performed_at"])

    # ── EQA ──────────────────────────────────────────────────────────────────
    if not _table_exists("lims_eqa"):
        op.create_table(
            "lims_eqa",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("program_id", sa.Integer(), sa.ForeignKey("lims_qc_programs.id", ondelete="SET NULL"), nullable=True),
            sa.Column("test_code", sa.String(50), nullable=False),
            sa.Column("scheme_name", sa.String(200), nullable=False),
            sa.Column("round_number", sa.String(50), nullable=False),
            sa.Column("sample_id", sa.String(100), nullable=True),
            sa.Column("submitted_value", sa.Float(), nullable=True),
            sa.Column("target_value", sa.Float(), nullable=True),
            sa.Column("acceptable_range", sa.String(100), nullable=True),
            sa.Column("z_score", sa.Float(), nullable=True),
            sa.Column("deviation_percent", sa.Float(), nullable=True),
            sa.Column("result", sa.String(20), nullable=True),
            sa.Column("submitted_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("corrective_action", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("lab_id", "scheme_name", "round_number", "test_code", name="uq_lims_eqa_round"),
        )
        op.create_index("ix_lims_eqa_lab_id", "lims_eqa", ["lab_id"])
        op.create_index("ix_lims_eqa_test_code", "lims_eqa", ["test_code"])

    # ── Lots ─────────────────────────────────────────────────────────────────
    if not _table_exists("lims_lots"):
        op.create_table(
            "lims_lots",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("lot_number", sa.String(100), nullable=False),
            sa.Column("item_type", sa.String(30), nullable=False),
            sa.Column("item_code", sa.String(50), nullable=True),
            sa.Column("item_name", sa.String(200), nullable=False),
            sa.Column("manufacturer_id", sa.Integer(), sa.ForeignKey("lims_manufacturers.id", ondelete="SET NULL"), nullable=True),
            sa.Column("quantity", sa.Float(), nullable=True),
            sa.Column("unit", sa.String(20), nullable=True),
            sa.Column("received_at", sa.Date(), nullable=True),
            sa.Column("expiry_at", sa.Date(), nullable=True),
            sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("opened_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("storage_condition", sa.String(200), nullable=True),
            sa.Column("certificate", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), default=True),
            sa.Column("is_consumed", sa.Boolean(), default=False),
            sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("lab_id", "lot_number", "item_type", name="uq_lims_lot"),
        )
        op.create_index("ix_lims_lots_lab_id", "lims_lots", ["lab_id"])
        op.create_index("ix_lims_lots_expiry_at", "lims_lots", ["expiry_at"])
        op.create_index("ix_lims_lot_expiry_active", "lims_lots", ["expiry_at", "is_active"])

    # ── Suppliers ────────────────────────────────────────────────────────────
    if not _table_exists("lims_suppliers"):
        op.create_table(
            "lims_suppliers",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("code", sa.String(50), nullable=False),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("name_ar", sa.String(200), nullable=True),
            sa.Column("contact_person", sa.String(200), nullable=True),
            sa.Column("phone", sa.String(20), nullable=True),
            sa.Column("email", sa.String(100), nullable=True),
            sa.Column("address", sa.String(500), nullable=True),
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
            sa.UniqueConstraint("lab_id", "code", name="uq_lims_supplier_lab_code"),
        )
        op.create_index("ix_lims_suppliers_lab_id", "lims_suppliers", ["lab_id"])

    # ── Reagents ─────────────────────────────────────────────────────────────
    if not _table_exists("lims_reagents"):
        op.create_table(
            "lims_reagents",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("reagent_code", sa.String(50), nullable=False),
            sa.Column("reagent_name", sa.String(200), nullable=False),
            sa.Column("reagent_name_ar", sa.String(200), nullable=True),
            sa.Column("lot_id", sa.Integer(), sa.ForeignKey("lims_lots.id", ondelete="SET NULL"), nullable=True),
            sa.Column("manufacturer_id", sa.Integer(), sa.ForeignKey("lims_manufacturers.id", ondelete="SET NULL"), nullable=True),
            sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("lims_suppliers.id", ondelete="SET NULL"), nullable=True),
            sa.Column("category", sa.String(50), nullable=True),
            sa.Column("current_quantity", sa.Float(), nullable=False, default=0),
            sa.Column("unit", sa.String(20), nullable=False),
            sa.Column("minimum_quantity", sa.Float(), nullable=True),
            sa.Column("maximum_quantity", sa.Float(), nullable=True),
            sa.Column("storage_location", sa.String(100), nullable=True),
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
            sa.UniqueConstraint("lab_id", "reagent_code", name="uq_lims_reagent_code"),
        )
        op.create_index("ix_lims_reagents_lab_id", "lims_reagents", ["lab_id"])
        op.create_index("ix_lims_reagents_reagent_code", "lims_reagents", ["reagent_code"])
        op.create_index("ix_lims_reagent_stock", "lims_reagents", ["lab_id", "current_quantity"])

    # ── Consumables ──────────────────────────────────────────────────────────
    if not _table_exists("lims_consumables"):
        op.create_table(
            "lims_consumables",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("code", sa.String(50), nullable=False),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("name_ar", sa.String(200), nullable=True),
            sa.Column("lot_id", sa.Integer(), sa.ForeignKey("lims_lots.id", ondelete="SET NULL"), nullable=True),
            sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("lims_suppliers.id", ondelete="SET NULL"), nullable=True),
            sa.Column("category", sa.String(50), nullable=True),
            sa.Column("current_quantity", sa.Integer(), nullable=False, default=0),
            sa.Column("unit", sa.String(20), nullable=False),
            sa.Column("minimum_quantity", sa.Integer(), nullable=True),
            sa.Column("storage_location", sa.String(100), nullable=True),
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
            sa.UniqueConstraint("lab_id", "code", name="uq_lims_consumable_code"),
        )
        op.create_index("ix_lims_consumables_lab_id", "lims_consumables", ["lab_id"])

    # ── Storage ──────────────────────────────────────────────────────────────
    if not _table_exists("lims_storage"):
        op.create_table(
            "lims_storage",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("code", sa.String(50), nullable=False),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("name_ar", sa.String(200), nullable=True),
            sa.Column("storage_type", sa.String(30), nullable=True),
            sa.Column("temperature_min", sa.Float(), nullable=True),
            sa.Column("temperature_max", sa.Float(), nullable=True),
            sa.Column("location", sa.String(200), nullable=True),
            sa.Column("capacity", sa.Integer(), nullable=True),
            sa.Column("is_active", sa.Boolean(), default=True),
            sa.Column("parent_id", sa.Integer(), sa.ForeignKey("lims_storage.id", ondelete="SET NULL"), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("lab_id", "code", name="uq_lims_storage_lab_code"),
        )
        op.create_index("ix_lims_storage_lab_id", "lims_storage", ["lab_id"])

    # ── Temperature Logs ─────────────────────────────────────────────────────
    if not _table_exists("lims_temperature_logs"):
        op.create_table(
            "lims_temperature_logs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("storage_id", sa.Integer(), sa.ForeignKey("lims_storage.id", ondelete="CASCADE"), nullable=False),
            sa.Column("temperature", sa.Float(), nullable=False),
            sa.Column("unit", sa.String(10), default="celsius"),
            sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("recorded_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("is_breach", sa.Boolean(), default=False),
            sa.Column("breach_notes", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_lims_temp_storage_time", "lims_temperature_logs", ["storage_id", "recorded_at"])

    # ── Equipment Logs ───────────────────────────────────────────────────────
    if not _table_exists("lims_equipment_logs"):
        op.create_table(
            "lims_equipment_logs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("instrument_id", sa.Integer(), sa.ForeignKey("lims_instruments.id", ondelete="CASCADE"), nullable=False),
            sa.Column("event_type", sa.String(30), nullable=False),
            sa.Column("description", sa.String(500), nullable=True),
            sa.Column("logged_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("logged_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("metadata_json", JSON(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_lims_eqlog_inst_time", "lims_equipment_logs", ["instrument_id", "logged_at"])

    # ── Specimen Catalog ─────────────────────────────────────────────────────
    if not _table_exists("lims_specimen_catalog"):
        op.create_table(
            "lims_specimen_catalog",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("code", sa.String(30), unique=True, nullable=False),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("name_ar", sa.String(200), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("default_container_type", sa.String(30), nullable=True),
            sa.Column("default_volume_ml", sa.Float(), nullable=True),
            sa.Column("storage_condition", sa.String(100), nullable=True),
            sa.Column("stability_hours", sa.Integer(), nullable=True),
            sa.Column("is_active", sa.Boolean(), default=True),
            sa.Column("loinc_code", sa.String(20), nullable=True),
            sa.Column("snomed_code", sa.String(20), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    # ── Containers ───────────────────────────────────────────────────────────
    if not _table_exists("lims_containers"):
        op.create_table(
            "lims_containers",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("code", sa.String(30), unique=True, nullable=False),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("name_ar", sa.String(200), nullable=True),
            sa.Column("container_type", sa.String(30), nullable=False),
            sa.Column("volume_ml", sa.Float(), nullable=True),
            sa.Column("additive", sa.String(100), nullable=True),
            sa.Column("color_code", sa.String(20), nullable=True),
            sa.Column("is_active", sa.Boolean(), default=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    # ── Specimens ────────────────────────────────────────────────────────────
    if not _table_exists("lims_specimens"):
        op.create_table(
            "lims_specimens",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("order_id", sa.Integer(), sa.ForeignKey("lab_orders.id", ondelete="CASCADE"), nullable=False),
            sa.Column("parent_specimen_id", sa.Integer(), sa.ForeignKey("lims_specimens.id", ondelete="SET NULL"), nullable=True),
            sa.Column("barcode", sa.String(30), unique=True, nullable=False),
            sa.Column("qr_code", sa.Text(), nullable=True),
            sa.Column("specimen_type", sa.String(30), nullable=False),
            sa.Column("container_type", sa.String(30), nullable=True),
            sa.Column("volume_ml", sa.Float(), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, default="ordered"),
            sa.Column("collection_time", sa.DateTime(timezone=True), nullable=True),
            sa.Column("collected_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("collection_site", sa.String(200), nullable=True),
            sa.Column("collection_notes", sa.Text(), nullable=True),
            sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("received_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("accepted_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("rejection_reason", sa.String(500), nullable=True),
            sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("rejected_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("storage_id", sa.Integer(), sa.ForeignKey("lims_storage.id", ondelete="SET NULL"), nullable=True),
            sa.Column("storage_position", sa.String(50), nullable=True),
            sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("verified_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("validated_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("released_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("disposed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("disposal_method", sa.String(100), nullable=True),
            sa.Column("clinical_info", sa.Text(), nullable=True),
            sa.Column("is_control", sa.Boolean(), default=False),
            sa.Column("control_specimen_id", sa.Integer(), sa.ForeignKey("lims_specimens.id", ondelete="SET NULL"), nullable=True),
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
        op.create_index("ix_lims_specimens_lab_id", "lims_specimens", ["lab_id"])
        op.create_index("ix_lims_specimens_order_id", "lims_specimens", ["order_id"])
        op.create_index("ix_lims_spec_lab_status", "lims_specimens", ["lab_id", "status"])
        op.create_index("ix_lims_spec_order", "lims_specimens", ["order_id", "status"])
        op.create_index("ix_lims_specimens_barcode", "lims_specimens", ["barcode"])

    # ── Transportation ───────────────────────────────────────────────────────
    if not _table_exists("lims_transportation"):
        op.create_table(
            "lims_transportation",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("specimen_id", sa.Integer(), sa.ForeignKey("lims_specimens.id", ondelete="CASCADE"), nullable=False),
            sa.Column("from_location", sa.String(200), nullable=False),
            sa.Column("to_location", sa.String(200), nullable=False),
            sa.Column("condition", sa.String(30), default="ambient"),
            sa.Column("courier_name", sa.String(200), nullable=True),
            sa.Column("courier_phone", sa.String(20), nullable=True),
            sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("temperature_min", sa.Float(), nullable=True),
            sa.Column("temperature_max", sa.Float(), nullable=True),
            sa.Column("chain_closed", sa.Boolean(), default=False),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_lims_transportation_specimen_id", "lims_transportation", ["specimen_id"])

    # ── Chain of Custody ─────────────────────────────────────────────────────
    if not _table_exists("lims_chain_of_custody"):
        op.create_table(
            "lims_chain_of_custody",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("specimen_id", sa.Integer(), sa.ForeignKey("lims_specimens.id", ondelete="CASCADE"), nullable=False),
            sa.Column("event_type", sa.String(30), nullable=False),
            sa.Column("from_person", sa.String(200), nullable=True),
            sa.Column("to_person", sa.String(200), nullable=True),
            sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
            sa.Column("reason", sa.String(500), nullable=True),
            sa.Column("signature", sa.Text(), nullable=True),
            sa.Column("previous_hash", sa.String(64), nullable=True),
            sa.Column("current_hash", sa.String(64), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_lims_coc_specimen", "lims_chain_of_custody", ["specimen_id", "timestamp"])

    # ── Orders (LIMS extension) ──────────────────────────────────────────────
    if not _table_exists("lims_orders"):
        op.create_table(
            "lims_orders",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("order_id", sa.Integer(), sa.ForeignKey("lab_orders.id", ondelete="CASCADE"), unique=True, nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("accession_number", sa.String(30), unique=True, nullable=False),
            sa.Column("priority", sa.String(20), default="routine"),
            sa.Column("order_status", sa.String(20), default="pending"),
            sa.Column("ordered_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("ordered_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("requested_completion", sa.DateTime(timezone=True), nullable=True),
            sa.Column("clinical_note", sa.Text(), nullable=True),
            sa.Column("diagnosis_code", sa.String(20), nullable=True),
            sa.Column("icd_code", sa.String(20), nullable=True),
            sa.Column("is_referral", sa.Boolean(), default=False),
            sa.Column("referring_lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="SET NULL"), nullable=True),
            sa.Column("referring_physician", sa.String(200), nullable=True),
            sa.Column("is_printed", sa.Boolean(), default=False),
            sa.Column("is_corrected", sa.Boolean(), default=False),
            sa.Column("correction_reason", sa.Text(), nullable=True),
            sa.Column("original_order_id", sa.Integer(), sa.ForeignKey("lims_orders.id", ondelete="SET NULL"), nullable=True),
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
        op.create_index("ix_lims_orders_order_id", "lims_orders", ["order_id"])
        op.create_index("ix_lims_orders_lab_id", "lims_orders", ["lab_id"])
        op.create_index("ix_lims_orders_accession_number", "lims_orders", ["accession_number"])
        op.create_index("ix_lims_order_lab_status", "lims_orders", ["lab_id", "order_status"])

    # ── Panels ───────────────────────────────────────────────────────────────
    if not _table_exists("lims_panels"):
        op.create_table(
            "lims_panels",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("code", sa.String(50), nullable=False),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("name_ar", sa.String(200), nullable=True),
            sa.Column("category", sa.String(50), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("tat_target_minutes", sa.Integer(), nullable=True),
            sa.Column("is_active", sa.Boolean(), default=True),
            sa.Column("is_national_essential", sa.Boolean(), default=False),
            sa.Column("department_id", sa.Integer(), sa.ForeignKey("lims_departments.id", ondelete="SET NULL"), nullable=True),
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
            sa.UniqueConstraint("lab_id", "code", name="uq_lims_panel_lab_code"),
        )
        op.create_index("ix_lims_panels_lab_id", "lims_panels", ["lab_id"])
        op.create_index("ix_lims_panels_code", "lims_panels", ["code"])

    # ── Panel Tests ──────────────────────────────────────────────────────────
    if not _table_exists("lims_panel_tests"):
        op.create_table(
            "lims_panel_tests",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("panel_id", sa.Integer(), sa.ForeignKey("lims_panels.id", ondelete="CASCADE"), nullable=False),
            sa.Column("test_code", sa.String(50), nullable=False),
            sa.Column("display_order", sa.Integer(), default=0),
            sa.Column("is_required", sa.Boolean(), default=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("panel_id", "test_code", name="uq_lims_panel_test"),
        )
        op.create_index("ix_lims_panel_tests_panel_id", "lims_panel_tests", ["panel_id"])
        op.create_index("ix_lims_panel_tests_test_code", "lims_panel_tests", ["test_code"])

    # ── Results ──────────────────────────────────────────────────────────────
    if not _table_exists("lims_results"):
        op.create_table(
            "lims_results",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("specimen_id", sa.Integer(), sa.ForeignKey("lims_specimens.id", ondelete="CASCADE"), nullable=False),
            sa.Column("order_id", sa.Integer(), sa.ForeignKey("lab_orders.id", ondelete="CASCADE"), nullable=False),
            sa.Column("test_code", sa.String(50), nullable=False),
            sa.Column("test_name", sa.String(200), nullable=False),
            sa.Column("test_name_ar", sa.String(200), nullable=True),
            sa.Column("category", sa.String(50), nullable=True),
            sa.Column("value_numeric", sa.Float(), nullable=True),
            sa.Column("value_text", sa.Text(), nullable=True),
            sa.Column("value_coded", sa.String(50), nullable=True),
            sa.Column("unit", sa.String(20), nullable=True),
            sa.Column("ref_range_low", sa.Float(), nullable=True),
            sa.Column("ref_range_high", sa.Float(), nullable=True),
            sa.Column("ref_range_text", sa.String(500), nullable=True),
            sa.Column("critical_low", sa.Float(), nullable=True),
            sa.Column("critical_high", sa.Float(), nullable=True),
            sa.Column("flag", sa.String(20), nullable=True),
            sa.Column("is_critical", sa.Boolean(), default=False),
            sa.Column("is_abnormal", sa.Boolean(), default=False),
            sa.Column("is_panic", sa.Boolean(), default=False),
            sa.Column("instrument_id", sa.Integer(), sa.ForeignKey("lims_instruments.id", ondelete="SET NULL"), nullable=True),
            sa.Column("instrument_result_id", sa.String(100), nullable=True),
            sa.Column("qc_status", sa.String(20), nullable=True),
            sa.Column("delta_check_status", sa.String(20), nullable=True),
            sa.Column("delta_percent", sa.Float(), nullable=True),
            sa.Column("validation_status", sa.String(20), default="pending"),
            sa.Column("auto_validated", sa.Boolean(), default=False),
            sa.Column("auto_validated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("validated_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("validation_note", sa.Text(), nullable=True),
            sa.Column("loinc_code", sa.String(20), nullable=True),
            sa.Column("snomed_code", sa.String(20), nullable=True),
            sa.Column("performed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("performed_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("result_status", sa.String(20), default="final"),
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
        op.create_index("ix_lims_results_lab_id", "lims_results", ["lab_id"])
        op.create_index("ix_lims_results_specimen_id", "lims_results", ["specimen_id"])
        op.create_index("ix_lims_result_lab_test", "lims_results", ["lab_id", "test_code"])
        op.create_index("ix_lims_result_validation", "lims_results", ["lab_id", "validation_status"])
        op.create_index("ix_lims_result_specimen", "lims_results", ["specimen_id", "test_code"], unique=True)
        op.create_index("ix_lims_results_loinc_code", "lims_results", ["loinc_code"])

    # ── Reference Ranges ─────────────────────────────────────────────────────
    if not _table_exists("lims_reference_ranges"):
        op.create_table(
            "lims_reference_ranges",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("test_code", sa.String(50), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=True),
            sa.Column("instrument_id", sa.Integer(), sa.ForeignKey("lims_instruments.id", ondelete="SET NULL"), nullable=True),
            sa.Column("method", sa.String(100), nullable=True),
            sa.Column("gender", sa.String(1), nullable=True),
            sa.Column("age_min_years", sa.Float(), nullable=True),
            sa.Column("age_max_years", sa.Float(), nullable=True),
            sa.Column("age_min_days", sa.Integer(), nullable=True),
            sa.Column("age_max_days", sa.Integer(), nullable=True),
            sa.Column("ref_range_low", sa.Float(), nullable=True),
            sa.Column("ref_range_high", sa.Float(), nullable=True),
            sa.Column("ref_range_text", sa.String(500), nullable=True),
            sa.Column("critical_low", sa.Float(), nullable=True),
            sa.Column("critical_high", sa.Float(), nullable=True),
            sa.Column("panic_low", sa.Float(), nullable=True),
            sa.Column("panic_high", sa.Float(), nullable=True),
            sa.Column("unit", sa.String(20), nullable=True),
            sa.Column("source", sa.String(200), nullable=True),
            sa.Column("is_active", sa.Boolean(), default=True),
            sa.Column("effective_from", sa.Date(), nullable=True),
            sa.Column("effective_until", sa.Date(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_lims_refrange_lookup", "lims_reference_ranges", ["test_code", "lab_id", "gender"])
        op.create_index("ix_lims_reference_ranges_test_code", "lims_reference_ranges", ["test_code"])

    # ── Auto-Validation Rules ───────────────────────────────────────────────
    if not _table_exists("lims_auto_validation_rules"):
        op.create_table(
            "lims_auto_validation_rules",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("rule_name", sa.String(200), nullable=False),
            sa.Column("test_code", sa.String(50), nullable=False),
            sa.Column("rule_type", sa.String(30), nullable=False),
            sa.Column("conditions", JSON(), nullable=False),
            sa.Column("action", sa.String(20), default="validate"),
            sa.Column("priority", sa.Integer(), default=0),
            sa.Column("is_active", sa.Boolean(), default=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_lims_autovalid_lab_id", "lims_auto_validation_rules", ["lab_id"])
        op.create_index("ix_lims_autovalid_test", "lims_auto_validation_rules", ["test_code", "lab_id"])

    # ── Delta Check Rules ───────────────────────────────────────────────────
    if not _table_exists("lims_delta_check_rules"):
        op.create_table(
            "lims_delta_check_rules",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("test_code", sa.String(50), nullable=False),
            sa.Column("test_name", sa.String(200), nullable=False),
            sa.Column("delta_percent", sa.Float(), nullable=False),
            sa.Column("delta_absolute", sa.Float(), nullable=True),
            sa.Column("window_days", sa.Integer(), default=30),
            sa.Column("applies_to", sa.String(20), default="all"),
            sa.Column("action", sa.String(20), default="flag"),
            sa.Column("is_active", sa.Boolean(), default=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("lab_id", "test_code", name="uq_lims_delta_check"),
        )
        op.create_index("ix_lims_delta_check_rules_lab_id", "lims_delta_check_rules", ["lab_id"])

    # ── Result Validations ──────────────────────────────────────────────────
    if not _table_exists("lims_result_validations"):
        op.create_table(
            "lims_result_validations",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("result_id", sa.Integer(), sa.ForeignKey("lims_results.id", ondelete="CASCADE"), nullable=False),
            sa.Column("action", sa.String(30), nullable=False),
            sa.Column("validated_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=False),
            sa.Column("validated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("is_electronic_signature", sa.Boolean(), default=False),
            sa.Column("signature_data", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_lims_result_validations_result_id", "lims_result_validations", ["result_id"])

    # ── Result Releases ──────────────────────────────────────────────────────
    if not _table_exists("lims_result_releases"):
        op.create_table(
            "lims_result_releases",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("order_id", sa.Integer(), sa.ForeignKey("lab_orders.id", ondelete="CASCADE"), nullable=False),
            sa.Column("released_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=False),
            sa.Column("released_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("release_channel", sa.String(20), nullable=True),
            sa.Column("is_patient_notified", sa.Boolean(), default=False),
            sa.Column("notified_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_lims_release_order", "lims_result_releases", ["order_id"])

    # ── Electronic Signatures ────────────────────────────────────────────────
    if not _table_exists("lims_electronic_signatures"):
        op.create_table(
            "lims_electronic_signatures",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("signature_type", sa.String(30), nullable=False),
            sa.Column("resource_type", sa.String(30), nullable=False),
            sa.Column("resource_id", sa.Integer(), nullable=False),
            sa.Column("signature_hash", sa.String(128), nullable=False),
            sa.Column("signed_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_revoked", sa.Boolean(), default=False),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_lims_esignature_user", "lims_electronic_signatures", ["user_id"])
        op.create_index("ix_lims_esignature_resource", "lims_electronic_signatures", ["resource_type", "resource_id"])

    # ── Reports ──────────────────────────────────────────────────────────────
    if not _table_exists("lims_reports"):
        op.create_table(
            "lims_reports",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("order_id", sa.Integer(), sa.ForeignKey("lab_orders.id", ondelete="CASCADE"), nullable=False),
            sa.Column("report_number", sa.String(30), unique=True, nullable=False),
            sa.Column("status", sa.String(20), default="draft"),
            sa.Column("title", sa.String(300), nullable=True),
            sa.Column("title_ar", sa.String(300), nullable=True),
            sa.Column("report_format", sa.String(20), default="pdf"),
            sa.Column("generated_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("finalized_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("corrected_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("corrected_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("correction_reason", sa.Text(), nullable=True),
            sa.Column("is_electronic", sa.Boolean(), default=True),
            sa.Column("is_printed", sa.Boolean(), default=False),
            sa.Column("printed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("printed_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("watermark", sa.String(200), nullable=True),
            sa.Column("locale", sa.String(10), default="ar"),
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
        op.create_index("ix_lims_reports_lab_id", "lims_reports", ["lab_id"])
        op.create_index("ix_lims_report_lab_status", "lims_reports", ["lab_id", "status"])
        op.create_index("ix_lims_reports_order_id", "lims_reports", ["order_id"])

    # ── Report Attachments ──────────────────────────────────────────────────
    if not _table_exists("lims_report_attachments"):
        op.create_table(
            "lims_report_attachments",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("report_id", sa.Integer(), sa.ForeignKey("lims_reports.id", ondelete="CASCADE"), nullable=False),
            sa.Column("file_name", sa.String(300), nullable=False),
            sa.Column("file_type", sa.String(100), nullable=True),
            sa.Column("file_size_bytes", sa.Integer(), nullable=True),
            sa.Column("storage_path", sa.String(500), nullable=True),
            sa.Column("is_watermarked", sa.Boolean(), default=False),
            sa.Column("uploaded_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_lims_report_attachments_report_id", "lims_report_attachments", ["report_id"])


def downgrade() -> None:
    """Drop all LIMS tables in reverse dependency order."""
    tables = [
        "lims_report_attachments",
        "lims_reports",
        "lims_electronic_signatures",
        "lims_result_releases",
        "lims_result_validations",
        "lims_delta_check_rules",
        "lims_auto_validation_rules",
        "lims_reference_ranges",
        "lims_results",
        "lims_panel_tests",
        "lims_panels",
        "lims_orders",
        "lims_chain_of_custody",
        "lims_transportation",
        "lims_specimens",
        "lims_containers",
        "lims_specimen_catalog",
        "lims_equipment_logs",
        "lims_temperature_logs",
        "lims_storage",
        "lims_consumables",
        "lims_reagents",
        "lims_suppliers",
        "lims_lots",
        "lims_eqa",
        "lims_iqc",
        "lims_qc_programs",
        "lims_calibrations",
        "lims_maintenance",
        "lims_instruments",
        "lims_instrument_models",
        "lims_manufacturers",
        "lims_workstations",
        "lims_sections",
        "lims_departments",
    ]
    for table in tables:
        if _table_exists(table):
            op.drop_table(table)
