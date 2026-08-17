"""EHR auto-sync connector state and synchronization records.

Prepared locally; not executed by this change set.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260816_0029"
down_revision = "20260816_0028"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    return bool(sa.inspect(op.get_bind()).has_table(name))


def upgrade() -> None:
    if not _has_table("ehr_connector_configs"):
        op.create_table(
            "ehr_connector_configs",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("connector_name", sa.String(80), nullable=False, server_default="ehr"),
            sa.Column("protocol", sa.String(20), nullable=False, server_default="fhir_r4"),
            sa.Column("endpoint", sa.String(500), nullable=False),
            sa.Column("contract_version", sa.String(80), nullable=False),
            sa.Column("trust_material_ref", sa.String(200), nullable=True),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("approved_by", sa.String(160), nullable=True),
            sa.Column("last_health_status", sa.String(30), nullable=False, server_default="unverified"),
            sa.Column("last_health_checked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_error", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("lab_id", "connector_name", name="uq_ehr_connector_lab_name"),
        )
    if not _has_table("ehr_sync_records"):
        op.create_table(
            "ehr_sync_records",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("event_type", sa.String(120), nullable=False),
            sa.Column("entity_type", sa.String(80), nullable=False),
            sa.Column("entity_id", sa.String(160), nullable=False),
            sa.Column("idempotency_key", sa.String(200), nullable=False),
            sa.Column("status", sa.String(30), nullable=False, server_default="queued"),
            sa.Column("outbox_event_id", sa.Integer(), nullable=True),
            sa.Column("external_id", sa.String(200), nullable=True),
            sa.Column("rejection_reason", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("lab_id", "idempotency_key", name="uq_ehr_sync_lab_idempotency"),
        )


def downgrade() -> None:
    # Intentionally conservative: data-bearing integration history is not removed automatically.
    return
