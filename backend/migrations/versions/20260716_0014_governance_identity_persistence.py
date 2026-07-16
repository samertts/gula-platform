"""Create governance identity persistence tables.

Revision ID: 20260716_0014
Revises: 20260716_0013
Create Date: 2026-07-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import inspect

revision: str = "20260716_0014"
down_revision: Union[str, None] = "20260716_0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def upgrade() -> None:
    # ── Identity Records ──
    if not _table_exists("gov_identity_records"):
        op.create_table(
            "gov_identity_records",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("health_number", sa.String(50), nullable=False, index=True),
            sa.Column("national_id_hash", sa.String(255), nullable=True, index=True),
            sa.Column("full_name", sa.String(300), nullable=False),
            sa.Column("date_of_birth", sa.DateTime(timezone=True), nullable=True),
            sa.Column("gender", sa.String(20), nullable=True),
            sa.Column("phone", sa.String(50), nullable=True),
            sa.Column("email", sa.String(200), nullable=True),
            sa.Column("address", sa.Text, nullable=True),
            sa.Column("identity_type", sa.String(30), nullable=False, default="citizen", index=True),
            sa.Column("identity_status", sa.String(20), nullable=False, default="active"),
            sa.Column("documents_json", JSON, nullable=True),
            sa.Column("relationships_json", JSON, nullable=True),
            sa.Column("history_json", JSON, nullable=True),
            sa.Column("metadata_json", JSON, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_gov_identity_health_number", "gov_identity_records", ["health_number"], unique=True)

    # ── Break Glass Accesses ──
    if not _table_exists("gov_break_glass_accesses"):
        op.create_table(
            "gov_break_glass_accesses",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("user_id", sa.String(100), nullable=False, index=True),
            sa.Column("user_name", sa.String(200), nullable=True),
            sa.Column("user_role", sa.String(50), nullable=True),
            sa.Column("reason", sa.String(50), nullable=False),
            sa.Column("reason_detail", sa.Text, nullable=True),
            sa.Column("resource_type", sa.String(50), nullable=True),
            sa.Column("resource_id", sa.String(100), nullable=True),
            sa.Column("patient_id", sa.String(36), nullable=True, index=True),
            sa.Column("accessed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_active", sa.Boolean, default=True, index=True),
            sa.Column("reviewed_by", sa.String(100), nullable=True),
            sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("review_notes", sa.Text, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_gov_break_glass_user", "gov_break_glass_accesses", ["user_id"])
        op.create_index("ix_gov_break_glass_active", "gov_break_glass_accesses", ["is_active"])

    # ── Merge Proposals ──
    if not _table_exists("gov_merge_proposals"):
        op.create_table(
            "gov_merge_proposals",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("proposal_key", sa.String(200), nullable=False, index=True),
            sa.Column("primary_hn", sa.String(50), nullable=False, index=True),
            sa.Column("duplicate_hn", sa.String(50), nullable=False, index=True),
            sa.Column("confidence_score", sa.Float, nullable=False, default=0.0),
            sa.Column("matched_fields", JSON, nullable=True),
            sa.Column("status", sa.String(20), nullable=False, default="pending", index=True),
            sa.Column("reviewed_by", sa.String(100), nullable=True),
            sa.Column("notes", sa.Text, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_gov_merge_proposal_key", "gov_merge_proposals", ["proposal_key"], unique=True)
        op.create_index("ix_gov_merge_status", "gov_merge_proposals", ["status"])

    # ── QR Codes ──
    if not _table_exists("gov_qr_codes"):
        op.create_table(
            "gov_qr_codes",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("citizen_id", sa.String(36), nullable=False, index=True),
            sa.Column("token", sa.String(255), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_active", sa.Boolean, default=True, index=True),
            sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("version", sa.Integer, default=1, nullable=False),
        )

    # ── Recovery Requests ──
    if not _table_exists("gov_recovery_requests"):
        op.create_table(
            "gov_recovery_requests",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("citizen_id", sa.String(36), nullable=False, index=True),
            sa.Column("method", sa.String(50), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, default="pending", index=True),
            sa.Column("verification_token", sa.String(255), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("version", sa.Integer, default=1, nullable=False),
        )

    # ── Guardians ──
    if not _table_exists("gov_guardians"):
        op.create_table(
            "gov_guardians",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("citizen_id", sa.String(36), nullable=False, index=True),
            sa.Column("guardian_id", sa.String(36), nullable=False, index=True),
            sa.Column("guardian_type", sa.String(50), nullable=False, default="legal_guardian"),
            sa.Column("relationship", sa.String(100), nullable=True),
            sa.Column("is_active", sa.Boolean, default=True, index=True),
            sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("version", sa.Integer, default=1, nullable=False),
        )


def downgrade() -> None:
    op.drop_table("gov_guardians")
    op.drop_table("gov_recovery_requests")
    op.drop_table("gov_qr_codes")
    op.drop_table("gov_merge_proposals")
    op.drop_table("gov_break_glass_accesses")
    op.drop_table("gov_identity_records")
