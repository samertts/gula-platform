"""Add canonical pharmacy, imaging and clinical-record source tables.

This revision is additive. It deliberately does not alter legacy pharmacy,
radiology or EHR tables and does not create a second identity, patient, audit
or sharing store.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "20260828_0014"
down_revision: str | None = "20260828_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _inspector():
    return inspect(op.get_bind())


def _table_exists(table: str) -> bool:
    return _inspector().has_table(table)


def _legacy_table_exists(name: str) -> bool:
    return _inspector().has_table(name)


def _index_exists(table: str, name: str) -> bool:
    return _table_exists(table) and any(item.get("name") == name for item in _inspector().get_indexes(table))


def _index(name: str, table: str, columns: list[str]) -> None:
    if not _index_exists(table, name):
        op.create_index(name, table, columns, unique=False)


def upgrade() -> None:
    if not _table_exists("core_medication_catalog"):
        op.create_table(
            "core_medication_catalog",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("code", sa.String(120), nullable=False, unique=True),
            sa.Column("code_system", sa.String(80), nullable=False, server_default="SYNTHETIC"),
            sa.Column("generic_name", sa.String(300), nullable=False),
            sa.Column("brand_name", sa.String(300)),
            sa.Column("strength_value", sa.String(80)),
            sa.Column("strength_unit", sa.String(40)),
            sa.Column("dosage_form", sa.String(80)),
            sa.Column("route", sa.String(80)),
            sa.Column("is_controlled", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.CheckConstraint("is_controlled IN (0,1)", name="ck_core_medication_controlled_bool"),
            sa.CheckConstraint("is_active IN (0,1)", name="ck_core_medication_active_bool"),
        )
    _index("ix_core_medication_active_name", "core_medication_catalog", ["is_active", "generic_name"])

    if not _table_exists("core_prescriptions"):
        op.create_table(
            "core_prescriptions",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("prescription_id", sa.String(26), nullable=False),
            sa.Column("prescription_number", sa.String(80), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("encounter_id", sa.String(26), nullable=False),
            sa.Column("patient_person_id", sa.String(26), nullable=False),
            sa.Column("prescriber_account_id", sa.String(26), nullable=False),
            sa.Column("organization_id", sa.String(26), nullable=False),
            sa.Column("facility_id", sa.String(26), nullable=False),
            sa.Column("workspace_id", sa.String(26), nullable=False),
            sa.Column("status", sa.String(24), nullable=False, server_default="DRAFT"),
            sa.Column("purpose", sa.String(40), nullable=False, server_default="treatment"),
            sa.Column("controlled_policy_status", sa.String(32), nullable=False, server_default="NOT_CONTROLLED"),
            sa.Column("signed_by_account_id", sa.String(26)),
            sa.Column("signed_at", sa.DateTime(timezone=True)),
            sa.Column("supersedes_id", sa.String(26)),
            sa.Column("amendment_reason", sa.String(500)),
            sa.Column("note", sa.Text()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["encounter_id"], ["core_encounters.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["patient_person_id"], ["niam_persons.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["prescriber_account_id"], ["niam_accounts.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["organization_id"], ["niam_organizations.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["facility_id"], ["niam_admin_facilities.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["workspace_id"], ["niam_workspaces.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["signed_by_account_id"], ["niam_accounts.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["supersedes_id"], ["core_prescriptions.id"], ondelete="RESTRICT"),
            sa.CheckConstraint("version > 0", name="ck_core_prescription_version_positive"),
            sa.CheckConstraint("status IN ('DRAFT','SIGNED','AMENDED','CANCELLED','COMPLETED')", name="ck_core_prescription_status"),
            sa.CheckConstraint("controlled_policy_status IN ('NOT_CONTROLLED','PENDING_POLICY_REVIEW','REJECTED_BY_POLICY')", name="ck_core_prescription_controlled_policy"),
            sa.UniqueConstraint("prescription_id", "version", name="uq_core_prescription_version"),
            sa.UniqueConstraint("prescription_number", "version", name="uq_core_prescription_number_version"),
        )
    _index("ix_core_prescription_scope_status", "core_prescriptions", ["organization_id", "facility_id", "workspace_id", "status", "created_at"])
    _index("ix_core_prescription_patient_created", "core_prescriptions", ["patient_person_id", "created_at"])

    if not _table_exists("core_prescription_items"):
        op.create_table(
            "core_prescription_items",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("prescription_row_id", sa.String(26), nullable=False),
            sa.Column("medication_catalog_id", sa.String(26), nullable=False),
            sa.Column("medication_code", sa.String(120), nullable=False),
            sa.Column("medication_name", sa.String(300), nullable=False),
            sa.Column("dose_value", sa.String(80), nullable=False),
            sa.Column("dose_unit", sa.String(40), nullable=False),
            sa.Column("frequency", sa.String(120), nullable=False),
            sa.Column("route", sa.String(80), nullable=False),
            sa.Column("duration_days", sa.Integer(), nullable=False),
            sa.Column("quantity", sa.Integer(), nullable=False),
            sa.Column("quantity_unit", sa.String(40), nullable=False),
            sa.Column("substitution_allowed", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("instructions", sa.Text()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["prescription_row_id"], ["core_prescriptions.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["medication_catalog_id"], ["core_medication_catalog.id"], ondelete="RESTRICT"),
            sa.CheckConstraint("duration_days > 0", name="ck_core_prescription_item_duration_positive"),
            sa.CheckConstraint("quantity > 0", name="ck_core_prescription_item_quantity_positive"),
            sa.CheckConstraint("substitution_allowed = 0", name="ck_core_prescription_item_no_auto_substitution"),
        )
    _index("ix_core_prescription_item_row", "core_prescription_items", ["prescription_row_id", "created_at"])
    _index("ix_core_prescription_item_medication", "core_prescription_items", ["medication_catalog_id"])

    if not _table_exists("core_medication_batches"):
        op.create_table(
            "core_medication_batches",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("medication_catalog_id", sa.String(26), nullable=False),
            sa.Column("batch_number", sa.String(120), nullable=False),
            sa.Column("organization_id", sa.String(26), nullable=False),
            sa.Column("facility_id", sa.String(26), nullable=False),
            sa.Column("workspace_id", sa.String(26), nullable=False),
            sa.Column("expiry_date", sa.Date(), nullable=False),
            sa.Column("quantity_received", sa.Integer(), nullable=False),
            sa.Column("quantity_available", sa.Integer(), nullable=False),
            sa.Column("quarantined", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["medication_catalog_id"], ["core_medication_catalog.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["organization_id"], ["niam_organizations.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["facility_id"], ["niam_admin_facilities.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["workspace_id"], ["niam_workspaces.id"], ondelete="RESTRICT"),
            sa.UniqueConstraint("facility_id", "medication_catalog_id", "batch_number", name="uq_core_medication_batch_facility"),
            sa.CheckConstraint("quantity_received >= 0", name="ck_core_medication_batch_received_nonnegative"),
            sa.CheckConstraint("quantity_available >= 0", name="ck_core_medication_batch_available_nonnegative"),
            sa.CheckConstraint("quantity_available <= quantity_received", name="ck_core_medication_batch_available_lte_received"),
            sa.CheckConstraint("quarantined IN (0,1)", name="ck_core_medication_batch_quarantine_bool"),
        )
    _index("ix_core_medication_batch_scope_expiry", "core_medication_batches", ["organization_id", "facility_id", "workspace_id", "expiry_date"])

    if not _table_exists("core_medication_stock_ledger"):
        op.create_table(
            "core_medication_stock_ledger",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("batch_id", sa.String(26), nullable=False),
            sa.Column("medication_catalog_id", sa.String(26), nullable=False),
            sa.Column("organization_id", sa.String(26), nullable=False),
            sa.Column("facility_id", sa.String(26), nullable=False),
            sa.Column("workspace_id", sa.String(26), nullable=False),
            sa.Column("movement_type", sa.String(32), nullable=False),
            sa.Column("quantity_delta", sa.Integer(), nullable=False),
            sa.Column("reference_type", sa.String(64), nullable=False),
            sa.Column("reference_id", sa.String(26), nullable=False),
            sa.Column("actor_account_id", sa.String(26), nullable=False),
            sa.Column("correlation_id", sa.String(128), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("metadata", sa.JSON()),
            sa.ForeignKeyConstraint(["batch_id"], ["core_medication_batches.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["medication_catalog_id"], ["core_medication_catalog.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["organization_id"], ["niam_organizations.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["facility_id"], ["niam_admin_facilities.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["workspace_id"], ["niam_workspaces.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["actor_account_id"], ["niam_accounts.id"], ondelete="RESTRICT"),
            sa.CheckConstraint("quantity_delta <> 0", name="ck_core_stock_ledger_delta_nonzero"),
            sa.CheckConstraint("movement_type IN ('RECEIPT','DISPENSE','ADJUSTMENT_REVERSAL')", name="ck_core_stock_ledger_movement"),
        )
    _index("ix_core_stock_ledger_batch_time", "core_medication_stock_ledger", ["batch_id", "created_at", "id"])

    if not _table_exists("core_medication_dispenses"):
        op.create_table(
            "core_medication_dispenses",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("prescription_row_id", sa.String(26), nullable=False),
            sa.Column("prescription_item_id", sa.String(26), nullable=False),
            sa.Column("patient_person_id", sa.String(26), nullable=False),
            sa.Column("medication_catalog_id", sa.String(26), nullable=False),
            sa.Column("batch_id", sa.String(26), nullable=False),
            sa.Column("organization_id", sa.String(26), nullable=False),
            sa.Column("facility_id", sa.String(26), nullable=False),
            sa.Column("workspace_id", sa.String(26), nullable=False),
            sa.Column("quantity", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(24), nullable=False, server_default="PREPARED"),
            sa.Column("prepared_by_account_id", sa.String(26), nullable=False),
            sa.Column("dispensed_by_account_id", sa.String(26)),
            sa.Column("verified_by_account_id", sa.String(26)),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("correlation_id", sa.String(128), nullable=False),
            sa.Column("dispensed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["prescription_row_id"], ["core_prescriptions.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["prescription_item_id"], ["core_prescription_items.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["medication_catalog_id"], ["core_medication_catalog.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["batch_id"], ["core_medication_batches.id"], ondelete="RESTRICT"),
            sa.CheckConstraint("quantity > 0", name="ck_core_dispense_quantity_positive"),
            sa.CheckConstraint("status IN ('PREPARED','PARTIAL','COMPLETED','REVERSED')", name="ck_core_dispense_status"),
            sa.CheckConstraint("version > 0", name="ck_core_dispense_version_positive"),
        )
    _index("ix_core_dispense_patient_time", "core_medication_dispenses", ["patient_person_id", "dispensed_at"])
    _index("ix_core_dispense_scope_time", "core_medication_dispenses", ["organization_id", "facility_id", "workspace_id", "dispensed_at"])

    if not _table_exists("core_imaging_orders"):
        op.create_table(
            "core_imaging_orders",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("order_id", sa.String(26), nullable=False, unique=True),
            sa.Column("encounter_id", sa.String(26), nullable=False),
            sa.Column("patient_person_id", sa.String(26), nullable=False),
            sa.Column("ordering_provider_account_id", sa.String(26), nullable=False),
            sa.Column("organization_id", sa.String(26), nullable=False),
            sa.Column("facility_id", sa.String(26), nullable=False),
            sa.Column("workspace_id", sa.String(26), nullable=False),
            sa.Column("accession_number", sa.String(80), nullable=False, unique=True),
            sa.Column("modality", sa.String(32), nullable=False),
            sa.Column("body_part", sa.String(120)),
            sa.Column("clinical_indication", sa.Text()),
            sa.Column("priority", sa.String(16), nullable=False, server_default="ROUTINE"),
            sa.Column("status", sa.String(24), nullable=False, server_default="DRAFT"),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.CheckConstraint("status IN ('DRAFT','PLACED','SCHEDULED','IN_PROGRESS','COMPLETED','CANCELLED')", name="ck_core_imaging_order_status"),
            sa.CheckConstraint("priority IN ('ROUTINE','URGENT','STAT')", name="ck_core_imaging_order_priority"),
            sa.CheckConstraint("version > 0", name="ck_core_imaging_order_version_positive"),
        )
    _index("ix_core_imaging_order_scope_status", "core_imaging_orders", ["organization_id", "facility_id", "workspace_id", "status", "created_at"])
    _index("ix_core_imaging_order_patient_created", "core_imaging_orders", ["patient_person_id", "created_at"])

    if not _table_exists("core_imaging_studies"):
        op.create_table(
            "core_imaging_studies",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("study_id", sa.String(26), nullable=False, unique=True),
            sa.Column("order_id", sa.String(26), nullable=False),
            sa.Column("patient_person_id", sa.String(26), nullable=False),
            sa.Column("organization_id", sa.String(26), nullable=False),
            sa.Column("facility_id", sa.String(26), nullable=False),
            sa.Column("workspace_id", sa.String(26), nullable=False),
            sa.Column("study_instance_uid", sa.String(128), nullable=False, unique=True),
            sa.Column("accession_number", sa.String(80), nullable=False),
            sa.Column("modality", sa.String(32), nullable=False),
            sa.Column("study_description", sa.String(256)),
            sa.Column("status", sa.String(24), nullable=False, server_default="RECEIVED"),
            sa.Column("provenance_type", sa.String(32), nullable=False, server_default="SYNTHETIC_ADAPTER"),
            sa.Column("source_message_id", sa.String(200), nullable=False, unique=True),
            sa.Column("quarantine_reason", sa.String(500)),
            sa.Column("series_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("instance_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("received_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("completed_at", sa.DateTime(timezone=True)),
            sa.Column("metadata", sa.JSON()),
            sa.ForeignKeyConstraint(["order_id"], ["core_imaging_orders.id"], ondelete="RESTRICT"),
            sa.CheckConstraint("status IN ('RECEIVED','MATCHED','ACQUIRED','COMPLETED','QUARANTINED')", name="ck_core_imaging_study_status"),
            sa.CheckConstraint("provenance_type IN ('SYNTHETIC_ADAPTER','DICOMWEB_ADAPTER','PACS_ADAPTER')", name="ck_core_imaging_study_provenance"),
            sa.CheckConstraint("series_count >= 0", name="ck_core_imaging_study_series_nonnegative"),
            sa.CheckConstraint("instance_count >= 0", name="ck_core_imaging_study_instances_nonnegative"),
            sa.CheckConstraint("version > 0", name="ck_core_imaging_study_version_positive"),
        )
    _index("ix_core_imaging_study_scope_status", "core_imaging_studies", ["organization_id", "facility_id", "workspace_id", "status", "received_at"])
    _index("ix_core_imaging_study_patient_time", "core_imaging_studies", ["patient_person_id", "received_at"])

    if not _table_exists("core_imaging_reports"):
        op.create_table(
            "core_imaging_reports",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("report_id", sa.String(26), nullable=False),
            sa.Column("study_id", sa.String(26), nullable=False),
            sa.Column("patient_person_id", sa.String(26), nullable=False),
            sa.Column("ordering_provider_account_id", sa.String(26), nullable=False),
            sa.Column("radiologist_account_id", sa.String(26), nullable=False),
            sa.Column("organization_id", sa.String(26), nullable=False),
            sa.Column("facility_id", sa.String(26), nullable=False),
            sa.Column("workspace_id", sa.String(26), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("status", sa.String(24), nullable=False, server_default="DRAFT"),
            sa.Column("findings", sa.Text()),
            sa.Column("impression", sa.Text()),
            sa.Column("critical", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("supersedes_id", sa.String(26)),
            sa.Column("amendment_reason", sa.String(500)),
            sa.Column("signed_at", sa.DateTime(timezone=True)),
            sa.Column("released_at", sa.DateTime(timezone=True)),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["study_id"], ["core_imaging_studies.id"], ondelete="RESTRICT"),
            sa.CheckConstraint("status IN ('DRAFT','SIGNED','RELEASED','AMENDED')", name="ck_core_imaging_report_status"),
            sa.CheckConstraint("critical IN (0,1)", name="ck_core_imaging_report_critical_bool"),
            sa.CheckConstraint("version > 0", name="ck_core_imaging_report_version_positive"),
            sa.UniqueConstraint("report_id", "version", name="uq_core_imaging_report_version"),
        )
    _index("ix_core_imaging_report_scope_status", "core_imaging_reports", ["organization_id", "facility_id", "workspace_id", "status", "created_at"])
    _index("ix_core_imaging_report_patient_time", "core_imaging_reports", ["patient_person_id", "created_at"])

    if not _table_exists("core_imaging_instances"):
        op.create_table(
            "core_imaging_instances",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("study_id", sa.String(26), nullable=False),
            sa.Column("series_instance_uid", sa.String(128), nullable=False),
            sa.Column("sop_instance_uid", sa.String(128), nullable=False, unique=True),
            sa.Column("patient_person_id", sa.String(26), nullable=False),
            sa.Column("provenance_type", sa.String(32), nullable=False),
            sa.Column("source_message_id", sa.String(200), nullable=False, unique=True),
            sa.Column("object_reference", sa.String(512), nullable=False),
            sa.Column("checksum", sa.String(128), nullable=False),
            sa.Column("file_size_bytes", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["study_id"], ["core_imaging_studies.id"], ondelete="RESTRICT"),
            sa.CheckConstraint("file_size_bytes > 0", name="ck_core_imaging_instance_size_positive"),
            sa.CheckConstraint("object_reference NOT LIKE 'http://%' AND object_reference NOT LIKE 'https://%'", name="ck_core_imaging_instance_no_public_url"),
        )
    _index("ix_core_imaging_instance_study_series", "core_imaging_instances", ["study_id", "series_instance_uid"])

    if not _table_exists("core_imaging_critical_events"):
        op.create_table(
            "core_imaging_critical_events",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("report_id", sa.String(26), nullable=False, unique=True),
            sa.Column("patient_person_id", sa.String(26), nullable=False),
            sa.Column("organization_id", sa.String(26), nullable=False),
            sa.Column("facility_id", sa.String(26), nullable=False),
            sa.Column("workspace_id", sa.String(26), nullable=False),
            sa.Column("status", sa.String(24), nullable=False, server_default="DETECTED"),
            sa.Column("severity", sa.String(16), nullable=False, server_default="CRITICAL"),
            sa.Column("required_action", sa.String(500), nullable=False),
            sa.Column("acknowledged_by_account_id", sa.String(26)),
            sa.Column("acknowledged_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["report_id"], ["core_imaging_reports.id"], ondelete="RESTRICT"),
            sa.CheckConstraint("status IN ('DETECTED','NOTIFIED','ACKNOWLEDGED','CLOSED')", name="ck_core_imaging_critical_status"),
            sa.CheckConstraint("severity IN ('HIGH','CRITICAL')", name="ck_core_imaging_critical_severity"),
            sa.CheckConstraint("version > 0", name="ck_core_imaging_critical_version_positive"),
        )

    permissions = (
        ("P14MEDCATALOG00000001", "clinical.medication.catalog_manage", "Manage medication catalog", "إدارة دليل الأدوية", "medication", "catalog_manage"),
        ("P14MEDPRESCRIBE0000001", "clinical.medication.prescribe", "Prescribe medication", "وصف الدواء", "medication", "prescribe"),
        ("P14MEDSIGN00000000001", "clinical.medication.sign", "Sign prescription", "توقيع الوصفة", "prescription", "sign"),
        ("P14MEDAMEND0000000001", "clinical.medication.amend", "Amend prescription", "تعديل الوصفة بإصدار جديد", "prescription", "amend"),
        ("P14MEDINVENTORY000001", "clinical.medication.inventory", "Manage medication inventory", "إدارة مخزون الأدوية", "medication", "inventory"),
        ("P14MEDDISPENSE0000001", "clinical.medication.dispense", "Prepare and dispense medication", "تحضير وصرف الدواء", "medication", "dispense"),
        ("P14MEDREAD0000000001", "clinical.medication.read", "Read medication history", "قراءة تاريخ الدواء", "medication", "read"),
        ("P14IMGORDER0000000001", "clinical.imaging.order", "Order imaging", "طلب التصوير الطبي", "imaging", "order"),
        ("P14IMGINGEST00000001", "clinical.imaging.ingest", "Ingest imaging metadata", "استلام بيانات التصوير", "imaging", "ingest"),
        ("P14IMGWRITE000000001", "clinical.imaging.report.write", "Write imaging report", "كتابة تقرير التصوير", "imaging_report", "write"),
        ("P14IMGSIGN0000000001", "clinical.imaging.report.sign", "Sign imaging report", "توقيع تقرير التصوير", "imaging_report", "sign"),
        ("P14IMGRELEASE0000001", "clinical.imaging.report.release", "Release imaging report", "إصدار تقرير التصوير", "imaging_report", "release"),
        ("P14IMGAMEND00000001", "clinical.imaging.report.amend", "Amend imaging report", "تعديل تقرير التصوير بإصدار جديد", "imaging_report", "amend"),
        ("P14IMGCRITACK0000001", "clinical.imaging.critical_ack", "Acknowledge critical imaging finding", "تأكيد نتيجة تصوير حرجة", "imaging_critical", "acknowledge"),
        ("P14IMGREAD000000001", "clinical.imaging.report.read", "Read imaging report", "قراءة تقرير التصوير", "imaging_report", "read"),
        ("P14RECORDREAD0000001", "clinical.record.read", "Read unified clinical record", "قراءة السجل السريري الموحد", "clinical_record", "read"),
    )
    for index, row in enumerate(permissions):
        exists = op.get_bind().execute(sa.text("SELECT 1 FROM niam_permissions WHERE permission_key = :permission_key"), {"permission_key": row[1]}).scalar()
        if not exists:
            op.get_bind().execute(
                sa.text("INSERT INTO niam_permissions (id, uuid, permission_key, name, name_ar, description, resource, action, sensitivity, status, version, created_at, updated_at) VALUES (:id, :uuid, :permission_key, :name, :name_ar, :description, :resource, :action, 'high', 'active', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"),
                {"id": row[0], "uuid": f"p14-clinical-{index:02d}", "permission_key": row[1], "name": row[2], "name_ar": row[3], "description": row[2], "resource": row[4], "action": row[5]},
            )


def downgrade() -> None:
    for table in (
        "core_imaging_critical_events",
        "core_imaging_instances",
        "core_imaging_reports",
        "core_imaging_studies",
        "core_imaging_orders",
        "core_medication_dispenses",
        "core_medication_stock_ledger",
        "core_medication_batches",
        "core_prescription_items",
        "core_prescriptions",
        "core_medication_catalog",
    ):
        if _table_exists(table):
            op.drop_table(table)
