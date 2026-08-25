"""Add isolated external ingestion and professional ER metadata.

Revision ID: 20260825_0009
Revises: 20260820_0008

The migration stores bounded metadata and non-reversible matching features only.
Raw government/professional files remain outside the database in a separately
protected quarantine object store.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20260825_0009"
down_revision = "20260820_0008"
branch_labels = None
depends_on = None


def _table_exists(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def upgrade() -> None:
    if not _table_exists("external_ingestion_sources"):
        op.create_table(
            "external_ingestion_sources",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("source_key", sa.String(80), nullable=False),
            sa.Column("source_kind", sa.String(40), nullable=False),
            sa.Column("display_name", sa.String(200), nullable=False),
            sa.Column("contract_status", sa.String(30), nullable=False, server_default="pending"),
            sa.Column("contract_expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("allowed_fields", sa.JSON(), nullable=False),
            sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("service_account_id", sa.Integer(), sa.ForeignKey("service_accounts.id", ondelete="RESTRICT"), nullable=True),
            sa.Column("vault_reference", sa.String(240), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.UniqueConstraint("source_key", name="uq_external_ingestion_source_key"),
            sa.CheckConstraint(
                "source_kind IN ('professional_registry','ministry_workforce','civil_identity')",
                name="ck_external_ingestion_source_kind",
            ),
            sa.CheckConstraint(
                "contract_status IN ('pending','active','suspended','expired')",
                name="ck_external_ingestion_source_contract_status",
            ),
        )
        op.create_index(
            "ix_external_ingestion_source_active",
            "external_ingestion_sources",
            ["is_enabled", "contract_status"],
        )
        op.create_index(
            "ix_external_ingestion_source_binding",
            "external_ingestion_sources",
            ["service_account_id", "is_enabled"],
        )

    if not _table_exists("external_ingestion_batches"):
        op.create_table(
            "external_ingestion_batches",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("source_id", sa.Integer(), sa.ForeignKey("external_ingestion_sources.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("export_id", sa.String(160), nullable=False),
            sa.Column("idempotency_key", sa.String(240), nullable=False),
            sa.Column("content_sha256", sa.String(64), nullable=False),
            sa.Column("object_uri", sa.String(512), nullable=False),
            sa.Column("schema_version", sa.Integer(), nullable=False),
            sa.Column("declared_record_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("status", sa.String(30), nullable=False, server_default="received"),
            sa.Column("received_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("staged_record_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("rejected_record_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("review_record_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("accepted_record_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("auto_matched_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("manifest", sa.JSON(), nullable=False),
            sa.Column("rejection_reason", sa.Text(), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("committed_by", sa.Integer(), nullable=True),
            sa.Column("committed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.UniqueConstraint("source_id", "idempotency_key", name="uq_external_ingestion_batch_idempotency"),
            sa.UniqueConstraint("source_id", "export_id", "content_sha256", name="uq_external_ingestion_batch_export_digest"),
            sa.CheckConstraint(
                "status IN ('received','staging','review_required','ready_for_approval','rejected','committed','expired')",
                name="ck_external_ingestion_batch_status",
            ),
        )
        op.create_index("ix_external_ingestion_batch_status", "external_ingestion_batches", ["status", "received_at"])
        op.create_index("ix_external_ingestion_batch_source", "external_ingestion_batches", ["source_id", "received_at"])

    if not _table_exists("external_professional_entities"):
        op.create_table(
            "external_professional_entities",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("entity_key_hmac", sa.String(64), nullable=False),
            sa.Column("profession", sa.String(60), nullable=False),
            sa.Column("state", sa.String(30), nullable=False, server_default="provisional"),
            sa.Column("source_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("gula_account_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.UniqueConstraint("entity_key_hmac", name="uq_external_professional_entity_key"),
            sa.CheckConstraint(
                "state IN ('provisional','verified','revoked')",
                name="ck_external_professional_entity_state",
            ),
        )
        op.create_index(
            "ix_external_professional_entity_profession",
            "external_professional_entities",
            ["profession", "state"],
        )

    if not _table_exists("external_professional_records"):
        op.create_table(
            "external_professional_records",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("batch_id", sa.Integer(), sa.ForeignKey("external_ingestion_batches.id", ondelete="CASCADE"), nullable=False),
            sa.Column("source_key", sa.String(80), nullable=False),
            sa.Column("source_record_id_hmac", sa.String(64), nullable=False),
            sa.Column("source_record_version", sa.String(80), nullable=True),
            sa.Column("person_ref_hmac", sa.String(64), nullable=False),
            sa.Column("national_id_hmac", sa.String(64), nullable=True),
            sa.Column("license_hmac", sa.String(64), nullable=True),
            sa.Column("license_authority", sa.String(120), nullable=True),
            sa.Column("profession", sa.String(60), nullable=False),
            sa.Column("specialty_hmac", sa.String(64), nullable=True),
            sa.Column("name_hmac", sa.String(64), nullable=False),
            sa.Column("name_tokens_hmac", sa.JSON(), nullable=False),
            sa.Column("phone_hmac", sa.String(64), nullable=True),
            sa.Column("birth_date_hmac", sa.String(64), nullable=True),
            sa.Column("employer_ref_hmac", sa.String(64), nullable=True),
            sa.Column("employment_status", sa.String(40), nullable=True),
            sa.Column("canonical_entity_id", sa.Integer(), sa.ForeignKey("external_professional_entities.id", ondelete="RESTRICT"), nullable=True),
            sa.Column("resolution_status", sa.String(30), nullable=False, server_default="unresolved"),
            sa.Column("resolution_method", sa.String(40), nullable=True),
            sa.Column("resolution_score", sa.Integer(), nullable=True),
            sa.Column("resolution_features", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.UniqueConstraint("batch_id", "source_record_id_hmac", name="uq_external_professional_record_batch_source_id"),
            sa.CheckConstraint(
                "resolution_status IN ('unresolved','unmatched','pending_review','auto_matched','approved_manual','rejected')",
                name="ck_external_professional_record_resolution_status",
            ),
        )
        op.create_index("ix_external_professional_record_nid", "external_professional_records", ["national_id_hmac"])
        op.create_index("ix_external_professional_record_license", "external_professional_records", ["license_hmac", "profession"])
        op.create_index("ix_external_professional_record_entity", "external_professional_records", ["canonical_entity_id"])
        op.create_index("ix_external_professional_record_resolution", "external_professional_records", ["resolution_status"])

    if not _table_exists("external_professional_match_reviews"):
        op.create_table(
            "external_professional_match_reviews",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("record_id", sa.Integer(), sa.ForeignKey("external_professional_records.id", ondelete="CASCADE"), nullable=False),
            sa.Column("candidate_entity_id", sa.Integer(), sa.ForeignKey("external_professional_entities.id", ondelete="RESTRICT"), nullable=True),
            sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
            sa.Column("reason", sa.Text(), nullable=False),
            sa.Column("evidence", sa.JSON(), nullable=False),
            sa.Column("decided_by", sa.Integer(), nullable=True),
            sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.UniqueConstraint("record_id", name="uq_external_professional_match_review_record"),
            sa.CheckConstraint(
                "status IN ('pending','approved','rejected')",
                name="ck_external_professional_match_review_status",
            ),
        )
        op.create_index(
            "ix_external_professional_match_review_status",
            "external_professional_match_reviews",
            ["status", "created_at"],
        )


def downgrade() -> None:
    if _table_exists("external_professional_match_reviews"):
        op.drop_table("external_professional_match_reviews")
    if _table_exists("external_professional_records"):
        op.drop_table("external_professional_records")
    if _table_exists("external_professional_entities"):
        op.drop_table("external_professional_entities")
    if _table_exists("external_ingestion_batches"):
        op.drop_table("external_ingestion_batches")
    if _table_exists("external_ingestion_sources"):
        op.drop_table("external_ingestion_sources")
