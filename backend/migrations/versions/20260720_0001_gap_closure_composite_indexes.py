"""Enterprise gap closure: add composite indexes for query performance

Gaps closed:
1. `quality_controls` — missing (lab_id, test_code, created_at) for trend queries
2. `samples` — missing (order_id, status) for status-filtering by order
3. `outbox_events` — missing (status, created_at) for outbox worker polling
4. `audit_logs` — missing (user_id, created_at) for user action history queries

Migration is idempotent (uses IF NOT EXISTS / manual existence checks).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260720_0001"
down_revision: Union[str, None] = "20260719_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


INDEXES = [
    ("ix_quality_controls_lab_test_time", "quality_controls", ("lab_id", "test_code", "created_at")),
    ("ix_samples_order_status", "samples", ("order_id", "status")),
    ("ix_outbox_events_status_created", "outbox_events", ("status", "created_at")),
    ("ix_audit_logs_user_time", "audit_logs", ("user_id", "created_at")),
]


def _index_exists(name: str) -> bool:
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT 1 FROM pg_indexes WHERE indexname = :name"),
        {"name": name},
    )
    return result.scalar() is not None


def upgrade() -> None:
    for name, table, columns in INDEXES:
        if not _index_exists(name):
            op.create_index(name, table, columns)
            print(f"  ✓ Created index {name} on {table}{columns}")


def downgrade() -> None:
    for name, table, columns in reversed(INDEXES):
        if _index_exists(name):
            op.drop_index(name, table_name=table)
            print(f"  ✗ Dropped index {name} on {table}")
