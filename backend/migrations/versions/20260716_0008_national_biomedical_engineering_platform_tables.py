"""Create National Biomedical Engineering Platform tables.

Revision ID: 20260716_0008
Revises: 20260716_0007
Create Date: 2026-07-16
"""

from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy import inspect

revision: str = "20260716_0008"
down_revision: Union[str, None] = "20260716_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def upgrade() -> None:
    if not _table_exists("biomed_devices"):
        op.create_table(
            "biomed_devices",
            sa.Column("device_name", sa.String(), nullable=False),
            sa.Column("model", sa.String()),
            sa.Column("manufacturer", sa.String()),
            sa.Column("serial_number", sa.String(), unique=True),
            sa.Column("udi_di", sa.String()),
            sa.Column("udi_pi", sa.String()),
            sa.Column("udi_full", sa.String()),
            sa.Column("asset_tag", sa.String(), unique=True),
            sa.Column("category", sa.String(), default="other"),
            sa.Column("risk_class", sa.String(), default="class_i"),
            sa.Column("status", sa.String(), default="available"),
            sa.Column("location_facility_id", sa.String()),
            sa.Column("location_department", sa.String()),
            sa.Column("location_room", sa.String()),
            sa.Column("owning_department", sa.String()),
            sa.Column("responsible_person", sa.String()),
            sa.Column("acquisition_date", sa.DateTime(timezone=True)),
            sa.Column("installation_date", sa.DateTime(timezone=True)),
            sa.Column("commissioning_date", sa.DateTime(timezone=True)),
            sa.Column("warranty_start", sa.DateTime(timezone=True)),
            sa.Column("warranty_end", sa.DateTime(timezone=True)),
            sa.Column("warranty_status", sa.String(), default="active"),
            sa.Column("expected_lifetime_years", sa.Integer(), default=10),
            sa.Column("purchase_cost", sa.Float()),
            sa.Column("current_value", sa.Float()),
            sa.Column("requires_calibration", sa.Boolean(), default=False),
            sa.Column("calibration_frequency_days", sa.Integer(), default=365),
            sa.Column("last_calibration_date", sa.DateTime(timezone=True)),
            sa.Column("next_calibration_due", sa.DateTime(timezone=True)),
            sa.Column("requires_pm", sa.Boolean(), default=True),
            sa.Column("pm_frequency_days", sa.Integer(), default=180),
            sa.Column("last_pm_date", sa.DateTime(timezone=True)),
            sa.Column("next_pm_due", sa.DateTime(timezone=True)),
            sa.Column("lifecycle_stage", sa.String(), default="operational"),
            sa.Column("vendor_id", sa.String()),
            sa.Column("vendor_name", sa.String()),
            sa.Column("contract_id", sa.String()),
            sa.Column("power_rating", sa.String()),
            sa.Column("dimensions", sa.String()),
            sa.Column("weight_kg", sa.Float()),
            sa.Column("software_version", sa.String()),
            sa.Column("firmware_version", sa.String()),
            sa.Column("network_address", sa.String()),
            sa.Column("notes", sa.Text()),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("created_by", sa.Integer()),
            sa.Column("updated_by", sa.Integer()),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_biomed_devices_udi_di", "biomed_devices", ["udi_di"])
        op.create_index("ix_biomed_devices_fhir_id", "biomed_devices", ["fhir_id"])
        op.create_index("ix_biomed_devices_lab_id", "biomed_devices", ["lab_id"])

    if not _table_exists("biomed_work_orders"):
        op.create_table(
            "biomed_work_orders",
            sa.Column("device_id", sa.String(), sa.ForeignKey("biomed_devices.id"), nullable=False),
            sa.Column("device_name", sa.String()),
            sa.Column("work_order_number", sa.String(), unique=True),
            sa.Column("maintenance_type", sa.String(), default="corrective"),
            sa.Column("priority", sa.String(), default="medium"),
            sa.Column("status", sa.String(), default="pending"),
            sa.Column("title", sa.String()),
            sa.Column("description", sa.Text()),
            sa.Column("reported_by", sa.String()),
            sa.Column("reported_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("assigned_to", sa.String()),
            sa.Column("assigned_date", sa.DateTime(timezone=True)),
            sa.Column("started_at", sa.DateTime(timezone=True)),
            sa.Column("completed_at", sa.DateTime(timezone=True)),
            sa.Column("verified_by", sa.String()),
            sa.Column("verified_at", sa.DateTime(timezone=True)),
            sa.Column("downtime_hours", sa.Float()),
            sa.Column("labor_hours", sa.Float()),
            sa.Column("problem_found", sa.Text()),
            sa.Column("action_taken", sa.Text()),
            sa.Column("parts_used", sa.JSON()),
            sa.Column("cost_parts", sa.Float()),
            sa.Column("cost_labor", sa.Float()),
            sa.Column("cost_total", sa.Float()),
            sa.Column("result", sa.Text()),
            sa.Column("result_verified", sa.Boolean(), default=False),
            sa.Column("notes", sa.Text()),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("created_by", sa.Integer()),
            sa.Column("updated_by", sa.Integer()),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_biomed_work_orders_lab_id", "biomed_work_orders", ["lab_id"])
        op.create_index("ix_biomed_work_orders_fhir_id", "biomed_work_orders", ["fhir_id"])
        op.create_index("ix_biomed_work_orders_device_id", "biomed_work_orders", ["device_id"])

    if not _table_exists("biomed_calibrations"):
        op.create_table(
            "biomed_calibrations",
            sa.Column("device_id", sa.String(), sa.ForeignKey("biomed_devices.id"), nullable=False),
            sa.Column("device_name", sa.String()),
            sa.Column("calibration_number", sa.String(), unique=True),
            sa.Column("calibration_type", sa.String(), default="internal"),
            sa.Column("status", sa.String(), default="pending"),
            sa.Column("calibration_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("calibrated_by", sa.String()),
            sa.Column("due_date", sa.DateTime(timezone=True)),
            sa.Column("standard_used", sa.String()),
            sa.Column("standard_id", sa.String()),
            sa.Column("standard_traceability", sa.String()),
            sa.Column("ambient_temperature", sa.Float()),
            sa.Column("ambient_humidity", sa.Float()),
            sa.Column("results", sa.JSON()),
            sa.Column("deviations", sa.JSON()),
            sa.Column("overall_result", sa.String(), default="pending"),
            sa.Column("passed", sa.Boolean(), default=False),
            sa.Column("verified_by", sa.String()),
            sa.Column("verified_at", sa.DateTime(timezone=True)),
            sa.Column("notes", sa.Text()),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("created_by", sa.Integer()),
            sa.Column("updated_by", sa.Integer()),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_biomed_calibrations_fhir_id", "biomed_calibrations", ["fhir_id"])
        op.create_index("ix_biomed_calibrations_lab_id", "biomed_calibrations", ["lab_id"])
        op.create_index("ix_biomed_calibrations_device_id", "biomed_calibrations", ["device_id"])

    if not _table_exists("biomed_safety_inspections"):
        op.create_table(
            "biomed_safety_inspections",
            sa.Column("device_id", sa.String(), sa.ForeignKey("biomed_devices.id"), nullable=False),
            sa.Column("device_name", sa.String()),
            sa.Column("inspection_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("inspected_by", sa.String()),
            sa.Column("inspection_type", sa.String(), default="routine"),
            sa.Column("electrical_safety_pass", sa.Boolean(), default=False),
            sa.Column("earth_leakage", sa.Float()),
            sa.Column("ground_resistance", sa.Float()),
            sa.Column("insulation_resistance", sa.Float()),
            sa.Column("functional_test_pass", sa.Boolean(), default=False),
            sa.Column("visual_inspection_pass", sa.Boolean(), default=False),
            sa.Column("overall_result", sa.String(), default="failed"),
            sa.Column("findings", sa.Text()),
            sa.Column("recommendations", sa.Text()),
            sa.Column("next_inspection_due", sa.DateTime(timezone=True)),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("created_by", sa.Integer()),
            sa.Column("updated_by", sa.Integer()),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_biomed_safety_inspections_lab_id", "biomed_safety_inspections", ["lab_id"])
        op.create_index("ix_biomed_safety_inspections_fhir_id", "biomed_safety_inspections", ["fhir_id"])
        op.create_index("ix_biomed_safety_inspections_device_id", "biomed_safety_inspections", ["device_id"])

    if not _table_exists("biomed_incidents"):
        op.create_table(
            "biomed_incidents",
            sa.Column("device_id", sa.String(), sa.ForeignKey("biomed_devices.id"), nullable=False),
            sa.Column("device_name", sa.String()),
            sa.Column("incident_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("reported_by", sa.String()),
            sa.Column("incident_type", sa.String()),
            sa.Column("severity", sa.String(), default="minor"),
            sa.Column("description", sa.Text()),
            sa.Column("patient_involved", sa.Boolean(), default=False),
            sa.Column("patient_impact", sa.Text()),
            sa.Column("operator_involved", sa.Boolean(), default=False),
            sa.Column("operator_impact", sa.Text()),
            sa.Column("immediate_action", sa.Text()),
            sa.Column("root_cause", sa.Text()),
            sa.Column("corrective_action", sa.Text()),
            sa.Column("fda_reportable", sa.Boolean(), default=False),
            sa.Column("manufacturer_notified", sa.Boolean(), default=False),
            sa.Column("manufacturer_response", sa.Text()),
            sa.Column("closed_at", sa.DateTime(timezone=True)),
            sa.Column("status", sa.String(), default="open"),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("created_by", sa.Integer()),
            sa.Column("updated_by", sa.Integer()),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_biomed_incidents_lab_id", "biomed_incidents", ["lab_id"])
        op.create_index("ix_biomed_incidents_fhir_id", "biomed_incidents", ["fhir_id"])
        op.create_index("ix_biomed_incidents_device_id", "biomed_incidents", ["device_id"])

    if not _table_exists("biomed_recalls"):
        op.create_table(
            "biomed_recalls",
            sa.Column("device_id", sa.String(), sa.ForeignKey("biomed_devices.id"), nullable=False),
            sa.Column("device_name", sa.String()),
            sa.Column("model", sa.String()),
            sa.Column("manufacturer", sa.String()),
            sa.Column("recall_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("recall_class", sa.String(), default="class_ii"),
            sa.Column("recall_reason", sa.Text()),
            sa.Column("recall_number", sa.String()),
            sa.Column("fda_recall_id", sa.String()),
            sa.Column("affected_serial_numbers", sa.JSON()),
            sa.Column("corrective_action", sa.Text()),
            sa.Column("status", sa.String(), default="open"),
            sa.Column("completed_at", sa.DateTime(timezone=True)),
            sa.Column("notes", sa.Text()),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("created_by", sa.Integer()),
            sa.Column("updated_by", sa.Integer()),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_biomed_recalls_fhir_id", "biomed_recalls", ["fhir_id"])
        op.create_index("ix_biomed_recalls_lab_id", "biomed_recalls", ["lab_id"])
        op.create_index("ix_biomed_recalls_device_id", "biomed_recalls", ["device_id"])

    if not _table_exists("biomed_technicians"):
        op.create_table(
            "biomed_technicians",
            sa.Column("user_id", sa.String()),
            sa.Column("full_name", sa.String(), nullable=False),
            sa.Column("specialization", sa.String()),
            sa.Column("certifications", sa.JSON()),
            sa.Column("phone", sa.String()),
            sa.Column("email", sa.String()),
            sa.Column("facility_id", sa.String()),
            sa.Column("is_available", sa.Boolean(), default=True),
            sa.Column("max_work_orders", sa.Integer(), default=5),
            sa.Column("skills", sa.JSON()),
            sa.Column("is_active", sa.Boolean(), default=True),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_biomed_technicians_lab_id", "biomed_technicians", ["lab_id"])
        op.create_index("ix_biomed_technicians_fhir_id", "biomed_technicians", ["fhir_id"])

    if not _table_exists("biomed_vendors"):
        op.create_table(
            "biomed_vendors",
            sa.Column("vendor_name", sa.String(), nullable=False),
            sa.Column("vendor_type", sa.String(), default="manufacturer"),
            sa.Column("contact_person", sa.String()),
            sa.Column("phone", sa.String()),
            sa.Column("email", sa.String()),
            sa.Column("address", sa.Text()),
            sa.Column("website", sa.String()),
            sa.Column("service_coverage", sa.String()),
            sa.Column("is_approved", sa.Boolean(), default=True),
            sa.Column("rating", sa.Float()),
            sa.Column("notes", sa.Text()),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_biomed_vendors_fhir_id", "biomed_vendors", ["fhir_id"])
        op.create_index("ix_biomed_vendors_lab_id", "biomed_vendors", ["lab_id"])

    if not _table_exists("biomed_spare_parts"):
        op.create_table(
            "biomed_spare_parts",
            sa.Column("part_number", sa.String()),
            sa.Column("part_name", sa.String(), nullable=False),
            sa.Column("manufacturer", sa.String()),
            sa.Column("compatible_models", sa.JSON()),
            sa.Column("quantity_in_stock", sa.Integer(), default=0),
            sa.Column("minimum_stock", sa.Integer(), default=1),
            sa.Column("unit_cost", sa.Float()),
            sa.Column("storage_location", sa.String()),
            sa.Column("supplier_id", sa.String()),
            sa.Column("lead_time_days", sa.Integer(), default=30),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_biomed_spare_parts_lab_id", "biomed_spare_parts", ["lab_id"])
        op.create_index("ix_biomed_spare_parts_fhir_id", "biomed_spare_parts", ["fhir_id"])
        op.create_index("ix_biomed_spare_parts_part_number", "biomed_spare_parts", ["part_number"])

    if not _table_exists("biomed_service_contracts"):
        op.create_table(
            "biomed_service_contracts",
            sa.Column("device_id", sa.String(), sa.ForeignKey("biomed_devices.id")),
            sa.Column("vendor_id", sa.String()),
            sa.Column("contract_number", sa.String(), unique=True),
            sa.Column("contract_type", sa.String(), default="full_service"),
            sa.Column("start_date", sa.DateTime(timezone=True)),
            sa.Column("end_date", sa.DateTime(timezone=True)),
            sa.Column("coverage_details", sa.Text()),
            sa.Column("response_time_hours", sa.Integer(), default=24),
            sa.Column("annual_cost", sa.Float()),
            sa.Column("includes_parts", sa.Boolean(), default=True),
            sa.Column("includes_labor", sa.Boolean(), default=True),
            sa.Column("includes_calibration", sa.Boolean(), default=False),
            sa.Column("is_active", sa.Boolean(), default=True),
            sa.Column("notes", sa.Text()),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("created_by", sa.Integer()),
            sa.Column("updated_by", sa.Integer()),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_biomed_service_contracts_lab_id", "biomed_service_contracts", ["lab_id"])
        op.create_index("ix_biomed_service_contracts_fhir_id", "biomed_service_contracts", ["fhir_id"])

    if not _table_exists("biomed_maintenance_schedules"):
        op.create_table(
            "biomed_maintenance_schedules",
            sa.Column("device_id", sa.String(), sa.ForeignKey("biomed_devices.id"), nullable=False),
            sa.Column("device_name", sa.String()),
            sa.Column("maintenance_type", sa.String(), default="preventive"),
            sa.Column("frequency_days", sa.Integer(), default=180),
            sa.Column("last_due_date", sa.DateTime(timezone=True)),
            sa.Column("next_due_date", sa.DateTime(timezone=True)),
            sa.Column("estimated_duration_minutes", sa.Integer(), default=60),
            sa.Column("required_skills", sa.JSON()),
            sa.Column("checklist_items", sa.JSON()),
            sa.Column("is_active", sa.Boolean(), default=True),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_biomed_maintenance_schedules_lab_id", "biomed_maintenance_schedules", ["lab_id"])
        op.create_index("ix_biomed_maintenance_schedules_fhir_id", "biomed_maintenance_schedules", ["fhir_id"])

    if not _table_exists("biomed_performance_verifications"):
        op.create_table(
            "biomed_performance_verifications",
            sa.Column("device_id", sa.String(), sa.ForeignKey("biomed_devices.id"), nullable=False),
            sa.Column("device_name", sa.String()),
            sa.Column("verification_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("verified_by", sa.String()),
            sa.Column("parameters", sa.JSON()),
            sa.Column("results", sa.JSON()),
            sa.Column("overall_result", sa.String(), default="not_performed"),
            sa.Column("deviations", sa.JSON()),
            sa.Column("notes", sa.Text()),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("created_by", sa.Integer()),
            sa.Column("updated_by", sa.Integer()),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_biomed_performance_verifications_lab_id", "biomed_performance_verifications", ["lab_id"])
        op.create_index("ix_biomed_performance_verifications_device_id", "biomed_performance_verifications", ["device_id"])
        op.create_index("ix_biomed_performance_verifications_fhir_id", "biomed_performance_verifications", ["fhir_id"])



def downgrade() -> None:
    if _table_exists("biomed_performance_verifications"):
        op.drop_table("biomed_performance_verifications")
    if _table_exists("biomed_maintenance_schedules"):
        op.drop_table("biomed_maintenance_schedules")
    if _table_exists("biomed_service_contracts"):
        op.drop_table("biomed_service_contracts")
    if _table_exists("biomed_spare_parts"):
        op.drop_table("biomed_spare_parts")
    if _table_exists("biomed_vendors"):
        op.drop_table("biomed_vendors")
    if _table_exists("biomed_technicians"):
        op.drop_table("biomed_technicians")
    if _table_exists("biomed_recalls"):
        op.drop_table("biomed_recalls")
    if _table_exists("biomed_incidents"):
        op.drop_table("biomed_incidents")
    if _table_exists("biomed_safety_inspections"):
        op.drop_table("biomed_safety_inspections")
    if _table_exists("biomed_calibrations"):
        op.drop_table("biomed_calibrations")
    if _table_exists("biomed_work_orders"):
        op.drop_table("biomed_work_orders")
    if _table_exists("biomed_devices"):
        op.drop_table("biomed_devices")
