"""Doctor Duty Context and shift-bound clinical access.

This migration is additive and fail-closed. It is prepared for controlled staging
execution; it does not execute against production as part of this change.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import context, op

revision = "20260818_0033"
down_revision = "20260817_0032"
branch_labels = None
depends_on = None


def _create_tables() -> None:
    op.create_table(
        "doctor_duties",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("facility_id", sa.Integer(), sa.ForeignKey("facilities.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("department_id", sa.String(100), nullable=True), sa.Column("ward_id", sa.String(100), nullable=True),
        sa.Column("room_id", sa.String(100), nullable=True), sa.Column("role_id", sa.String(100), nullable=False),
        sa.Column("purpose", sa.String(100), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False), sa.Column("expected_end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actual_started_at", sa.DateTime(timezone=True), nullable=True), sa.Column("actual_ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="SCHEDULED"), sa.Column("assigned_patient_ids", sa.JSON(), nullable=True), sa.Column("scope", sa.JSON(), nullable=True),
        sa.Column("assigned_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True), sa.Column("revoked_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("revocation_reason", sa.Text(), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False), sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.CheckConstraint("status IN ('SCHEDULED','CHECKED_IN','ACTIVE','PAUSED','HANDOVER_PENDING','HANDOVER_COMPLETED','ENDED','CANCELLED','REVOKED')", name="ck_doctor_duty_status"),
        sa.CheckConstraint("expected_end_at > starts_at", name="ck_doctor_duty_time_order"),
    )
    op.create_index("ix_doctor_duties_tenant_id", "doctor_duties", ["tenant_id"])
    op.create_index("ix_doctor_duties_user_status_time", "doctor_duties", ["user_id", "status", "starts_at", "expected_end_at"])
    op.create_index("ix_doctor_duties_organization_id", "doctor_duties", ["organization_id"])
    op.create_index("ix_doctor_duties_facility_id", "doctor_duties", ["facility_id"])
    op.create_index("ix_doctor_duties_department_id", "doctor_duties", ["department_id"])
    op.create_index("ix_doctor_duties_ward_id", "doctor_duties", ["ward_id"])

    op.create_table(
        "duty_contexts",
        sa.Column("id", sa.String(64), primary_key=True), sa.Column("duty_id", sa.Integer(), sa.ForeignKey("doctor_duties.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("tenant_id", sa.Integer(), nullable=True), sa.Column("organization_id", sa.Integer(), nullable=False), sa.Column("facility_id", sa.Integer(), nullable=False),
        sa.Column("department_id", sa.String(100), nullable=True), sa.Column("ward_id", sa.String(100), nullable=True), sa.Column("role_id", sa.String(100), nullable=False), sa.Column("purpose", sa.String(100), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="ACTIVE"), sa.Column("started_at", sa.DateTime(timezone=True), nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("authz_version", sa.Integer(), nullable=False, server_default="1"), sa.Column("assigned_patient_ids", sa.JSON(), nullable=True), sa.Column("permissions", sa.JSON(), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_duty_contexts_user_active", "duty_contexts", ["user_id", "status", "expires_at"])
    op.create_index("ix_duty_contexts_scope", "duty_contexts", ["organization_id", "facility_id", "department_id", "ward_id"])

    op.create_table(
        "shift_contexts",
        sa.Column("id", sa.String(64), primary_key=True), sa.Column("duty_context_id", sa.String(64), sa.ForeignKey("duty_contexts.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("shift_start", sa.DateTime(timezone=True), nullable=False), sa.Column("shift_expected_end", sa.DateTime(timezone=True), nullable=False), sa.Column("timezone", sa.String(64), nullable=False, server_default="UTC"),
        sa.Column("server_started_at", sa.DateTime(timezone=True), nullable=False), sa.Column("server_ended_at", sa.DateTime(timezone=True), nullable=True), sa.Column("status", sa.String(30), nullable=False, server_default="ACTIVE"),
    )

    op.create_table(
        "clinical_access_contexts",
        sa.Column("id", sa.String(64), primary_key=True), sa.Column("duty_context_id", sa.String(64), sa.ForeignKey("duty_contexts.id", ondelete="CASCADE"), nullable=False, unique=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False), sa.Column("facility_id", sa.Integer(), nullable=False), sa.Column("department_id", sa.String(100), nullable=True), sa.Column("ward_id", sa.String(100), nullable=True), sa.Column("scope_type", sa.String(30), nullable=False, server_default="ASSIGNED_LOCATION"),
        sa.Column("allowed_resources", sa.JSON(), nullable=False), sa.Column("patient_scope", sa.JSON(), nullable=False), sa.Column("purpose", sa.String(100), nullable=False), sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True), sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_index("ix_clinical_access_contexts_user_id", "clinical_access_contexts", ["user_id"])
    op.create_index("ix_clinical_access_contexts_organization_id", "clinical_access_contexts", ["organization_id"])
    op.create_index("ix_clinical_access_contexts_facility_id", "clinical_access_contexts", ["facility_id"])
    op.create_index("ix_clinical_access_contexts_active", "clinical_access_contexts", ["active"])
    op.create_index("ix_clinical_access_contexts_expires_at", "clinical_access_contexts", ["expires_at"])

    op.create_table(
        "duty_handovers",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("outgoing_duty_id", sa.Integer(), sa.ForeignKey("doctor_duties.id", ondelete="RESTRICT"), nullable=False), sa.Column("incoming_duty_id", sa.Integer(), sa.ForeignKey("doctor_duties.id", ondelete="RESTRICT"), nullable=False), sa.Column("outgoing_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False), sa.Column("incoming_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False), sa.Column("patient_ids", sa.JSON(), nullable=False), sa.Column("task_ids", sa.JSON(), nullable=False), sa.Column("status", sa.String(30), nullable=False, server_default="PENDING"), sa.Column("started_at", sa.DateTime(timezone=True), nullable=False), sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True), sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True), sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_duty_handovers_outgoing_duty_id", "duty_handovers", ["outgoing_duty_id"])
    op.create_index("ix_duty_handovers_incoming_duty_id", "duty_handovers", ["incoming_duty_id"])

    op.create_table(
        "duty_audit_events",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("event_type", sa.String(60), nullable=False), sa.Column("actor_id", sa.Integer(), nullable=True), sa.Column("duty_context_id", sa.String(64), nullable=True), sa.Column("organization_id", sa.Integer(), nullable=True), sa.Column("facility_id", sa.Integer(), nullable=True), sa.Column("location", sa.JSON(), nullable=True), sa.Column("resource_type", sa.String(80), nullable=True), sa.Column("resource_id", sa.String(120), nullable=True), sa.Column("patient_id", sa.Integer(), nullable=True), sa.Column("purpose", sa.String(100), nullable=True), sa.Column("decision", sa.String(20), nullable=False), sa.Column("request_id", sa.String(120), nullable=True), sa.Column("correlation_id", sa.String(120), nullable=True), sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False), sa.Column("metadata_json", sa.JSON(), nullable=True),
    )
    op.create_index("ix_duty_audit_events_event_type", "duty_audit_events", ["event_type"])
    op.create_index("ix_duty_audit_events_actor_id", "duty_audit_events", ["actor_id"])
    op.create_index("ix_duty_audit_events_duty_context_id", "duty_audit_events", ["duty_context_id"])
    op.create_index("ix_duty_audit_events_patient_id", "duty_audit_events", ["patient_id"])
    op.create_index("ix_duty_audit_events_occurred_at", "duty_audit_events", ["occurred_at"])

    op.create_table(
        "duty_break_glass",
        sa.Column("id", sa.String(64), primary_key=True), sa.Column("duty_context_id", sa.String(64), sa.ForeignKey("duty_contexts.id", ondelete="CASCADE"), nullable=False), sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False), sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="SET NULL"), nullable=True), sa.Column("reason", sa.Text(), nullable=False), sa.Column("scope", sa.JSON(), nullable=False), sa.Column("started_at", sa.DateTime(timezone=True), nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True), sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
    )
    op.create_index("ix_duty_break_glass_duty_context_id", "duty_break_glass", ["duty_context_id"])


def upgrade() -> None:
    # Offline SQL is intentionally deterministic. Online execution checks table presence.
    if context.is_offline_mode():
        _create_tables()
        return
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("doctor_duties"):
        _create_tables()


def downgrade() -> None:
    # Destructive rollback is deliberately blocked outside an explicit offline review.
    if context.is_offline_mode():
        for table in ("duty_break_glass", "duty_audit_events", "duty_handovers", "clinical_access_contexts", "shift_contexts", "duty_contexts", "doctor_duties"):
            op.drop_table(table)
        return
    raise RuntimeError("Doctor Duty tables are retained by policy; use an approved offline rollback plan.")
