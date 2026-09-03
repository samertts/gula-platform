"""Additive LIS test catalog, analyzer trust, message and QC boundaries.

Revision ID: 20260828_0018
Revises: 20260828_0017
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260828_0018"
down_revision: str | None = "20260828_0017"
branch_labels = None
depends_on = None


def _table_exists(table: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table)


def _index_exists(index: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(index == item["name"] for table in inspector.get_table_names() for item in inspector.get_indexes(table))


def upgrade() -> None:
    if not _table_exists("core_lab_test_catalog"):
        op.create_table("core_lab_test_catalog", sa.Column("id", sa.String(26), primary_key=True), sa.Column("laboratory_id", sa.String(26), nullable=False), sa.Column("organization_id", sa.String(26), nullable=False), sa.Column("facility_id", sa.String(26), nullable=False), sa.Column("canonical_code", sa.String(120), nullable=False), sa.Column("local_code", sa.String(120)), sa.Column("name", sa.String(240), nullable=False), sa.Column("system", sa.String(120), nullable=False), sa.Column("specimen_type", sa.String(80), nullable=False), sa.Column("unit_ucum", sa.String(80)), sa.Column("method", sa.String(160)), sa.Column("reference_range", sa.JSON(), nullable=False, server_default=sa.text("'{}'")), sa.Column("critical_range", sa.JSON(), nullable=False, server_default=sa.text("'{}'")), sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("version", sa.Integer(), nullable=False, server_default="1"), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")), sa.UniqueConstraint("facility_id", "canonical_code", "version", name="uq_core_lab_test_catalog_version"), sa.CheckConstraint("version > 0", name="ck_core_lab_test_catalog_version"))
    if not _table_exists("core_lab_analyzers"):
        op.create_table("core_lab_analyzers", sa.Column("id", sa.String(26), primary_key=True), sa.Column("laboratory_id", sa.String(26), nullable=False), sa.Column("organization_id", sa.String(26), nullable=False), sa.Column("facility_id", sa.String(26), nullable=False), sa.Column("section", sa.String(120), nullable=False), sa.Column("manufacturer", sa.String(160), nullable=False), sa.Column("model", sa.String(160), nullable=False), sa.Column("serial_fingerprint", sa.String(128), nullable=False), sa.Column("protocol", sa.String(32), nullable=False), sa.Column("status", sa.String(24), nullable=False, server_default="REGISTERED"), sa.Column("configuration_version", sa.Integer(), nullable=False, server_default="1"), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")), sa.UniqueConstraint("facility_id", "serial_fingerprint", name="uq_core_lab_analyzer_serial"), sa.CheckConstraint("status IN ('REGISTERED','VALIDATED','ACTIVE','MAINTENANCE','QUARANTINED','RETIRED')", name="ck_core_lab_analyzer_status"), sa.CheckConstraint("protocol IN ('ASTM','HL7_V2','FHIR','FILE','SYNTHETIC')", name="ck_core_lab_analyzer_protocol"))
    if not _table_exists("core_lab_analyzer_messages"):
        op.create_table("core_lab_analyzer_messages", sa.Column("id", sa.String(26), primary_key=True), sa.Column("message_id", sa.String(160), nullable=False), sa.Column("analyzer_id", sa.String(26), nullable=False), sa.Column("lab_order_id", sa.String(26), nullable=False), sa.Column("specimen_id", sa.String(26), nullable=False), sa.Column("patient_person_id", sa.String(26), nullable=False), sa.Column("test_code", sa.String(120), nullable=False), sa.Column("payload_hash", sa.String(64), nullable=False), sa.Column("quality_flags", sa.JSON(), nullable=False, server_default=sa.text("'{}'")), sa.Column("status", sa.String(24), nullable=False, server_default="RECEIVED"), sa.Column("source", sa.String(32), nullable=False, server_default="SYNTHETIC"), sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")), sa.Column("received_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")), sa.UniqueConstraint("message_id", name="uq_core_lab_analyzer_message_id"), sa.CheckConstraint("status IN ('RECEIVED','VALIDATED','REJECTED','DUPLICATE')", name="ck_core_lab_analyzer_message_status"), sa.CheckConstraint("source IN ('SYNTHETIC','HL7_V2','ASTM','FHIR','FILE')", name="ck_core_lab_analyzer_message_source"))
    if not _table_exists("core_lab_quality_controls"):
        op.create_table("core_lab_quality_controls", sa.Column("id", sa.String(26), primary_key=True), sa.Column("result_id", sa.String(26), nullable=False), sa.Column("analyzer_id", sa.String(26)), sa.Column("organization_id", sa.String(26), nullable=False), sa.Column("facility_id", sa.String(26), nullable=False), sa.Column("workspace_id", sa.String(26), nullable=False), sa.Column("status", sa.String(24), nullable=False, server_default="PENDING"), sa.Column("reason", sa.String(500)), sa.Column("override_reason", sa.String(500)), sa.Column("performed_by_account_id", sa.String(26), nullable=False), sa.Column("version", sa.Integer(), nullable=False, server_default="1"), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")), sa.UniqueConstraint("result_id", name="uq_core_lab_qc_result"), sa.CheckConstraint("status IN ('PENDING','PASS','FAILED','OVERRIDDEN')", name="ck_core_lab_qc_status"), sa.CheckConstraint("version > 0", name="ck_core_lab_qc_version"))
    for name, table, columns in (("ix_core_lab_test_catalog_scope", "core_lab_test_catalog", ("facility_id", "canonical_code", "active")), ("ix_core_lab_analyzer_scope_status", "core_lab_analyzers", ("organization_id", "facility_id", "status")), ("ix_core_lab_analyzer_message_specimen", "core_lab_analyzer_messages", ("specimen_id", "occurred_at", "received_at")), ("ix_core_lab_qc_scope_status", "core_lab_quality_controls", ("organization_id", "facility_id", "workspace_id", "status"))):
        if not _index_exists(name):
            op.create_index(name, table, list(columns))
    permissions = (("P18LABANLM000001", "clinical.laboratory.analyzer.manage", "Manage laboratory analyzers", "إدارة أجهزة المختبر", "lab_analyzer", "manage"), ("P18LABANLI000001", "clinical.laboratory.analyzer.ingest", "Ingest analyzer messages", "استلام رسائل المحلل", "lab_analyzer_message", "ingest"), ("P18LABQCM0000001", "clinical.laboratory.qc.write", "Record laboratory QC", "تسجيل ضبط جودة المختبر", "lab_quality_control", "write"))
    for index, row in enumerate(permissions):
        if _table_exists("niam_permissions") and not op.get_bind().execute(sa.text("SELECT 1 FROM niam_permissions WHERE permission_key = :permission_key"), {"permission_key": row[1]}).scalar():
            op.get_bind().execute(sa.text("INSERT INTO niam_permissions (id, uuid, permission_key, name, name_ar, description, resource, action, sensitivity, status, version, created_at, updated_at) VALUES (:id, :uuid, :permission_key, :name, :name_ar, :description, :resource, :action, 'high', 'active', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"), {"id": row[0], "uuid": f"p18-lis-{index:02d}", "permission_key": row[1], "name": row[2], "name_ar": row[3], "description": row[2], "resource": row[4], "action": row[5]})


def downgrade() -> None:
    for table in ("core_lab_quality_controls", "core_lab_analyzer_messages", "core_lab_analyzers", "core_lab_test_catalog"):
        if _table_exists(table):
            op.drop_table(table)
