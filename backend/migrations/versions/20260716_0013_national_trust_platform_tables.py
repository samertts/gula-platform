"""Create National Trust Platform tables.

Revision ID: 20260716_0013
Revises: 20260716_0012
Create Date: 2026-07-16
"""

from typing import Sequence, Union
import sqlalchemy as sa
from alembic import context, op
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import inspect

revision: str = "20260716_0013"
down_revision: Union[str, None] = "20260716_0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table: str) -> bool:
    if context.is_offline_mode():
        return True
    return inspect(op.get_bind()).has_table(table)


def upgrade() -> None:
    # ── Consent Records ──
    if not _table_exists("trust_consent_records"):
        op.create_table(
            "trust_consent_records",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), nullable=False, index=True),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id"), nullable=False, index=True),
            sa.Column("purpose", sa.String(50), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
            sa.Column("granted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("data_categories", sa.String(500), nullable=True),
            sa.Column("guardian_id", sa.Integer(), sa.ForeignKey("lab_users.id"), nullable=True),
            sa.Column("consent_hash", sa.String(128), nullable=False),
            sa.Column("consent_version", sa.String(20), nullable=False, server_default="1.0"),
            sa.Column("ip_address", sa.String(45), nullable=True),
            sa.Column("user_agent", sa.String(500), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("is_deleted", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_trust_consent_patient_purpose", "trust_consent_records", ["patient_id", "purpose"])

    # ── Data Retention Policies ──
    if not _table_exists("trust_retention_policies"):
        op.create_table(
            "trust_retention_policies",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("data_category", sa.String(50), nullable=False, unique=True),
            sa.Column("retention_period", sa.String(50), nullable=False),
            sa.Column("retention_days", sa.Integer(), nullable=False),
            sa.Column("action_on_expiry", sa.String(100), nullable=False, server_default="anonymize"),
            sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("policy_version", sa.String(20), nullable=False, server_default="1.0"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("is_deleted", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )

    # ── Sovereignty Rules ──
    if not _table_exists("trust_sovereignty_rules"):
        op.create_table(
            "trust_sovereignty_rules",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("data_category", sa.String(50), nullable=False, unique=True),
            sa.Column("sovereignty_level", sa.String(50), nullable=False, server_default="national_only"),
            sa.Column("allows_cross_border", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("requires_encryption", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("requires_consent", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("encryption_algorithm", sa.String(100), nullable=False, server_default="AES-256-GCM"),
            sa.Column("key_ownership", sa.String(100), nullable=False, server_default="national"),
            sa.Column("data_residency", sa.String(200), nullable=False, server_default="IRQ"),
            sa.Column("rule_version", sa.String(20), nullable=False, server_default="1.0"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("is_deleted", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )

    # ── Trust Service Logs ──
    if not _table_exists("trust_service_logs"):
        op.create_table(
            "trust_service_logs",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("service_type", sa.String(50), nullable=False),
            sa.Column("request_id", sa.String(64), nullable=False, index=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("lab_users.id"), nullable=True),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id"), nullable=True),
            sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), nullable=True),
            sa.Column("document_hash", sa.String(128), nullable=True, index=True),
            sa.Column("signature_value", sa.Text(), nullable=True),
            sa.Column("certificate_serial", sa.String(128), nullable=True),
            sa.Column("timestamp_token", sa.Text(), nullable=True),
            sa.Column("status", sa.String(50), nullable=False, server_default="completed"),
            sa.Column("result_hash", sa.String(128), nullable=True),
            sa.Column("metadata_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("is_deleted", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )

    # ── Compliance Evidence ──
    if not _table_exists("trust_compliance_evidence"):
        op.create_table(
            "trust_compliance_evidence",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("evidence_type", sa.String(100), nullable=False),
            sa.Column("evidence_id", sa.String(128), nullable=False, unique=True),
            sa.Column("source", sa.String(200), nullable=False),
            sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("collected_by", sa.Integer(), sa.ForeignKey("lab_users.id"), nullable=True),
            sa.Column("status", sa.String(50), nullable=False, server_default="pending_review"),
            sa.Column("evidence_hash", sa.String(128), nullable=False),
            sa.Column("evidence_data", sa.Text(), nullable=True),
            sa.Column("retention_until", sa.DateTime(timezone=True), nullable=True),
            sa.Column("chain_of_custody", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("is_deleted", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_trust_evidence_type", "trust_compliance_evidence", ["evidence_type"])

    # ── Compliance Checks ──
    if not _table_exists("trust_compliance_checks"):
        op.create_table(
            "trust_compliance_checks",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("check_type", sa.String(100), nullable=False),
            sa.Column("check_name", sa.String(200), nullable=False),
            sa.Column("target_id", sa.String(128), nullable=True),
            sa.Column("target_type", sa.String(50), nullable=True),
            sa.Column("result", sa.String(50), nullable=False),
            sa.Column("score", sa.Integer(), nullable=True),
            sa.Column("details", sa.Text(), nullable=True),
            sa.Column("checked_by", sa.Integer(), sa.ForeignKey("lab_users.id"), nullable=True),
            sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("next_check_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("corrective_action_id", sa.String(128), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("is_deleted", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_trust_compliance_check_type", "trust_compliance_checks", ["check_type"])


def downgrade() -> None:
    op.drop_table("trust_compliance_checks")
    op.drop_table("trust_compliance_evidence")
    op.drop_table("trust_service_logs")
    op.drop_table("trust_sovereignty_rules")
    op.drop_table("trust_retention_policies")
    op.drop_table("trust_consent_records")
