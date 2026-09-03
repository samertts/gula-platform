"""Add canonical Emergency/EMS and NIAM health-identity hardening.

This revision is additive. Emergency external delivery remains a synthetic
outbox intent and Health ID ownership remains CitizenLifecycle/NIAM.
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "20260828_0016"
down_revision: str | None = "20260828_0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _inspector():
    return inspect(op.get_bind())


def _table_exists(table: str) -> bool:
    return _inspector().has_table(table)


def _column_exists(table: str, column: str) -> bool:
    return _table_exists(table) and any(item.get("name") == column for item in _inspector().get_columns(table))


def _index_exists(table: str, name: str) -> bool:
    return _table_exists(table) and any(item.get("name") == name for item in _inspector().get_indexes(table))


def _index(name: str, table: str, columns: list[str], *, unique: bool = False) -> None:
    if _table_exists(table) and not _index_exists(table, name):
        op.create_index(name, table, columns, unique=unique)


def _add_session_column(column: sa.Column) -> None:
    name = str(column.name)
    if not _column_exists("niam_sessions", name):
        op.add_column("niam_sessions", column)


def upgrade() -> None:
    if not _table_exists("core_emergency_temporary_subjects"):
        op.create_table(
            "core_emergency_temporary_subjects",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("temporary_subject_id", sa.String(64), nullable=False),
            sa.Column("organization_id", sa.String(26), nullable=False),
            sa.Column("facility_id", sa.String(26), nullable=False),
            sa.Column("workspace_id", sa.String(26), nullable=False),
            sa.Column("created_by_account_id", sa.String(26), nullable=False),
            sa.Column("status", sa.String(24), nullable=False, server_default="UNVERIFIED"),
            sa.Column("synthetic_label", sa.String(160), nullable=False),
            sa.Column("reconciliation_status", sa.String(24), nullable=False, server_default="UNMATCHED"),
            sa.Column("reconciled_person_id", sa.String(26), nullable=True),
            sa.Column("reconciliation_reason", sa.Text(), nullable=True),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("temporary_subject_id", name="uq_core_emergency_temp_subject"),
            sa.CheckConstraint("status IN ('UNVERIFIED','ACTIVE','RECONCILED','RETIRED')", name="ck_core_emergency_temp_status"),
            sa.CheckConstraint("reconciliation_status IN ('UNMATCHED','PENDING_REVIEW','MATCHED','REJECTED')", name="ck_core_emergency_temp_reconciliation"),
            sa.CheckConstraint("version > 0", name="ck_core_emergency_temp_version"),
        )

    if not _table_exists("core_emergency_incidents"):
        op.create_table(
            "core_emergency_incidents",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("incident_id", sa.String(64), nullable=False),
            sa.Column("subject_kind", sa.String(16), nullable=False),
            sa.Column("patient_person_id", sa.String(26), nullable=True),
            sa.Column("temporary_subject_id", sa.String(26), nullable=True),
            sa.Column("encounter_id", sa.String(26), nullable=True),
            sa.Column("organization_id", sa.String(26), nullable=False),
            sa.Column("facility_id", sa.String(26), nullable=False),
            sa.Column("workspace_id", sa.String(26), nullable=False),
            sa.Column("reported_by_account_id", sa.String(26), nullable=False),
            sa.Column("status", sa.String(32), nullable=False, server_default="REPORTED"),
            sa.Column("priority", sa.String(16), nullable=False, server_default="URGENT"),
            sa.Column("chief_complaint", sa.Text(), nullable=False),
            sa.Column("location_summary", sa.String(500), nullable=True),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("reported_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("incident_id", name="uq_core_emergency_incident"),
            sa.CheckConstraint("subject_kind IN ('KNOWN_PATIENT','TEMPORARY')", name="ck_core_emergency_subject_kind"),
            sa.CheckConstraint("(subject_kind = 'KNOWN_PATIENT' AND patient_person_id IS NOT NULL AND temporary_subject_id IS NULL) OR (subject_kind = 'TEMPORARY' AND patient_person_id IS NULL AND temporary_subject_id IS NOT NULL)", name="ck_core_emergency_subject_exclusive"),
            sa.CheckConstraint("status IN ('REPORTED','TRIAGED','DISPATCHED','EN_ROUTE','ON_SCENE','TRANSPORTING','AT_DESTINATION','HANDOVER_COMPLETE','CLOSED','CANCELLED')", name="ck_core_emergency_incident_status"),
            sa.CheckConstraint("priority IN ('ROUTINE','URGENT','STAT','CRITICAL')", name="ck_core_emergency_priority"),
            sa.CheckConstraint("version > 0", name="ck_core_emergency_incident_version"),
        )

    if not _table_exists("core_emergency_dispatches"):
        op.create_table(
            "core_emergency_dispatches",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("dispatch_request_id", sa.String(100), nullable=False),
            sa.Column("incident_id", sa.String(26), nullable=False),
            sa.Column("ambulance_reference", sa.String(120), nullable=False),
            sa.Column("crew_references", sa.JSON(), nullable=False),
            sa.Column("status", sa.String(24), nullable=False, server_default="ASSIGNED"),
            sa.Column("assigned_by_account_id", sa.String(26), nullable=False),
            sa.Column("dispatch_notes", sa.Text(), nullable=True),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("dispatch_request_id", name="uq_core_emergency_dispatch_request"),
            sa.CheckConstraint("status IN ('ASSIGNED','EN_ROUTE','ON_SCENE','TRANSPORTING','AT_DESTINATION','COMPLETED','CANCELLED')", name="ck_core_emergency_dispatch_status"),
            sa.CheckConstraint("version > 0", name="ck_core_emergency_dispatch_version"),
        )

    if not _table_exists("core_emergency_triage_assessments"):
        op.create_table(
            "core_emergency_triage_assessments",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("triage_id", sa.String(64), nullable=False),
            sa.Column("incident_id", sa.String(26), nullable=False),
            sa.Column("patient_person_id", sa.String(26), nullable=True),
            sa.Column("temporary_subject_id", sa.String(26), nullable=True),
            sa.Column("category", sa.String(24), nullable=False),
            sa.Column("clinician_summary", sa.Text(), nullable=False),
            sa.Column("vital_snapshot", sa.JSON(), nullable=False),
            sa.Column("assessed_by_account_id", sa.String(26), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("triage_id", name="uq_core_emergency_triage"),
            sa.CheckConstraint("category IN ('IMMEDIATE','VERY_URGENT','URGENT','STANDARD','DELAYED','EXPECTANT')", name="ck_core_emergency_triage_category"),
            sa.CheckConstraint("version > 0", name="ck_core_emergency_triage_version"),
        )

    if not _table_exists("core_emergency_treatments"):
        op.create_table(
            "core_emergency_treatments",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("treatment_request_id", sa.String(100), nullable=False),
            sa.Column("incident_id", sa.String(26), nullable=False),
            sa.Column("patient_person_id", sa.String(26), nullable=True),
            sa.Column("temporary_subject_id", sa.String(26), nullable=True),
            sa.Column("treatment_type", sa.String(100), nullable=False),
            sa.Column("treatment_details", sa.Text(), nullable=False),
            sa.Column("performed_by_account_id", sa.String(26), nullable=False),
            sa.Column("performed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("treatment_request_id", name="uq_core_emergency_treatment_request"),
        )

    if not _table_exists("core_emergency_prealerts"):
        op.create_table(
            "core_emergency_prealerts",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("prealert_request_id", sa.String(100), nullable=False),
            sa.Column("incident_id", sa.String(26), nullable=False),
            sa.Column("destination_facility_reference", sa.String(120), nullable=False),
            sa.Column("acuity", sa.String(24), nullable=False),
            sa.Column("estimated_arrival_minutes", sa.Integer(), nullable=False),
            sa.Column("minimal_payload", sa.JSON(), nullable=False),
            sa.Column("delivery_mode", sa.String(32), nullable=False, server_default="SYNTHETIC_INTENT"),
            sa.Column("status", sa.String(24), nullable=False, server_default="PENDING"),
            sa.Column("created_by_account_id", sa.String(26), nullable=False),
            sa.Column("acknowledged_by_account_id", sa.String(26), nullable=True),
            sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("prealert_request_id", name="uq_core_emergency_prealert_request"),
            sa.CheckConstraint("estimated_arrival_minutes >= 0 AND estimated_arrival_minutes <= 1440", name="ck_core_prealert_eta_bounds"),
            sa.CheckConstraint("delivery_mode = 'SYNTHETIC_INTENT'", name="ck_core_prealert_synthetic_only"),
            sa.CheckConstraint("status IN ('PENDING','ACKNOWLEDGED','EXPIRED','FAILED')", name="ck_core_prealert_status"),
            sa.CheckConstraint("version > 0", name="ck_core_prealert_version"),
        )

    if not _table_exists("core_emergency_handovers"):
        op.create_table(
            "core_emergency_handovers",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("handover_request_id", sa.String(100), nullable=False),
            sa.Column("incident_id", sa.String(26), nullable=False),
            sa.Column("receiving_facility_reference", sa.String(120), nullable=False),
            sa.Column("patient_person_id", sa.String(26), nullable=True),
            sa.Column("temporary_subject_id", sa.String(26), nullable=True),
            sa.Column("minimal_summary", sa.JSON(), nullable=False),
            sa.Column("submitted_by_account_id", sa.String(26), nullable=False),
            sa.Column("received_by_account_id", sa.String(26), nullable=True),
            sa.Column("supersedes_id", sa.String(26), nullable=True),
            sa.Column("amendment_reason", sa.Text(), nullable=True),
            sa.Column("status", sa.String(24), nullable=False, server_default="SUBMITTED"),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("handover_request_id", name="uq_core_emergency_handover_request"),
            sa.CheckConstraint("status IN ('SUBMITTED','ACKNOWLEDGED','AMENDED','CANCELLED')", name="ck_core_emergency_handover_status"),
            sa.CheckConstraint("version > 0", name="ck_core_emergency_handover_version"),
        )

    if not _table_exists("core_emergency_epcr"):
        op.create_table(
            "core_emergency_epcr",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("epcr_id", sa.String(64), nullable=False),
            sa.Column("incident_id", sa.String(26), nullable=False),
            sa.Column("patient_person_id", sa.String(26), nullable=True),
            sa.Column("temporary_subject_id", sa.String(26), nullable=True),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("status", sa.String(24), nullable=False, server_default="DRAFT"),
            sa.Column("chief_complaint", sa.Text(), nullable=False),
            sa.Column("narrative", sa.Text(), nullable=False),
            sa.Column("interventions", sa.JSON(), nullable=False),
            sa.Column("destination_facility_reference", sa.String(120), nullable=True),
            sa.Column("signature_evidence", sa.JSON(), nullable=True),
            sa.Column("authored_by_account_id", sa.String(26), nullable=False),
            sa.Column("signed_by_account_id", sa.String(26), nullable=True),
            sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("supersedes_id", sa.String(26), nullable=True),
            sa.Column("amendment_reason", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("epcr_id", "version", name="uq_core_emergency_epcr_version"),
            sa.CheckConstraint("status IN ('DRAFT','SIGNED','AMENDED')", name="ck_core_emergency_epcr_status"),
            sa.CheckConstraint("version > 0", name="ck_core_emergency_epcr_version"),
        )

    if not _table_exists("core_emergency_outbox"):
        op.create_table(
            "core_emergency_outbox",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("event_key", sa.String(160), nullable=False),
            sa.Column("event_type", sa.String(100), nullable=False),
            sa.Column("aggregate_type", sa.String(80), nullable=False),
            sa.Column("aggregate_id", sa.String(26), nullable=False),
            sa.Column("payload", sa.JSON(), nullable=False),
            sa.Column("delivery_mode", sa.String(32), nullable=False, server_default="SYNTHETIC_INTENT"),
            sa.Column("status", sa.String(24), nullable=False, server_default="PENDING"),
            sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("last_error", sa.Text(), nullable=True),
            sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("event_key", name="uq_core_emergency_outbox_event"),
            sa.CheckConstraint("delivery_mode = 'SYNTHETIC_INTENT'", name="ck_core_emergency_outbox_synthetic_only"),
            sa.CheckConstraint("status IN ('PENDING','CLAIMED','DELIVERED','FAILED')", name="ck_core_emergency_outbox_status"),
            sa.CheckConstraint("attempt_count >= 0", name="ck_core_emergency_outbox_attempts"),
        )

    if not _table_exists("niam_health_identity_operations"):
        op.create_table(
            "niam_health_identity_operations",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("operation_id", sa.String(100), nullable=False),
            sa.Column("account_id", sa.String(26), sa.ForeignKey("niam_accounts.id", ondelete="CASCADE"), nullable=False),
            sa.Column("identity_id", sa.String(26), sa.ForeignKey("niam_identities.id", ondelete="CASCADE"), nullable=False),
            sa.Column("person_id", sa.String(26), sa.ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False),
            sa.Column("operation_type", sa.String(40), nullable=False),
            sa.Column("status", sa.String(24), nullable=False, server_default="PENDING"),
            sa.Column("method", sa.String(32), nullable=False),
            sa.Column("provider", sa.String(80), nullable=False, server_default="SYNTHETIC_ADAPTER"),
            sa.Column("assurance_level", sa.String(16), nullable=False, server_default="L0"),
            sa.Column("provider_reference", sa.String(160), nullable=True),
            sa.Column("evidence_digest", sa.String(128), nullable=True),
            sa.Column("verified_attributes", sa.JSON(), nullable=True),
            sa.Column("purpose", sa.String(160), nullable=False),
            sa.Column("reason", sa.Text(), nullable=True),
            sa.Column("source", sa.String(32), nullable=False, server_default="SYNTHETIC"),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("operation_id", name="uq_niam_health_operation_id"),
            sa.CheckConstraint("operation_type IN ('VERIFICATION','HEALTH_ID_ISSUANCE','RECOVERY','CONSENT_GRANT','CONSENT_REVOKE','DEVICE_TRUST')", name="ck_niam_health_operation_type"),
            sa.CheckConstraint("status IN ('PENDING','VERIFIED','COMPLETED','FAILED','REJECTED','REVOKED')", name="ck_niam_health_operation_status"),
            sa.CheckConstraint("method IN ('SYNTHETIC','OTP','OCR','NFC','LIVENESS','GOVERNMENT')", name="ck_niam_health_operation_method"),
            sa.CheckConstraint("assurance_level IN ('L0','L1','L2','L3')", name="ck_niam_health_operation_assurance"),
            sa.CheckConstraint("source = 'SYNTHETIC'", name="ck_niam_health_operation_synthetic_source"),
            sa.CheckConstraint("version > 0", name="ck_niam_health_operation_version"),
        )

    _add_session_column(sa.Column("refresh_family_id", sa.String(64), nullable=True))
    _add_session_column(sa.Column("parent_refresh_token_jti", sa.String(128), nullable=True))
    _add_session_column(sa.Column("refresh_reuse_detected_at", sa.DateTime(timezone=True), nullable=True))
    _add_session_column(sa.Column("device_trust_required", sa.Boolean(), nullable=False, server_default=sa.text("false")))

    for name, table, columns in (
        ("ix_core_emergency_temp_scope", "core_emergency_temporary_subjects", ["organization_id", "facility_id", "workspace_id", "status"]),
        ("ix_core_emergency_incident_scope_status", "core_emergency_incidents", ["organization_id", "facility_id", "workspace_id", "status", "reported_at"]),
        ("ix_core_emergency_incident_patient_time", "core_emergency_incidents", ["patient_person_id", "reported_at"]),
        ("ix_core_emergency_dispatch_incident_status", "core_emergency_dispatches", ["incident_id", "status"]),
        ("ix_core_emergency_triage_incident_time", "core_emergency_triage_assessments", ["incident_id", "assessed_at"]),
        ("ix_core_emergency_prealert_incident_status", "core_emergency_prealerts", ["incident_id", "status"]),
        ("ix_core_emergency_handover_incident_status", "core_emergency_handovers", ["incident_id", "status"]),
        ("ix_core_emergency_handover_supersedes", "core_emergency_handovers", ["supersedes_id"]),
        ("ix_core_emergency_epcr_incident_status", "core_emergency_epcr", ["incident_id", "status"]),
        ("ix_core_emergency_outbox_status_retry", "core_emergency_outbox", ["status", "next_attempt_at"]),
        ("ix_niam_health_operation_account_status", "niam_health_identity_operations", ["account_id", "status", "created_at"]),
        ("ix_niam_sessions_refresh_family", "niam_sessions", ["refresh_family_id", "is_active"]),
    ):
        _index(name, table, columns)

    permissions = (
        ("p16-hospital-01", "clinical.hospital.bed.manage", "Manage hospital wards rooms and beds", "إدارة أجنحة وغرف وأسرة المستشفى", "hospital_bed", "manage"),
        ("p16-hospital-02", "clinical.hospital.care_team.write", "Manage hospital care-team membership", "إدارة عضوية فريق رعاية المستشفى", "hospital_care_team", "write"),
        ("p16-emergency-01", "clinical.emergency.subject.write", "Create temporary emergency subject", "إنشاء هوية طوارئ مؤقتة", "emergency", "subject.write"),
        ("p16-emergency-02", "clinical.emergency.incident.write", "Manage emergency incident", "إدارة حادثة طوارئ", "emergency", "incident.write"),
        ("p16-emergency-03", "clinical.emergency.triage.write", "Record emergency triage", "تسجيل فرز الطوارئ", "emergency", "triage.write"),
        ("p16-emergency-04", "clinical.emergency.dispatch.write", "Manage EMS dispatch", "إدارة إرسال الإسعاف", "emergency", "dispatch.write"),
        ("p16-emergency-05", "clinical.emergency.treatment.write", "Record prehospital treatment", "تسجيل علاج ما قبل المستشفى", "emergency", "treatment.write"),
        ("p16-emergency-06", "clinical.emergency.prealert.write", "Send synthetic emergency pre-alert", "إرسال تنبيه طوارئ اصطناعي", "emergency", "prealert.write"),
        ("p16-emergency-07", "clinical.emergency.handover.write", "Manage emergency handover", "إدارة تسليم الطوارئ", "emergency", "handover.write"),
        ("p16-emergency-08", "clinical.emergency.epcr.write", "Write emergency care report", "كتابة تقرير الرعاية الإسعافية", "emergency", "epcr.write"),
        ("p16-emergency-09", "clinical.emergency.epcr.sign", "Sign emergency care report", "توقيع تقرير الرعاية الإسعافية", "emergency", "epcr.sign"),
        ("p16-identity-01", "identity.health.status.read", "Read own synthetic health identity status", "قراءة حالة الهوية الصحية الاصطناعية", "identity", "health.status.read"),
        ("p16-identity-02", "identity.verification.request", "Request identity verification", "طلب التحقق من الهوية", "identity", "verification.request"),
        ("p16-identity-03", "identity.verification.complete", "Complete identity verification", "إكمال التحقق من الهوية", "identity", "verification.complete"),
        ("p16-identity-04", "identity.health_id.issue", "Issue synthetic Health ID", "إصدار معرف صحي اصطناعي", "identity", "health_id.issue"),
        ("p16-identity-05", "identity.device.register", "Register identity device", "تسجيل جهاز الهوية", "identity", "device.register"),
        ("p16-identity-06", "identity.device.trust", "Trust identity device", "توثيق جهاز الهوية", "identity", "device.trust"),
        ("p16-identity-07", "identity.consent.grant", "Grant bounded consent", "منح موافقة محددة", "identity", "consent.grant"),
        ("p16-identity-08", "identity.consent.revoke", "Revoke consent", "سحب الموافقة", "identity", "consent.revoke"),
        ("p16-identity-09", "identity.recovery.request", "Request account recovery", "طلب استرداد الحساب", "identity", "recovery.request"),
        ("p16-identity-10", "identity.recovery.complete", "Complete account recovery", "إكمال استرداد الحساب", "identity", "recovery.complete"),
    )
    for index, row in enumerate(permissions):
        exists = op.get_bind().execute(sa.text("SELECT 1 FROM niam_permissions WHERE permission_key = :permission_key"), {"permission_key": row[1]}).scalar()
        if not exists:
            op.get_bind().execute(
                sa.text("INSERT INTO niam_permissions (id, uuid, permission_key, name, name_ar, description, resource, action, sensitivity, status, version, created_at, updated_at) VALUES (:id, :uuid, :permission_key, :name, :name_ar, :description, :resource, :action, 'high', 'active', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"),
                {"id": row[0], "uuid": f"p16-health-{index:02d}", "permission_key": row[1], "name": row[2], "name_ar": row[3], "description": row[2], "resource": row[4], "action": row[5]},
            )


def downgrade() -> None:
    if _column_exists("core_emergency_handovers", "amendment_reason"):
        op.drop_column("core_emergency_handovers", "amendment_reason")
    if _column_exists("core_emergency_handovers", "supersedes_id"):
        op.drop_column("core_emergency_handovers", "supersedes_id")
    for column in ("device_trust_required", "refresh_reuse_detected_at", "parent_refresh_token_jti", "refresh_family_id"):
        if _column_exists("niam_sessions", column):
            op.drop_column("niam_sessions", column)
    for table in (
        "niam_health_identity_operations",
        "core_emergency_outbox",
        "core_emergency_epcr",
        "core_emergency_handovers",
        "core_emergency_prealerts",
        "core_emergency_treatments",
        "core_emergency_triage_assessments",
        "core_emergency_dispatches",
        "core_emergency_incidents",
        "core_emergency_temporary_subjects",
    ):
        if _table_exists(table):
            op.drop_table(table)
