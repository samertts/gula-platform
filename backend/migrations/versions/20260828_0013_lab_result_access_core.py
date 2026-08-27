"""Canonical Laboratory, Result, and Clinical Access core.

This migration is additive. Legacy ``lab_orders``/``lab_results``/``niam_consents``
are intentionally not altered; the new domains use separate canonical tables and
opaque polymorphic resource references where cross-domain ownership is explicit.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "20260828_0013"
down_revision: str | None = "20260827_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _inspector():
    return inspect(op.get_bind())


def _table_exists(table_name: str) -> bool:
    return _inspector().has_table(table_name)


def _index_exists(table: str, name: str) -> bool:
    if not _table_exists(table):
        return False
    return any(item.get("name") == name for item in _inspector().get_indexes(table))


def _index(name: str, table: str, columns: list[str]) -> None:
    if not _index_exists(table, name):
        op.create_index(name, table, columns, unique=False)


def upgrade() -> None:
    if not _table_exists("core_clinical_command_receipts"):
        op.create_table(
            "core_clinical_command_receipts",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("actor_account_id", sa.String(26), sa.ForeignKey("niam_accounts.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("operation", sa.String(100), nullable=False),
            sa.Column("idempotency_key", sa.String(128), nullable=False),
            sa.Column("request_fingerprint", sa.String(64), nullable=False),
            sa.Column("resource_id", sa.String(26), nullable=True),
            sa.Column("status", sa.String(24), nullable=False, server_default="CLAIMED"),
            sa.Column("response_body", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("actor_account_id", "operation", "idempotency_key", name="uq_core_clinical_command_receipt"),
            sa.CheckConstraint("status IN ('CLAIMED','COMPLETED','REJECTED')", name="ck_core_clinical_command_receipt_status"),
        )
        _index("ix_core_clinical_command_receipt_actor", "core_clinical_command_receipts", ["actor_account_id"])
        _index("ix_core_clinical_command_receipt_resource", "core_clinical_command_receipts", ["resource_id"])
        _index("ix_core_clinical_command_receipt_lookup", "core_clinical_command_receipts", ["actor_account_id", "operation", "created_at"])

    if not _table_exists("core_lab_orders"):
        op.create_table(
            "core_lab_orders",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("encounter_id", sa.String(26), sa.ForeignKey("core_encounters.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("patient_person_id", sa.String(26), sa.ForeignKey("niam_persons.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("ordering_provider_account_id", sa.String(26), sa.ForeignKey("niam_accounts.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("laboratory_id", sa.String(26), sa.ForeignKey("niam_admin_facilities.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("organization_id", sa.String(26), sa.ForeignKey("niam_organizations.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("facility_id", sa.String(26), sa.ForeignKey("niam_admin_facilities.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("workspace_id", sa.String(26), sa.ForeignKey("niam_workspaces.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("status", sa.String(24), nullable=False, server_default="DRAFT"),
            sa.Column("priority", sa.String(16), nullable=False, server_default="ROUTINE"),
            sa.Column("clinical_indication", sa.Text(), nullable=True),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("verified_by_account_id", sa.String(26), sa.ForeignKey("niam_accounts.id", ondelete="RESTRICT"), nullable=True),
            sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.CheckConstraint("status IN ('DRAFT','PLACED','VERIFIED','ACCEPTED','IN_PROGRESS','COMPLETED','REJECTED','CANCELLED')", name="ck_core_lab_order_status"),
            sa.CheckConstraint("priority IN ('ROUTINE','URGENT','STAT')", name="ck_core_lab_order_priority"),
            sa.CheckConstraint("version > 0", name="ck_core_lab_order_version_positive"),
        )
        _index("ix_core_lab_orders_encounter", "core_lab_orders", ["encounter_id"])
        _index("ix_core_lab_orders_patient", "core_lab_orders", ["patient_person_id"])
        _index("ix_core_lab_orders_provider", "core_lab_orders", ["ordering_provider_account_id"])
        _index("ix_core_lab_orders_laboratory", "core_lab_orders", ["laboratory_id"])
        _index("ix_core_lab_orders_scope_status", "core_lab_orders", ["organization_id", "facility_id", "workspace_id", "status", "created_at"])
        _index("ix_core_lab_orders_patient_created", "core_lab_orders", ["patient_person_id", "created_at"])

    if not _table_exists("core_lab_order_items"):
        op.create_table(
            "core_lab_order_items",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("lab_order_id", sa.String(26), sa.ForeignKey("core_lab_orders.id", ondelete="CASCADE"), nullable=False),
            sa.Column("test_code", sa.String(120), nullable=False),
            sa.Column("test_name", sa.String(240), nullable=False),
            sa.Column("specimen_type", sa.String(80), nullable=False),
            sa.Column("status", sa.String(24), nullable=False, server_default="ORDERED"),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("lab_order_id", "test_code", name="uq_core_lab_order_item_test"),
            sa.CheckConstraint("status IN ('ORDERED','COLLECTED','RECEIVED','PROCESSING','COMPLETED','REJECTED','CANCELLED')", name="ck_core_lab_order_item_status"),
            sa.CheckConstraint("version > 0", name="ck_core_lab_order_item_version_positive"),
        )
        _index("ix_core_lab_order_items_order", "core_lab_order_items", ["lab_order_id"])
        _index("ix_core_lab_order_items_test", "core_lab_order_items", ["test_code", "created_at"])

    if not _table_exists("core_specimens"):
        op.create_table(
            "core_specimens",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("lab_order_id", sa.String(26), sa.ForeignKey("core_lab_orders.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("order_item_id", sa.String(26), sa.ForeignKey("core_lab_order_items.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("encounter_id", sa.String(26), sa.ForeignKey("core_encounters.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("patient_person_id", sa.String(26), sa.ForeignKey("niam_persons.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("laboratory_id", sa.String(26), sa.ForeignKey("niam_admin_facilities.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("organization_id", sa.String(26), sa.ForeignKey("niam_organizations.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("facility_id", sa.String(26), sa.ForeignKey("niam_admin_facilities.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("workspace_id", sa.String(26), sa.ForeignKey("niam_workspaces.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("specimen_type", sa.String(80), nullable=False),
            sa.Column("accession_number", sa.String(80), nullable=False),
            sa.Column("barcode", sa.String(120), nullable=False),
            sa.Column("status", sa.String(24), nullable=False, server_default="ORDERED"),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("collector_account_id", sa.String(26), sa.ForeignKey("niam_accounts.id", ondelete="RESTRICT"), nullable=True),
            sa.Column("receiver_account_id", sa.String(26), sa.ForeignKey("niam_accounts.id", ondelete="RESTRICT"), nullable=True),
            sa.Column("collected_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("rejection_reason", sa.String(500), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("order_item_id", name="uq_core_specimen_order_item"),
            sa.UniqueConstraint("accession_number", name="uq_core_specimen_accession"),
            sa.UniqueConstraint("barcode", name="uq_core_specimen_barcode"),
            sa.CheckConstraint("status IN ('ORDERED','COLLECTED','RECEIVED','PROCESSING','ANALYZING','VALIDATED','REJECTED')", name="ck_core_specimen_status"),
            sa.CheckConstraint("version > 0", name="ck_core_specimen_version_positive"),
        )
        _index("ix_core_specimens_order", "core_specimens", ["lab_order_id"])
        _index("ix_core_specimens_item", "core_specimens", ["order_item_id"])
        _index("ix_core_specimens_encounter", "core_specimens", ["encounter_id"])
        _index("ix_core_specimens_patient", "core_specimens", ["patient_person_id"])
        _index("ix_core_specimens_laboratory", "core_specimens", ["laboratory_id"])
        _index("ix_core_specimens_scope_status", "core_specimens", ["organization_id", "facility_id", "workspace_id", "status", "created_at"])
        _index("ix_core_specimens_lab_worklist", "core_specimens", ["laboratory_id", "status", "created_at"])

    if not _table_exists("core_specimen_events"):
        op.create_table(
            "core_specimen_events",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("specimen_id", sa.String(26), sa.ForeignKey("core_specimens.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("event_type", sa.String(48), nullable=False),
            sa.Column("previous_state", sa.String(24), nullable=False),
            sa.Column("new_state", sa.String(24), nullable=False),
            sa.Column("actor_account_id", sa.String(26), sa.ForeignKey("niam_accounts.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("laboratory_id", sa.String(26), sa.ForeignKey("niam_admin_facilities.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("organization_id", sa.String(26), sa.ForeignKey("niam_organizations.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("facility_id", sa.String(26), sa.ForeignKey("niam_admin_facilities.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("workspace_id", sa.String(26), sa.ForeignKey("niam_workspaces.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("correlation_id", sa.String(128), nullable=False),
            sa.Column("event_metadata", sa.JSON(), nullable=True),
            sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.CheckConstraint("length(trim(event_type)) > 0", name="ck_core_specimen_event_type_nonempty"),
        )
        _index("ix_core_specimen_events_specimen", "core_specimen_events", ["specimen_id"])
        _index("ix_core_specimen_events_type", "core_specimen_events", ["event_type"])
        _index("ix_core_specimen_events_timeline", "core_specimen_events", ["specimen_id", "occurred_at", "id"])

    if not _table_exists("core_lab_results"):
        op.create_table(
            "core_lab_results",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("result_id", sa.String(26), nullable=False),
            sa.Column("specimen_id", sa.String(26), sa.ForeignKey("core_specimens.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("lab_order_id", sa.String(26), sa.ForeignKey("core_lab_orders.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("order_item_id", sa.String(26), sa.ForeignKey("core_lab_order_items.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("encounter_id", sa.String(26), sa.ForeignKey("core_encounters.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("patient_person_id", sa.String(26), sa.ForeignKey("niam_persons.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("laboratory_id", sa.String(26), sa.ForeignKey("niam_admin_facilities.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("organization_id", sa.String(26), sa.ForeignKey("niam_organizations.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("facility_id", sa.String(26), sa.ForeignKey("niam_admin_facilities.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("workspace_id", sa.String(26), sa.ForeignKey("niam_workspaces.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("value_numeric", sa.Numeric(20, 6), nullable=True),
            sa.Column("value_text", sa.Text(), nullable=True),
            sa.Column("unit", sa.String(40), nullable=True),
            sa.Column("reference_low", sa.Numeric(20, 6), nullable=True),
            sa.Column("reference_high", sa.Numeric(20, 6), nullable=True),
            sa.Column("abnormal_flag", sa.String(24), nullable=True),
            sa.Column("test_code", sa.String(120), nullable=False),
            sa.Column("test_name", sa.String(240), nullable=False),
            sa.Column("provenance_type", sa.String(32), nullable=False, server_default="MANUAL"),
            sa.Column("source_message_id", sa.String(200), nullable=True),
            sa.Column("analyzer_code", sa.String(120), nullable=True),
            sa.Column("technical_validated_by", sa.String(26), sa.ForeignKey("niam_accounts.id", ondelete="RESTRICT"), nullable=True),
            sa.Column("technical_validated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("clinically_validated_by", sa.String(26), sa.ForeignKey("niam_accounts.id", ondelete="RESTRICT"), nullable=True),
            sa.Column("clinically_validated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("supersedes_id", sa.String(26), nullable=True),
            sa.Column("amendment_reason", sa.String(500), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("result_id", "version", name="uq_core_lab_result_version"),
            sa.UniqueConstraint("source_message_id", name="uq_core_lab_result_source_message"),
            sa.CheckConstraint("status IN ('DRAFT','TECHNICALLY_VALIDATED','CLINICALLY_VALIDATED','RELEASED','CORRECTED','AMENDED')", name="ck_core_lab_result_status"),
            sa.CheckConstraint("provenance_type IN ('MANUAL','ANALYZER','IMPORTED_SYNTHETIC')", name="ck_core_lab_result_provenance"),
            sa.CheckConstraint("version > 0", name="ck_core_lab_result_version_positive"),
            sa.CheckConstraint("reference_high IS NULL OR reference_low IS NULL OR reference_high >= reference_low", name="ck_core_lab_result_reference_range"),
        )
        _index("ix_core_lab_results_specimen", "core_lab_results", ["specimen_id"])
        _index("ix_core_lab_results_order", "core_lab_results", ["lab_order_id"])
        _index("ix_core_lab_results_patient", "core_lab_results", ["patient_person_id"])
        _index("ix_core_lab_results_scope_status", "core_lab_results", ["organization_id", "facility_id", "workspace_id", "status", "created_at"])
        _index("ix_core_lab_results_patient_status", "core_lab_results", ["patient_person_id", "status", "created_at"])

    if not _table_exists("core_critical_result_events"):
        op.create_table(
            "core_critical_result_events",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("result_id", sa.String(26), sa.ForeignKey("core_lab_results.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("patient_person_id", sa.String(26), sa.ForeignKey("niam_persons.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("organization_id", sa.String(26), sa.ForeignKey("niam_organizations.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("facility_id", sa.String(26), sa.ForeignKey("niam_admin_facilities.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("workspace_id", sa.String(26), sa.ForeignKey("niam_workspaces.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("severity", sa.String(16), nullable=False),
            sa.Column("status", sa.String(24), nullable=False, server_default="DETECTED"),
            sa.Column("required_action", sa.String(500), nullable=False),
            sa.Column("acknowledged_by", sa.String(26), sa.ForeignKey("niam_accounts.id", ondelete="RESTRICT"), nullable=True),
            sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("closed_by", sa.String(26), sa.ForeignKey("niam_accounts.id", ondelete="RESTRICT"), nullable=True),
            sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("resolution_reason", sa.String(500), nullable=True),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("result_id", name="uq_core_critical_result_result"),
            sa.CheckConstraint("severity IN ('HIGH','CRITICAL')", name="ck_core_critical_result_severity"),
            sa.CheckConstraint("status IN ('DETECTED','NOTIFIED','ACKNOWLEDGED','ACTIONED','ESCALATED','CLOSED')", name="ck_core_critical_result_status"),
            sa.CheckConstraint("version > 0", name="ck_core_critical_result_version_positive"),
        )
        _index("ix_core_critical_result_events_result", "core_critical_result_events", ["result_id"])
        _index("ix_core_critical_result_events_scope_status", "core_critical_result_events", ["organization_id", "facility_id", "workspace_id", "status", "created_at"])

    if not _table_exists("core_clinical_notifications"):
        op.create_table(
            "core_clinical_notifications",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("event_key", sa.String(200), nullable=False),
            sa.Column("recipient_account_id", sa.String(26), sa.ForeignKey("niam_accounts.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("event_type", sa.String(80), nullable=False),
            sa.Column("channel", sa.String(32), nullable=False, server_default="SYNTHETIC"),
            sa.Column("status", sa.String(24), nullable=False, server_default="PENDING"),
            sa.Column("payload", sa.JSON(), nullable=False),
            sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("last_error", sa.String(500), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("event_key", name="uq_core_clinical_notification_event"),
            sa.CheckConstraint("channel IN ('SYNTHETIC','INTERNAL')", name="ck_core_notification_channel"),
            sa.CheckConstraint("status IN ('PENDING','DELIVERED','FAILED','ACKNOWLEDGED','ESCALATED')", name="ck_core_notification_status"),
            sa.CheckConstraint("attempt_count >= 0", name="ck_core_notification_attempts"),
        )
        _index("ix_core_clinical_notifications_recipient", "core_clinical_notifications", ["recipient_account_id"])
        _index("ix_core_clinical_notifications_status", "core_clinical_notifications", ["status", "created_at"])

    if not _table_exists("core_access_grants"):
        op.create_table(
            "core_access_grants",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("patient_person_id", sa.String(26), sa.ForeignKey("niam_persons.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("grantee_account_id", sa.String(26), sa.ForeignKey("niam_accounts.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("resource_type", sa.String(40), nullable=False),
            sa.Column("resource_id", sa.String(26), nullable=False),
            sa.Column("organization_id", sa.String(26), sa.ForeignKey("niam_organizations.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("facility_id", sa.String(26), sa.ForeignKey("niam_admin_facilities.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("workspace_id", sa.String(26), sa.ForeignKey("niam_workspaces.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("purpose", sa.String(40), nullable=False),
            sa.Column("scope", sa.JSON(), nullable=False),
            sa.Column("status", sa.String(24), nullable=False, server_default="ACTIVE"),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("reason", sa.String(500), nullable=True),
            sa.Column("created_by_account_id", sa.String(26), sa.ForeignKey("niam_accounts.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("revoked_by_account_id", sa.String(26), sa.ForeignKey("niam_accounts.id", ondelete="RESTRICT"), nullable=True),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("supersedes_id", sa.String(26), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("patient_person_id", "grantee_account_id", "resource_type", "resource_id", "version", name="uq_core_access_grant_version"),
            sa.CheckConstraint("status IN ('ACTIVE','EXPIRED','REVOKED')", name="ck_core_access_grant_status"),
            sa.CheckConstraint("purpose IN ('TREATMENT','RESEARCH','BILLING','AUDIT','PUBLIC_HEALTH')", name="ck_core_access_grant_purpose"),
            sa.CheckConstraint("version > 0", name="ck_core_access_grant_version_positive"),
        )
        _index("ix_core_access_grants_patient", "core_access_grants", ["patient_person_id"])
        _index("ix_core_access_grants_grantee", "core_access_grants", ["grantee_account_id"])
        _index("ix_core_access_grants_resource", "core_access_grants", ["resource_id"])
        _index("ix_core_access_grants_effective", "core_access_grants", ["grantee_account_id", "resource_type", "resource_id", "status", "expires_at"])
        _index("ix_core_access_grants_patient_status", "core_access_grants", ["patient_person_id", "status", "created_at"])

    if not _table_exists("core_access_history"):
        op.create_table(
            "core_access_history",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("grant_id", sa.String(26), sa.ForeignKey("core_access_grants.id", ondelete="RESTRICT"), nullable=True),
            sa.Column("patient_person_id", sa.String(26), sa.ForeignKey("niam_persons.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("actor_account_id", sa.String(26), sa.ForeignKey("niam_accounts.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("resource_type", sa.String(40), nullable=False),
            sa.Column("resource_id", sa.String(26), nullable=False),
            sa.Column("organization_id", sa.String(26), sa.ForeignKey("niam_organizations.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("facility_id", sa.String(26), sa.ForeignKey("niam_admin_facilities.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("workspace_id", sa.String(26), sa.ForeignKey("niam_workspaces.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("purpose", sa.String(40), nullable=True),
            sa.Column("scope", sa.JSON(), nullable=True),
            sa.Column("action", sa.String(48), nullable=False),
            sa.Column("decision", sa.String(16), nullable=False),
            sa.Column("reason_code", sa.String(80), nullable=True),
            sa.Column("correlation_id", sa.String(128), nullable=False),
            sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.CheckConstraint("decision IN ('ALLOW','DENY')", name="ck_core_access_history_decision"),
            sa.CheckConstraint("length(trim(action)) > 0", name="ck_core_access_history_action_nonempty"),
        )
        _index("ix_core_access_history_grant", "core_access_history", ["grant_id"])
        _index("ix_core_access_history_patient", "core_access_history", ["patient_person_id"])
        _index("ix_core_access_history_resource", "core_access_history", ["resource_id"])
        _index("ix_core_access_history_patient_time", "core_access_history", ["patient_person_id", "occurred_at", "id"])
        _index("ix_core_access_history_scope_time", "core_access_history", ["organization_id", "facility_id", "workspace_id", "occurred_at"])

    _seed_permissions()


def _seed_permissions() -> None:
    if not _table_exists("niam_permissions"):
        return
    bind = op.get_bind()
    rows = (
        ("P13LABORDERCREATE000000001", "clinical.lab_order.create", "Create laboratory order", "إنشاء طلب مختبر", "lab_order", "create"),
        ("P13LABORDERREAD0000000001", "clinical.lab_order.read", "Read laboratory order", "قراءة طلب مختبر", "lab_order", "read"),
        ("P13LABORDERVERIFY0000001", "clinical.lab_order.verify", "Verify laboratory order", "تحقق طلب مختبر", "lab_order", "verify"),
        ("P13SPECIMENMANAGE000001", "clinical.specimen.manage", "Manage specimen custody", "إدارة سلسلة حيازة العينة", "specimen", "manage"),
        ("P13RESULTWRITE00000000001", "clinical.result.write", "Write laboratory result", "كتابة نتيجة مختبر", "lab_result", "write"),
        ("P13RESULTREAD00000000001", "clinical.result.read", "Read laboratory result", "قراءة نتيجة مختبر", "lab_result", "read"),
        ("P13RESULTTECHVALID00001", "clinical.result.validate_technical", "Technically validate result", "التحقق الفني من النتيجة", "lab_result", "validate_technical"),
        ("P13RESULTCLINVALID00001", "clinical.result.validate_clinical", "Clinically validate result", "التحقق السريري من النتيجة", "lab_result", "validate_clinical"),
        ("P13RESULTRELEASE000001", "clinical.result.release", "Release laboratory result", "إصدار نتيجة مختبر", "lab_result", "release"),
        ("P13RESULTAMEND00000001", "clinical.result.amend", "Amend laboratory result", "تعديل إصدار نتيجة مختبر", "lab_result", "amend"),
        ("P13CRITICALACK00000001", "clinical.critical.acknowledge", "Acknowledge critical result", "تأكيد نتيجة حرجة", "critical_result", "acknowledge"),
    )
    for index, row in enumerate(rows):
        exists = bind.execute(sa.text("SELECT 1 FROM niam_permissions WHERE permission_key = :permission_key"), {"permission_key": row[1]}).scalar()
        if not exists:
            bind.execute(
                sa.text(
                    "INSERT INTO niam_permissions "
                    "(id, uuid, permission_key, name, name_ar, description, resource, action, sensitivity, status, version, created_at, updated_at) "
                    "VALUES (:id, :uuid, :permission_key, :name, :name_ar, :description, :resource, :action, 'high', 'active', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                ),
                {"id": row[0], "uuid": f"p13-clinical-{index:02d}", "permission_key": row[1], "name": row[2], "name_ar": row[3], "description": row[2], "resource": row[4], "action": row[5]},
            )



def downgrade() -> None:
    for table in (
        "core_access_history",
        "core_access_grants",
        "core_clinical_notifications",
        "core_critical_result_events",
        "core_lab_results",
        "core_specimen_events",
        "core_specimens",
        "core_lab_order_items",
        "core_lab_orders",
        "core_clinical_command_receipts",
    ):
        if _table_exists(table):
            op.drop_table(table)
