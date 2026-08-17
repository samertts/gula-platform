"""sync conflict locks and realtime clinical notifications

Revision ID: 20260817_0025
Revises: 20260817_0024
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260817_0025"
down_revision = "20260817_0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "national_sync_operations",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("operation_id", sa.String(length=64), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("device_id", sa.String(length=128), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("hospital_id", sa.Integer(), nullable=True),
        sa.Column("client_sequence", sa.Integer(), nullable=True),
        sa.Column("operation_type", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=128), nullable=True),
        sa.Column("base_version", sa.Integer(), nullable=True),
        sa.Column("priority", sa.String(length=16), nullable=False, server_default="routine"),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("payload_hash", sa.String(length=128), nullable=False),
        sa.Column("signature", sa.String(length=256), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_code", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("operation_id", name="uq_sync_operation_id"),
        sa.UniqueConstraint("lab_id", "device_id", "idempotency_key", name="uq_sync_scope_idempotency"),
    )
    op.create_index("ix_sync_operation_device", "national_sync_operations", ["device_id"])
    op.create_index("ix_sync_operation_lab", "national_sync_operations", ["lab_id"])
    op.create_index("ix_sync_operation_hospital", "national_sync_operations", ["hospital_id"])
    op.create_index("ix_sync_operation_entity", "national_sync_operations", ["entity_type", "entity_id"])
    op.create_index("ix_sync_operation_status", "national_sync_operations", ["status"])
    op.create_index("ix_sync_queue_priority_created", "national_sync_operations", ["lab_id", "hospital_id", "status", "priority", "created_at"])

    op.create_table(
        "national_sync_conflicts",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("operation_id", sa.String(length=64), nullable=False),
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("hospital_id", sa.Integer(), nullable=True),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=128), nullable=True),
        sa.Column("conflict_type", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False, server_default="P2_HIGH"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("base_version", sa.Integer(), nullable=True),
        sa.Column("server_version", sa.Integer(), nullable=True),
        sa.Column("local_payload", sa.JSON(), nullable=False),
        sa.Column("server_snapshot", sa.JSON(), nullable=True),
        sa.Column("resolution", sa.String(length=64), nullable=True),
        sa.Column("resolution_reason", sa.Text(), nullable=True),
        sa.Column("resolved_by", sa.String(length=64), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_sync_conflict_lab_status", "national_sync_conflicts", ["lab_id", "hospital_id", "status", "severity", "created_at"])
    op.create_index("ix_sync_conflict_entity", "national_sync_conflicts", ["entity_id"])

    op.create_table(
        "national_record_locks",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("resource_type", sa.String(length=64), nullable=False),
        sa.Column("resource_id", sa.String(length=128), nullable=False),
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("hospital_id", sa.Integer(), nullable=True),
        sa.Column("owner_user_id", sa.String(length=64), nullable=False),
        sa.Column("owner_device_id", sa.String(length=128), nullable=False),
        sa.Column("lock_token_hash", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="active"),
        sa.Column("acquired_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("lock_token_hash", name="uq_record_lock_token_hash"),
    )
    op.create_index("ix_record_lock_resource", "national_record_locks", ["resource_type", "resource_id", "lab_id", "status"])
    op.create_index("ix_record_lock_expiry", "national_record_locks", ["expires_at"])

    op.create_table(
        "national_sync_outbox",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=96), nullable=False),
        sa.Column("aggregate_type", sa.String(length=64), nullable=False),
        sa.Column("aggregate_id", sa.String(length=128), nullable=False),
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("hospital_id", sa.Integer(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("event_id", name="uq_sync_outbox_event_id"),
    )
    op.create_index("ix_sync_outbox_pending", "national_sync_outbox", ["status", "next_attempt_at"])

    op.create_table(
        "national_clinical_notifications",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("conflict_id", sa.String(length=26), nullable=False),
        sa.Column("recipient_user_id", sa.String(length=64), nullable=False),
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("hospital_id", sa.Integer(), nullable=True),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=False),
        sa.Column("resource_id", sa.String(length=128), nullable=True),
        sa.Column("dedupe_key", sa.String(length=256), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="delivered"),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_by", sa.String(length=64), nullable=True),
        sa.Column("escalated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("escalated_to", sa.String(length=64), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("dedupe_key", name="uq_clinical_notification_dedupe"),
    )
    op.create_index("ix_clinical_notification_inbox", "national_clinical_notifications", ["recipient_user_id", "status", "severity", "created_at"])

    op.create_table(
        "national_device_sessions",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("device_id", sa.String(length=128), nullable=False),
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("hospital_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("policy_version", sa.String(length=64), nullable=False, server_default="offline-emergency-1"),
        sa.Column("allowed_operation_types", sa.JSON(), nullable=False),
        sa.Column("session_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("device_id", name="uq_device_session_device"),
    )
    op.create_index("ix_device_session_scope", "national_device_sessions", ["lab_id", "hospital_id", "revoked", "expires_at"])


def downgrade() -> None:
    op.drop_table("national_device_sessions")
    op.drop_table("national_clinical_notifications")
    op.drop_table("national_sync_outbox")
    op.drop_table("national_record_locks")
    op.drop_table("national_sync_conflicts")
    op.drop_table("national_sync_operations")
