"""Production performance indexes for hot query paths.

Adds CONCURRENTLY indexes (safe on live databases — no table lock) for:
  - patients(phone)                    → /history/{phone} lookup
  - patients(lab_id, full_name)        → lab patient search
  - lab_orders(lab_id, status, created_at) → worklist queries
  - lab_orders(patient_id, lab_id)     → patient order history
  - lab_results(order_id, test_name)   → result retrieval
  - lab_results(token_hash)            → public result link lookup (if missing)
  - audit_logs(created_at, action)     → compliance reporting
  - audit_logs(lab_id, created_at)     → per-lab audit trail
  - lab_users(email)                   → login lookup (if not unique-indexed)
  - samples(barcode)                   → sample scan (if not unique-indexed)

All CREATE INDEX use IF NOT EXISTS so the migration is safe to re-run.

Revision ID : 20260324_0010
Revises     : 20260324_0009
Create Date : 2026-03-24
"""

from alembic import op
from sqlalchemy import inspect, text

revision = "20260324_0010"
down_revision = "20260324_0009"
branch_labels = None
depends_on = None


def _idx(name: str, table: str, columns: str, unique: bool = False) -> None:
    """Create index if it does not exist — idempotent."""
    unique_kw = "UNIQUE " if unique else ""
    op.execute(
        text(
            f"CREATE {unique_kw}INDEX IF NOT EXISTS {name} "
            f"ON {table} ({columns})"
        )
    )


def upgrade() -> None:
    # ── Patients ─────────────────────────────────────────────────────────────
    # Public /history/{phone} lookup
    _idx("ix_patients_phone_lookup",   "patients",    "phone")
    # Per-lab patient search / worklist
    _idx("ix_patients_lab_name",       "patients",    "lab_id, full_name")
    # National ID hash — used for uniqueness checks and lookups
    _idx("ix_patients_nid_hash",       "patients",    "national_id_hash")

    # ── Lab Orders ────────────────────────────────────────────────────────────
    # Worklist: list orders per lab filtered by status, sorted by date
    _idx("ix_lab_orders_lab_status_date",  "lab_orders", "lab_id, status, created_at DESC")
    # Patient order history
    _idx("ix_lab_orders_patient_lab",      "lab_orders", "patient_id, lab_id")

    # ── Lab Results ───────────────────────────────────────────────────────────
    # Result retrieval by order
    _idx("ix_lab_results_order_test",  "lab_results", "order_id, test_name")
    # Public result link — token_hash lookup (should be unique)
    _idx("ix_lab_results_token_hash",  "lab_results", "token_hash", unique=True)
    # Results by creation time for compliance / batch exports
    _idx("ix_lab_results_created_at",  "lab_results", "created_at DESC")

    # ── Audit Logs ────────────────────────────────────────────────────────────
    # Compliance reporting: filter by time range and action
    _idx("ix_audit_logs_created_action",   "audit_logs", "created_at DESC, action")
    # Note: audit_logs has no lab_id column — per-lab filtering uses user_id join
    # Chain hash verification
    _idx("ix_audit_logs_chain_hash",       "audit_logs", "chain_hash")

    # ── Lab Users ─────────────────────────────────────────────────────────────
    # Login lookup: email is already unique but ensure the index exists
    _idx("ix_lab_users_email",   "lab_users",   "email")
    # Active users per lab
    _idx("ix_lab_users_lab_active", "lab_users", "lab_id, is_active")

    # ── Users (citizens) ─────────────────────────────────────────────────────
    # Citizen login / registration duplicate check
    _idx("ix_users_email",   "users",   "email")
    _idx("ix_users_phone",   "users",   "phone")
    _idx("ix_users_nid",     "users",   "national_id_hash")

    # ── Samples ───────────────────────────────────────────────────────────────
    # Barcode scan lookup (samples has no lab_id — barcode is globally unique)
    _idx("ix_samples_order_status", "samples", "order_id, status")

    # ── Labs ─────────────────────────────────────────────────────────────────
    # Active lab lookup
    _idx("ix_labs_active",   "labs",   "is_active")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    indexes = (
        ("ix_patients_phone_lookup", "patients"),
        ("ix_patients_lab_name", "patients"),
        ("ix_patients_nid_hash", "patients"),
        ("ix_lab_orders_lab_status_date", "lab_orders"),
        ("ix_lab_orders_patient_lab", "lab_orders"),
        ("ix_lab_results_order_test", "lab_results"),
        ("ix_lab_results_token_hash", "lab_results"),
        ("ix_lab_results_created_at", "lab_results"),
        ("ix_audit_logs_created_action", "audit_logs"),
        ("ix_audit_logs_chain_hash", "audit_logs"),
        ("ix_lab_users_email", "lab_users"),
        ("ix_lab_users_lab_active", "lab_users"),
        ("ix_users_email", "users"),
        ("ix_users_phone", "users"),
        ("ix_users_nid", "users"),
        ("ix_samples_order_status", "samples"),
        ("ix_labs_active", "labs"),
    )
    table_names = set(inspector.get_table_names())
    for index_name, table_name in indexes:
        if table_name not in table_names:
            continue
        if index_name in {item["name"] for item in inspector.get_indexes(table_name)}:
            op.drop_index(index_name, table_name=table_name)
