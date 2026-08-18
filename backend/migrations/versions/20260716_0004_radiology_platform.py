"""Create Radiology Platform tables.

Creates all Radiology domain entities:
  - radiology_orders, radiology_appointments, radiology_protocols
  - radiology_exams, radiology_series, radiology_images
  - radiology_image_annotations, radiology_image_measurements
  - radiology_reports, radiology_critical_findings
  - radiology_report_templates, radiology_modality_devices
  - radiology_worklist_entries, radiology_mpps
  - radiology_dicom_storage, radiology_dicom_studies
  - radiology_image_shares, radiology_ai_analysis_jobs

Revision ID: 20260716_0004
Revises: 20260716_0003
Create Date: 2026-07-16
"""

from typing import Sequence, Union
from alembic import context, op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy import inspect

revision: str = "20260716_0004"
down_revision: Union[str, None] = "20260716_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table: str) -> bool:
    if context.is_offline_mode():
        return True
    return inspect(op.get_bind()).has_table(table)


def _index_exists(idx_name: str) -> bool:
    insp = inspect(op.get_bind())
    for table in insp.get_table_names():
        for idx in insp.get_indexes(table):
            if idx["name"] == idx_name:
                return True
    return False


def upgrade() -> None:
    # ── Radiology Orders ──────────────────────────────────────────────────────
    if not _table_exists("radiology_orders"):
        op.create_table(
            "radiology_orders",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
            sa.Column("accession_number", sa.String(30), unique=True, nullable=False),
            sa.Column("order_number", sa.String(30), nullable=False),
            sa.Column("order_type", sa.String(50), nullable=False),
            sa.Column("priority", sa.String(20), default="routine"),
            sa.Column("status", sa.String(20), nullable=False, server_default="ordered"),
            sa.Column("ordered_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("ordering_physician", sa.String(200), nullable=True),
            sa.Column("ordered_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("clinical_indication", sa.Text(), nullable=True),
            sa.Column("diagnosis_code", sa.String(20), nullable=True),
            sa.Column("icd_code", sa.String(20), nullable=True),
            sa.Column("is_stat", sa.Boolean(), default=False),
            sa.Column("is_inpatient", sa.Boolean(), default=False),
            sa.Column("ward", sa.String(100), nullable=True),
            sa.Column("bed_number", sa.String(20), nullable=True),
            sa.Column("modality", sa.String(50), nullable=True),
            sa.Column("body_part", sa.String(100), nullable=True),
            sa.Column("contrast_required", sa.Boolean(), default=False),
            sa.Column("contrast_details", sa.Text(), nullable=True),
            sa.Column("patient_preparation", sa.Text(), nullable=True),
            sa.Column("cancelled_reason", sa.Text(), nullable=True),
            sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("cancelled_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
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
        op.create_index("ix_radiology_orders_lab_id", "radiology_orders", ["lab_id"])
        op.create_index("ix_radiology_orders_patient_id", "radiology_orders", ["patient_id"])
        op.create_index("ix_radiology_orders_accession_number", "radiology_orders", ["accession_number"])
        op.create_index("ix_radiology_orders_lab_status", "radiology_orders", ["lab_id", "status"])
        op.create_index("ix_radiology_orders_ordered_at", "radiology_orders", ["ordered_at"])

    # ── Modality Devices ──────────────────────────────────────────────────────
    if not _table_exists("radiology_modality_devices"):
        op.create_table(
            "radiology_modality_devices",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("device_code", sa.String(50), nullable=False),
            sa.Column("device_name", sa.String(200), nullable=False),
            sa.Column("modality_type", sa.String(50), nullable=False),
            sa.Column("manufacturer", sa.String(200), nullable=True),
            sa.Column("model", sa.String(200), nullable=True),
            sa.Column("serial_number", sa.String(200), nullable=True),
            sa.Column("ae_title", sa.String(64), nullable=True),
            sa.Column("ip_address", sa.String(45), nullable=True),
            sa.Column("port", sa.Integer(), nullable=True),
            sa.Column("location", sa.String(200), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="online"),
            sa.Column("software_version", sa.String(50), nullable=True),
            sa.Column("installation_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_calibration_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("next_calibration_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("supports_mpps", sa.Boolean(), default=True),
            sa.Column("supports_worklist", sa.Boolean(), default=True),
            sa.Column("is_online", sa.Boolean(), default=True),
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
            sa.UniqueConstraint("lab_id", "device_code", name="uq_radiology_device_code"),
        )
        op.create_index("ix_radiology_modality_devices_lab_id", "radiology_modality_devices", ["lab_id"])
        op.create_index("ix_radiology_modality_devices_modality", "radiology_modality_devices", ["modality_type"])
        op.create_index("ix_radiology_modality_devices_ae_title", "radiology_modality_devices", ["ae_title"])

    # ── Radiology Appointments ────────────────────────────────────────────────
    if not _table_exists("radiology_appointments"):
        op.create_table(
            "radiology_appointments",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("order_id", sa.Integer(), sa.ForeignKey("radiology_orders.id", ondelete="CASCADE"), nullable=False),
            sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
            sa.Column("appointment_number", sa.String(30), unique=True, nullable=False),
            sa.Column("modality", sa.String(50), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="scheduled"),
            sa.Column("scheduled_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("start_time", sa.Time(), nullable=True),
            sa.Column("end_time", sa.Time(), nullable=True),
            sa.Column("actual_start_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("actual_end_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("room", sa.String(50), nullable=True),
            sa.Column("device_id", sa.Integer(), sa.ForeignKey("radiology_modality_devices.id", ondelete="SET NULL"), nullable=True),
            sa.Column("technician_id", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("radiologist_id", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("check_in_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("arrived_late", sa.Boolean(), default=False),
            sa.Column("cancelled_reason", sa.Text(), nullable=True),
            sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
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
        op.create_index("ix_radiology_appointments_lab_id", "radiology_appointments", ["lab_id"])
        op.create_index("ix_radiology_appointments_order_id", "radiology_appointments", ["order_id"])
        op.create_index("ix_radiology_appointments_patient_id", "radiology_appointments", ["patient_id"])
        op.create_index("ix_radiology_appointments_scheduled_date", "radiology_appointments", ["scheduled_date"])
        op.create_index("ix_radiology_appointments_lab_status", "radiology_appointments", ["lab_id", "status"])

    # ── Protocols ─────────────────────────────────────────────────────────────
    if not _table_exists("radiology_protocols"):
        op.create_table(
            "radiology_protocols",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=True),
            sa.Column("protocol_code", sa.String(50), nullable=False),
            sa.Column("protocol_name", sa.String(300), nullable=False),
            sa.Column("protocol_name_ar", sa.String(300), nullable=True),
            sa.Column("modality", sa.String(50), nullable=False),
            sa.Column("body_part", sa.String(100), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("technique", sa.Text(), nullable=True),
            sa.Column("contrast_protocol", sa.Text(), nullable=True),
            sa.Column("parameters", JSON(), nullable=True),
            sa.Column("radiation_dose_mgy", sa.Float(), nullable=True),
            sa.Column("standard_duration_minutes", sa.Integer(), nullable=True),
            sa.Column("preparation_instructions", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), default=True),
            sa.Column("is_national_standard", sa.Boolean(), default=False),
            sa.Column("version", sa.String(20), nullable=True),
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
            sa.UniqueConstraint("lab_id", "protocol_code", name="uq_radiology_protocol_code"),
        )
        op.create_index("ix_radiology_protocols_modality", "radiology_protocols", ["modality"])

    # ── Exams ─────────────────────────────────────────────────────────────────
    if not _table_exists("radiology_exams"):
        op.create_table(
            "radiology_exams",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("order_id", sa.Integer(), sa.ForeignKey("radiology_orders.id", ondelete="CASCADE"), nullable=False),
            sa.Column("appointment_id", sa.Integer(), sa.ForeignKey("radiology_appointments.id", ondelete="SET NULL"), nullable=True),
            sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
            sa.Column("protocol_id", sa.Integer(), sa.ForeignKey("radiology_protocols.id", ondelete="SET NULL"), nullable=True),
            sa.Column("device_id", sa.Integer(), sa.ForeignKey("radiology_modality_devices.id", ondelete="SET NULL"), nullable=True),
            sa.Column("accession_number", sa.String(30), nullable=False),
            sa.Column("exam_number", sa.String(30), nullable=False),
            sa.Column("modality", sa.String(50), nullable=False),
            sa.Column("body_part", sa.String(100), nullable=False),
            sa.Column("laterality", sa.String(20), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="scheduled"),
            sa.Column("technique_description", sa.Text(), nullable=True),
            sa.Column("contrast_used", sa.Boolean(), default=False),
            sa.Column("contrast_type", sa.String(100), nullable=True),
            sa.Column("contrast_volume_ml", sa.Float(), nullable=True),
            sa.Column("radiation_dose_mgy", sa.Float(), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("performed_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("technician_id", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("clinical_findings", sa.Text(), nullable=True),
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
        op.create_index("ix_radiology_exams_lab_id", "radiology_exams", ["lab_id"])
        op.create_index("ix_radiology_exams_order_id", "radiology_exams", ["order_id"])
        op.create_index("ix_radiology_exams_patient_id", "radiology_exams", ["patient_id"])
        op.create_index("ix_radiology_exams_accession_number", "radiology_exams", ["accession_number"])
        op.create_index("ix_radiology_exams_lab_status", "radiology_exams", ["lab_id", "status", "modality"])

    # ── Series ────────────────────────────────────────────────────────────────
    if not _table_exists("radiology_series"):
        op.create_table(
            "radiology_series",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("exam_id", sa.Integer(), sa.ForeignKey("radiology_exams.id", ondelete="CASCADE"), nullable=False),
            sa.Column("series_instance_uid", sa.String(128), unique=True, nullable=False),
            sa.Column("series_number", sa.Integer(), nullable=True),
            sa.Column("modality", sa.String(50), nullable=False),
            sa.Column("body_part", sa.String(100), nullable=True),
            sa.Column("laterality", sa.String(20), nullable=True),
            sa.Column("series_description", sa.String(500), nullable=True),
            sa.Column("number_of_images", sa.Integer(), nullable=True),
            sa.Column("protocol_name", sa.String(200), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("kvp", sa.Float(), nullable=True),
            sa.Column("ma", sa.Float(), nullable=True),
            sa.Column("exposure_time_ms", sa.Float(), nullable=True),
            sa.Column("slice_thickness_mm", sa.Float(), nullable=True),
            sa.Column("spacing_between_slices_mm", sa.Float(), nullable=True),
            sa.Column("pixel_spacing", sa.String(50), nullable=True),
            sa.Column("image_orientation", sa.String(200), nullable=True),
            sa.Column("image_position", sa.String(200), nullable=True),
            sa.Column("series_metadata", JSONB() if op.get_bind().dialect.name == "postgresql" else sa.JSON(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_radiology_series_exam_id", "radiology_series", ["exam_id"])
        op.create_index("ix_radiology_series_modality", "radiology_series", ["modality"])
        op.create_index("ix_radiology_series_instance_uid", "radiology_series", ["series_instance_uid"])

    # ── Images ────────────────────────────────────────────────────────────────
    if not _table_exists("radiology_images"):
        op.create_table(
            "radiology_images",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("series_id", sa.Integer(), sa.ForeignKey("radiology_series.id", ondelete="CASCADE"), nullable=False),
            sa.Column("sop_instance_uid", sa.String(128), unique=True, nullable=False),
            sa.Column("instance_number", sa.Integer(), nullable=True),
            sa.Column("image_type", sa.String(50), nullable=True),
            sa.Column("image_laterality", sa.String(20), nullable=True),
            sa.Column("image_metadata", JSONB() if op.get_bind().dialect.name == "postgresql" else sa.JSON(), nullable=True),
            sa.Column("file_path", sa.String(500), nullable=True),
            sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
            sa.Column("storage_class", sa.String(50), nullable=True),
            sa.Column("checksum", sa.String(64), nullable=True),
            sa.Column("width_px", sa.Integer(), nullable=True),
            sa.Column("height_px", sa.Integer(), nullable=True),
            sa.Column("bits_allocated", sa.Integer(), nullable=True),
            sa.Column("window_center", sa.Float(), nullable=True),
            sa.Column("window_width", sa.Float(), nullable=True),
            sa.Column("is_key_image", sa.Boolean(), default=False),
            sa.Column("is_annotated", sa.Boolean(), default=False),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_radiology_images_series_id", "radiology_images", ["series_id"])
        op.create_index("ix_radiology_images_sop_instance_uid", "radiology_images", ["sop_instance_uid"])

    # ── Image Annotations ─────────────────────────────────────────────────────
    if not _table_exists("radiology_image_annotations"):
        op.create_table(
            "radiology_image_annotations",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("image_id", sa.Integer(), sa.ForeignKey("radiology_images.id", ondelete="CASCADE"), nullable=False),
            sa.Column("exam_id", sa.Integer(), sa.ForeignKey("radiology_exams.id", ondelete="CASCADE"), nullable=False),
            sa.Column("annotation_type", sa.String(50), nullable=False),
            sa.Column("label", sa.String(300), nullable=True),
            sa.Column("coordinates", JSONB() if op.get_bind().dialect.name == "postgresql" else sa.JSON(), nullable=False),
            sa.Column("measurements", JSONB() if op.get_bind().dialect.name == "postgresql" else sa.JSON(), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("created_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("is_verified", sa.Boolean(), default=False),
            sa.Column("verified_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_radiology_annotations_image_id", "radiology_image_annotations", ["image_id"])
        op.create_index("ix_radiology_annotations_exam_id", "radiology_image_annotations", ["exam_id"])
        op.create_index("ix_radiology_annotations_created_by", "radiology_image_annotations", ["created_by"])

    # ── Image Measurements ────────────────────────────────────────────────────
    if not _table_exists("radiology_image_measurements"):
        op.create_table(
            "radiology_image_measurements",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("image_id", sa.Integer(), sa.ForeignKey("radiology_images.id", ondelete="CASCADE"), nullable=False),
            sa.Column("annotation_id", sa.Integer(), sa.ForeignKey("radiology_image_annotations.id", ondelete="SET NULL"), nullable=True),
            sa.Column("exam_id", sa.Integer(), sa.ForeignKey("radiology_exams.id", ondelete="CASCADE"), nullable=False),
            sa.Column("measurement_type", sa.String(50), nullable=False),
            sa.Column("label", sa.String(300), nullable=True),
            sa.Column("value", sa.Float(), nullable=False),
            sa.Column("unit", sa.String(20), nullable=True),
            sa.Column("longest_diameter_mm", sa.Float(), nullable=True),
            sa.Column("shortest_diameter_mm", sa.Float(), nullable=True),
            sa.Column("volume_ml", sa.Float(), nullable=True),
            sa.Column("recist_category", sa.String(20), nullable=True),
            sa.Column("reference_point", JSONB() if op.get_bind().dialect.name == "postgresql" else sa.JSON(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_radiology_measurements_image_id", "radiology_image_measurements", ["image_id"])
        op.create_index("ix_radiology_measurements_exam_id", "radiology_image_measurements", ["exam_id"])
        op.create_index("ix_radiology_measurements_type", "radiology_image_measurements", ["measurement_type"])

    # ── Report Templates ──────────────────────────────────────────────────────
    if not _table_exists("radiology_report_templates"):
        op.create_table(
            "radiology_report_templates",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=True),
            sa.Column("template_code", sa.String(50), nullable=False),
            sa.Column("template_name", sa.String(300), nullable=False),
            sa.Column("template_name_ar", sa.String(300), nullable=True),
            sa.Column("modality", sa.String(50), nullable=True),
            sa.Column("body_part", sa.String(100), nullable=True),
            sa.Column("content_structure", JSONB() if op.get_bind().dialect.name == "postgresql" else sa.JSON(), nullable=True),
            sa.Column("default_text", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), default=True),
            sa.Column("is_shared", sa.Boolean(), default=False),
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
            sa.UniqueConstraint("lab_id", "template_code", name="uq_radiology_template_code"),
        )
        op.create_index("ix_radiology_templates_modality", "radiology_report_templates", ["modality"])

    # ── Critical Findings ─────────────────────────────────────────────────────
    if not _table_exists("radiology_critical_findings"):
        op.create_table(
            "radiology_critical_findings",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("order_id", sa.Integer(), sa.ForeignKey("radiology_orders.id", ondelete="CASCADE"), nullable=False),
            sa.Column("exam_id", sa.Integer(), sa.ForeignKey("radiology_exams.id", ondelete="SET NULL"), nullable=True),
            sa.Column("report_id", sa.Integer(), nullable=True),
            sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
            sa.Column("finding_type", sa.String(100), nullable=False),
            sa.Column("finding_description", sa.Text(), nullable=False),
            sa.Column("severity", sa.String(20), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="open"),
            sa.Column("identified_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("identified_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("notified_to", sa.String(200), nullable=True),
            sa.Column("notified_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("acknowledged_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("action_taken", sa.Text(), nullable=True),
            sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
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
        op.create_index("ix_radiology_critical_lab_id", "radiology_critical_findings", ["lab_id"])
        op.create_index("ix_radiology_critical_patient_id", "radiology_critical_findings", ["patient_id"])
        op.create_index("ix_radiology_critical_status", "radiology_critical_findings", ["lab_id", "status", "severity"])
        op.create_index("ix_radiology_critical_identified_at", "radiology_critical_findings", ["identified_at"])

    # ── Reports ───────────────────────────────────────────────────────────────
    if not _table_exists("radiology_reports"):
        op.create_table(
            "radiology_reports",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("order_id", sa.Integer(), sa.ForeignKey("radiology_orders.id", ondelete="CASCADE"), nullable=False),
            sa.Column("exam_id", sa.Integer(), sa.ForeignKey("radiology_exams.id", ondelete="SET NULL"), nullable=True),
            sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
            sa.Column("report_number", sa.String(30), unique=True, nullable=False),
            sa.Column("accession_number", sa.String(30), nullable=False),
            sa.Column("report_status", sa.String(20), nullable=False, server_default="draft"),
            sa.Column("report_type", sa.String(50), default="final"),
            sa.Column("clinical_indication", sa.Text(), nullable=True),
            sa.Column("technique", sa.Text(), nullable=True),
            sa.Column("comparison", sa.Text(), nullable=True),
            sa.Column("findings", sa.Text(), nullable=True),
            sa.Column("impression", sa.Text(), nullable=True),
            sa.Column("conclusion", sa.Text(), nullable=True),
            sa.Column("recommendations", sa.Text(), nullable=True),
            sa.Column("radiology_code", sa.String(20), nullable=True),
            sa.Column("snomed_codes", JSON(), nullable=True),
            sa.Column("body_parts_examined", JSON(), nullable=True),
            sa.Column("template_id", sa.Integer(), sa.ForeignKey("radiology_report_templates.id", ondelete="SET NULL"), nullable=True),
            sa.Column("drafted_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("drafted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("approved_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_corrected", sa.Boolean(), default=False),
            sa.Column("correction_reason", sa.Text(), nullable=True),
            sa.Column("original_report_id", sa.Integer(), sa.ForeignKey("radiology_reports.id", ondelete="SET NULL"), nullable=True),
            sa.Column("is_critical", sa.Boolean(), default=False),
            sa.Column("critical_finding_id", sa.Integer(), sa.ForeignKey("radiology_critical_findings.id", ondelete="SET NULL"), nullable=True),
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
        op.create_index("ix_radiology_reports_lab_id", "radiology_reports", ["lab_id"])
        op.create_index("ix_radiology_reports_order_id", "radiology_reports", ["order_id"])
        op.create_index("ix_radiology_reports_patient_id", "radiology_reports", ["patient_id"])
        op.create_index("ix_radiology_reports_accession_number", "radiology_reports", ["accession_number"])
        op.create_index("ix_radiology_reports_lab_status", "radiology_reports", ["lab_id", "report_status"])

    # ── Critical Findings FK (deferred—circular dependency) ───────────────────
    if _table_exists("radiology_critical_findings") and _table_exists("radiology_reports"):
        bind = op.get_bind()
        if bind.dialect.name == "sqlite":
            with op.batch_alter_table("radiology_critical_findings", schema=None) as batch_op:
                try:
                    batch_op.create_foreign_key(
                        "fk_radiology_critical_findings_report_id",
                        "radiology_reports",
                        ["report_id"],
                        ["id"],
                        ondelete="SET NULL",
                    )
                except Exception:
                    pass
        else:
            op.create_foreign_key(
                "fk_radiology_critical_findings_report_id",
                "radiology_critical_findings",
                "radiology_reports",
                ["report_id"],
                ["id"],
                ondelete="SET NULL",
            )

    # ── Worklist Entries ──────────────────────────────────────────────────────
    if not _table_exists("radiology_worklist_entries"):
        op.create_table(
            "radiology_worklist_entries",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("order_id", sa.Integer(), sa.ForeignKey("radiology_orders.id", ondelete="CASCADE"), nullable=False),
            sa.Column("appointment_id", sa.Integer(), sa.ForeignKey("radiology_appointments.id", ondelete="SET NULL"), nullable=True),
            sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="SET NULL"), nullable=True),
            sa.Column("device_id", sa.Integer(), sa.ForeignKey("radiology_modality_devices.id", ondelete="SET NULL"), nullable=True),
            sa.Column("accession_number", sa.String(30), nullable=False),
            sa.Column("modality", sa.String(50), nullable=False),
            sa.Column("body_part", sa.String(100), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="scheduled"),
            sa.Column("priority", sa.String(20), default="routine"),
            sa.Column("scheduled_step_start", sa.DateTime(timezone=True), nullable=True),
            sa.Column("scheduled_step_end", sa.DateTime(timezone=True), nullable=True),
            sa.Column("performed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("performed_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
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
        op.create_index("ix_radiology_worklist_lab_id", "radiology_worklist_entries", ["lab_id"])
        op.create_index("ix_radiology_worklist_order_id", "radiology_worklist_entries", ["order_id"])
        op.create_index("ix_radiology_worklist_device_id", "radiology_worklist_entries", ["device_id"])
        op.create_index("ix_radiology_worklist_lab_status", "radiology_worklist_entries", ["lab_id", "status", "modality"])

    # ── MPPS (Modality Performed Procedure Step) ──────────────────────────────
    if not _table_exists("radiology_mpps"):
        op.create_table(
            "radiology_mpps",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("order_id", sa.Integer(), sa.ForeignKey("radiology_orders.id", ondelete="CASCADE"), nullable=False),
            sa.Column("exam_id", sa.Integer(), sa.ForeignKey("radiology_exams.id", ondelete="SET NULL"), nullable=True),
            sa.Column("device_id", sa.Integer(), sa.ForeignKey("radiology_modality_devices.id", ondelete="SET NULL"), nullable=True),
            sa.Column("mpps_uid", sa.String(128), unique=True, nullable=False),
            sa.Column("accession_number", sa.String(30), nullable=False),
            sa.Column("status", sa.String(20), nullable=False),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("discontinued_reason", sa.String(200), nullable=True),
            sa.Column("performed_protocol", JSON(), nullable=True),
            sa.Column("performed_steps", JSON(), nullable=True),
            sa.Column("radiation_dose", JSON(), nullable=True),
            sa.Column("contrast_volume", sa.Float(), nullable=True),
            sa.Column("number_of_images", sa.Integer(), nullable=True),
            sa.Column("comments", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_radiology_mpps_lab_id", "radiology_mpps", ["lab_id"])
        op.create_index("ix_radiology_mpps_order_id", "radiology_mpps", ["order_id"])
        op.create_index("ix_radiology_mpps_device_id", "radiology_mpps", ["device_id"])
        op.create_index("ix_radiology_mpps_status", "radiology_mpps", ["lab_id", "status"])
        op.create_index("ix_radiology_mpps_started_at", "radiology_mpps", ["started_at"])

    # ── DICOM Storage ─────────────────────────────────────────────────────────
    if not _table_exists("radiology_dicom_storage"):
        op.create_table(
            "radiology_dicom_storage",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("study_uid", sa.String(128), nullable=False),
            sa.Column("series_uid", sa.String(128), nullable=True),
            sa.Column("sop_instance_uid", sa.String(128), nullable=False),
            sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="SET NULL"), nullable=True),
            sa.Column("storage_path", sa.String(500), nullable=False),
            sa.Column("storage_type", sa.String(30), nullable=False),
            sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
            sa.Column("checksum", sa.String(64), nullable=True),
            sa.Column("compression", sa.String(30), nullable=True),
            sa.Column("storage_class", sa.String(50), nullable=True),
            sa.Column("is_archived", sa.Boolean(), default=False),
            sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("retention_until", sa.DateTime(timezone=True), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_radiology_dicom_storage_lab_id", "radiology_dicom_storage", ["lab_id"])
        op.create_index("ix_radiology_dicom_storage_study_uid", "radiology_dicom_storage", ["study_uid"])
        op.create_index("ix_radiology_dicom_storage_sop_instance", "radiology_dicom_storage", ["sop_instance_uid"])
        op.create_index("ix_radiology_dicom_storage_is_archived", "radiology_dicom_storage", ["is_archived"])

    # ── DICOM Studies ─────────────────────────────────────────────────────────
    if not _table_exists("radiology_dicom_studies"):
        op.create_table(
            "radiology_dicom_studies",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("order_id", sa.Integer(), sa.ForeignKey("radiology_orders.id", ondelete="SET NULL"), nullable=True),
            sa.Column("exam_id", sa.Integer(), sa.ForeignKey("radiology_exams.id", ondelete="SET NULL"), nullable=True),
            sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="SET NULL"), nullable=True),
            sa.Column("study_instance_uid", sa.String(128), unique=True, nullable=False),
            sa.Column("accession_number", sa.String(30), nullable=False),
            sa.Column("study_id", sa.String(64), nullable=True),
            sa.Column("study_description", sa.String(500), nullable=True),
            sa.Column("modality", sa.String(50), nullable=False),
            sa.Column("body_part", sa.String(100), nullable=True),
            sa.Column("study_date", sa.Date(), nullable=True),
            sa.Column("study_time", sa.Time(), nullable=True),
            sa.Column("number_of_series", sa.Integer(), nullable=True),
            sa.Column("number_of_instances", sa.Integer(), nullable=True),
            sa.Column("referring_physician", sa.String(200), nullable=True),
            sa.Column("performing_physician", sa.String(200), nullable=True),
            sa.Column("study_metadata", JSONB() if op.get_bind().dialect.name == "postgresql" else sa.JSON(), nullable=True),
            sa.Column("dicom_tags", JSONB() if op.get_bind().dialect.name == "postgresql" else sa.JSON(), nullable=True),
            sa.Column("study_size_bytes", sa.BigInteger(), nullable=True),
            sa.Column("is_complete", sa.Boolean(), default=False),
            sa.Column("is_verified", sa.Boolean(), default=False),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_radiology_dicom_studies_lab_id", "radiology_dicom_studies", ["lab_id"])
        op.create_index("ix_radiology_dicom_studies_order_id", "radiology_dicom_studies", ["order_id"])
        op.create_index("ix_radiology_dicom_studies_study_uid", "radiology_dicom_studies", ["study_instance_uid"])
        op.create_index("ix_radiology_dicom_studies_accession", "radiology_dicom_studies", ["accession_number"])
        op.create_index("ix_radiology_dicom_studies_modality", "radiology_dicom_studies", ["modality"])

    # ── Image Shares ──────────────────────────────────────────────────────────
    if not _table_exists("radiology_image_shares"):
        op.create_table(
            "radiology_image_shares",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("study_id", sa.Integer(), sa.ForeignKey("radiology_dicom_studies.id", ondelete="CASCADE"), nullable=True),
            sa.Column("exam_id", sa.Integer(), sa.ForeignKey("radiology_exams.id", ondelete="CASCADE"), nullable=True),
            sa.Column("shared_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=False),
            sa.Column("shared_with_name", sa.String(200), nullable=False),
            sa.Column("shared_with_contact", sa.String(200), nullable=True),
            sa.Column("share_method", sa.String(30), nullable=False),
            sa.Column("share_url", sa.String(500), nullable=True),
            sa.Column("access_token", sa.String(128), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("accessed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("access_count", sa.Integer(), default=0),
            sa.Column("status", sa.String(20), nullable=False, server_default="active"),
            sa.Column("purpose", sa.Text(), nullable=True),
            sa.Column("consent_obtained", sa.Boolean(), default=True),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
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
        op.create_index("ix_radiology_image_shares_lab_id", "radiology_image_shares", ["lab_id"])
        op.create_index("ix_radiology_image_shares_study_id", "radiology_image_shares", ["study_id"])
        op.create_index("ix_radiology_image_shares_shared_by", "radiology_image_shares", ["shared_by"])
        op.create_index("ix_radiology_image_shares_status", "radiology_image_shares", ["lab_id", "status"])

    # ── AI Analysis Jobs ──────────────────────────────────────────────────────
    if not _table_exists("radiology_ai_analysis_jobs"):
        op.create_table(
            "radiology_ai_analysis_jobs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("exam_id", sa.Integer(), sa.ForeignKey("radiology_exams.id", ondelete="CASCADE"), nullable=False),
            sa.Column("series_id", sa.Integer(), sa.ForeignKey("radiology_series.id", ondelete="SET NULL"), nullable=True),
            sa.Column("image_id", sa.Integer(), sa.ForeignKey("radiology_images.id", ondelete="SET NULL"), nullable=True),
            sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="SET NULL"), nullable=True),
            sa.Column("job_type", sa.String(50), nullable=False),
            sa.Column("model_name", sa.String(200), nullable=False),
            sa.Column("model_version", sa.String(50), nullable=True),
            sa.Column("input_parameters", JSONB() if op.get_bind().dialect.name == "postgresql" else sa.JSON(), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
            sa.Column("priority", sa.Integer(), default=0),
            sa.Column("queued_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("result", JSONB() if op.get_bind().dialect.name == "postgresql" else sa.JSON(), nullable=True),
            sa.Column("confidence_score", sa.Float(), nullable=True),
            sa.Column("processing_time_ms", sa.Integer(), nullable=True),
            sa.Column("is_reviewed", sa.Boolean(), default=False),
            sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
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
        op.create_index("ix_radiology_ai_jobs_lab_id", "radiology_ai_analysis_jobs", ["lab_id"])
        op.create_index("ix_radiology_ai_jobs_exam_id", "radiology_ai_analysis_jobs", ["exam_id"])
        op.create_index("ix_radiology_ai_jobs_series_id", "radiology_ai_analysis_jobs", ["series_id"])
        op.create_index("ix_radiology_ai_jobs_lab_status", "radiology_ai_analysis_jobs", ["lab_id", "status"])
        op.create_index("ix_radiology_ai_jobs_type", "radiology_ai_analysis_jobs", ["job_type", "status"])


def downgrade() -> None:
    tables = [
        "radiology_ai_analysis_jobs",
        "radiology_image_shares",
        "radiology_dicom_studies",
        "radiology_dicom_storage",
        "radiology_mpps",
        "radiology_worklist_entries",
        "radiology_modality_devices",
        "radiology_report_templates",
        "radiology_critical_findings",
        "radiology_reports",
        "radiology_image_measurements",
        "radiology_image_annotations",
        "radiology_images",
        "radiology_series",
        "radiology_exams",
        "radiology_protocols",
        "radiology_appointments",
        "radiology_orders",
    ]
    for table in tables:
        if _table_exists(table):
            op.drop_table(table)
