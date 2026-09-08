"""Blood Bank Phase 2 operational lifecycle tables.

Revision ID: 20260901_0001
Revises: 20260814_0006
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260901_0001"
down_revision = "20260814_0006"
branch_labels = None
depends_on = None


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _columns(table: str) -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(table)}


def _add_column(table: str, column: sa.Column) -> None:
    if table in _tables() and column.name not in _columns(table):
        op.add_column(table, column)


def upgrade() -> None:
    tables = _tables()
    common = [
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.String(100)),
    ]
    if "blood_bank_patient_samples" not in tables:
        op.create_table("blood_bank_patient_samples", *common,
            sa.Column("patient_id", sa.String(100), nullable=False),
            sa.Column("encounter_id", sa.String(100)),
            sa.Column("facility_id", sa.String(100), nullable=False),
            sa.Column("specimen_identifier", sa.String(120), nullable=False, unique=True),
            sa.Column("status", sa.String(40), nullable=False, server_default="collected"),
            sa.Column("collected_by", sa.String(100), nullable=False),
            sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("received_at", sa.DateTime(timezone=True)),
            sa.Column("validated_by", sa.String(100)),
            sa.Column("validated_at", sa.DateTime(timezone=True)),
            sa.Column("expires_at", sa.DateTime(timezone=True)),
            sa.Column("rejection_reason", sa.Text()),
        )
    if "blood_bank_reservations" not in tables:
        op.create_table("blood_bank_reservations", *common,
            sa.Column("order_id", sa.String(100), nullable=False),
            sa.Column("patient_id", sa.String(100), nullable=False),
            sa.Column("encounter_id", sa.String(100)),
            sa.Column("unit_id", sa.String(100), nullable=False),
            sa.Column("component_id", sa.String(100)),
            sa.Column("facility_id", sa.String(100), nullable=False),
            sa.Column("requested_by", sa.String(100), nullable=False),
            sa.Column("status", sa.String(40), nullable=False, server_default="reserved"),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("released_at", sa.DateTime(timezone=True)),
            sa.Column("release_reason", sa.Text()),
            sa.UniqueConstraint("lab_id", "unit_id", name="uq_blood_reservation_lab_unit"),
        )
    if "blood_bank_reactions" not in tables:
        op.create_table("blood_bank_reactions", *common,
            sa.Column("patient_id", sa.String(100), nullable=False),
            sa.Column("transfusion_id", sa.String(100), nullable=False),
            sa.Column("unit_id", sa.String(100), nullable=False),
            sa.Column("component_id", sa.String(100)),
            sa.Column("encounter_id", sa.String(100)),
            sa.Column("facility_id", sa.String(100), nullable=False),
            sa.Column("reporter_id", sa.String(100), nullable=False),
            sa.Column("status", sa.String(40), nullable=False, server_default="suspected"),
            sa.Column("severity", sa.String(40)),
            sa.Column("symptoms", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("investigation", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("related_sample_ids", sa.JSON(), nullable=False, server_default="[]"),
            sa.Column("outcome", sa.Text()),
            sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("resolved_at", sa.DateTime(timezone=True)),
        )
    if "blood_bank_traceability_events" not in tables:
        op.create_table("blood_bank_traceability_events", *common,
            sa.Column("unit_id", sa.String(100), nullable=False),
            sa.Column("facility_id", sa.String(100), nullable=False),
            sa.Column("event_type", sa.String(60), nullable=False),
            sa.Column("object_type", sa.String(60), nullable=False),
            sa.Column("object_id", sa.String(100), nullable=False),
            sa.Column("actor_id", sa.String(100), nullable=False),
            sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("reason", sa.Text()),
            sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        )
    _add_column("blood_bank_crossmatches", sa.Column("sample_id", sa.String(100)))
    _add_column("blood_bank_crossmatches", sa.Column("policy_version", sa.String(80)))
    for table, columns in {
        "blood_bank_patient_samples": ["patient_id", "facility_id", "status", "expires_at"],
        "blood_bank_reservations": ["lab_id", "unit_id", "order_id", "status", "expires_at"],
        "blood_bank_reactions": ["lab_id", "unit_id", "transfusion_id", "status"],
        "blood_bank_traceability_events": ["lab_id", "unit_id", "object_id", "event_type"],
    }.items():
        for column in columns:
            op.create_index(f"ix_{table}_{column}", table, [column], if_not_exists=True)


def downgrade() -> None:
    for table in ("blood_bank_traceability_events", "blood_bank_reactions", "blood_bank_reservations", "blood_bank_patient_samples"):
        if table in _tables():
            op.drop_table(table)
    for table, column in (("blood_bank_crossmatches", "policy_version"), ("blood_bank_crossmatches", "sample_id")):
        if table in _tables() and column in _columns(table):
            op.drop_column(table, column)
