"""Claims + Fraud Detection tables.

New tables:
  claims       — insurance claims for completed lab orders
  fraud_scores — per-claim fraud scoring audit trail

Lifecycle: submitted → fraud_scored → approved|pending_review|rejected → paid

Decision thresholds:
  score < 0.30  → approve
  score 0.30–0.69 → review
  score ≥ 0.70  → reject

All DDL is idempotent — safe to run on existing databases.

Revision ID : 20260405_0015
Revises     : 20260405_0014
Create Date : 2026-04-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision      = "20260405_0015"
down_revision = "20260405_0014"
branch_labels = None
depends_on    = None


def _table_exists(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def upgrade() -> None:
    # ── claims ────────────────────────────────────────────────────────────────
    if not _table_exists("claims"):
        op.create_table(
            "claims",
            sa.Column("id",              sa.Integer(),          primary_key=True, autoincrement=True),
            sa.Column("patient_id",      sa.Integer(),          sa.ForeignKey("patients.id"), nullable=False),
            sa.Column("order_id",        sa.Integer(),          sa.ForeignKey("lab_orders.id"), nullable=False),
            sa.Column("lab_id",          sa.Integer(),          sa.ForeignKey("labs.id"), nullable=False),
            # Financials
            sa.Column("amount",          sa.Numeric(12, 2),     nullable=False),
            sa.Column("currency",        sa.String(3),          nullable=False, server_default="IQD"),
            # Insurance
            sa.Column("insurance_id",    sa.String(100),        nullable=True),
            sa.Column("diagnosis_codes", sa.Text(),             nullable=True),
            sa.Column("notes",           sa.Text(),             nullable=True),
            # Status
            sa.Column("status",          sa.String(30),         nullable=False, server_default="submitted"),
            # Fraud
            sa.Column("fraud_score",     sa.Numeric(4, 3),      nullable=True),
            sa.Column("fraud_decision",  sa.String(20),         nullable=True),
            sa.Column("fraud_flags",     sa.Text(),             nullable=True),
            # Audit
            sa.Column("submitted_by",    sa.Integer(),          sa.ForeignKey("lab_users.id"), nullable=True),
            sa.Column("submitted_at",    sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("reviewed_by",     sa.Integer(),          sa.ForeignKey("lab_users.id"), nullable=True),
            sa.Column("reviewed_at",     sa.DateTime(timezone=True), nullable=True),
            sa.Column("paid_at",         sa.DateTime(timezone=True), nullable=True),
            # Idempotency
            sa.Column("idempotency_key", sa.String(64),         nullable=True),
            # Constraints
            sa.UniqueConstraint("order_id", name="uq_claim_order_id"),
        )
        op.create_index("ix_claims_patient_id",   "claims", ["patient_id"])
        op.create_index("ix_claims_order_id",      "claims", ["order_id"])
        op.create_index("ix_claims_lab_id",        "claims", ["lab_id"])
        op.create_index("ix_claims_status",        "claims", ["status"])
        op.create_index("ix_claims_insurance_id",  "claims", ["insurance_id"])
        op.create_index("ix_claims_submitted_at",  "claims", ["submitted_at"])
        op.create_index("ix_claims_idempotency",   "claims", ["idempotency_key"])
        op.create_index("ix_claims_lab_status",    "claims", ["lab_id", "status"])

    # ── fraud_scores ──────────────────────────────────────────────────────────
    if not _table_exists("fraud_scores"):
        op.create_table(
            "fraud_scores",
            sa.Column("id",              sa.Integer(),          primary_key=True, autoincrement=True),
            sa.Column("claim_id",        sa.Integer(),          sa.ForeignKey("claims.id"), nullable=False, unique=True),
            sa.Column("score_amount",    sa.Numeric(4, 3),      nullable=True),
            sa.Column("score_velocity",  sa.Numeric(4, 3),      nullable=True),
            sa.Column("score_duplicate", sa.Numeric(4, 3),      nullable=True),
            sa.Column("score_ai",        sa.Numeric(4, 3),      nullable=True),
            sa.Column("score_final",     sa.Numeric(4, 3),      nullable=False),
            sa.Column("rules_triggered", sa.Text(),             nullable=True),
            sa.Column("ai_explanation",  sa.Text(),             nullable=True),
            sa.Column("ai_confidence",   sa.Numeric(4, 3),      nullable=True),
            sa.Column("decision",        sa.String(20),         nullable=False),
            sa.Column("scored_at",       sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("engine_version",  sa.String(20),         nullable=False, server_default="1.0.0"),
        )
        op.create_index("ix_fraud_scores_claim_id",  "fraud_scores", ["claim_id"])
        op.create_index("ix_fraud_scores_scored_at", "fraud_scores", ["scored_at"])
        op.create_index("ix_fraud_scores_decision",  "fraud_scores", ["decision"])


def downgrade() -> None:
    if _table_exists("fraud_scores"):
        op.drop_table("fraud_scores")
    if _table_exists("claims"):
        op.drop_table("claims")
