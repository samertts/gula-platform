"""Query indexes for immunization dashboards and overdue work queues.

Prepared locally; not executed by this change set.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import context, op

revision = "20260817_0031"
down_revision = "20260817_0030"
branch_labels = None
depends_on = None

_INDEXES = {
    "ph_immunization_records": {
        "ix_ph_immunization_records_lab_date_status": ["lab_id", "administration_date", "status"],
        "ix_ph_immunization_records_lab_patient": ["lab_id", "patient_id"],
    },
    "ph_immunization_schedules": {
        "ix_ph_immunization_schedules_lab_status_due": ["lab_id", "status", "due_date"],
        "ix_ph_immunization_schedules_lab_patient_due": ["lab_id", "patient_id", "due_date"],
    },
    "ph_immunization_follow_up_tasks": {
        "ix_ph_immunization_followup_lab_status_action": ["lab_id", "status", "next_action_at"],
    },
}


def upgrade() -> None:
    if context.is_offline_mode():
        for table_name, indexes in _INDEXES.items():
            for index_name, columns in indexes.items():
                op.create_index(index_name, table_name, columns)
        return
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for table_name, indexes in _INDEXES.items():
        if not inspector.has_table(table_name):
            continue
        existing = {item["name"] for item in inspector.get_indexes(table_name)}
        for index_name, columns in indexes.items():
            if index_name not in existing:
                op.create_index(index_name, table_name, columns)


def downgrade() -> None:
    # Keep performance indexes during rollback; no data is removed by this migration.
    return
