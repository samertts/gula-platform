"""AI Safety + Hallucination Telemetry — additive columns on ai_interactions.

Revision ID: 20260511_0002
Revises    : 20260511_0001
Create Date: 2026-05-11

Operationalises directive §8 (AI Safety Layer) and §14 (Hallucination
Control) on top of the Phase 3 dataset substrate established by
``20260511_0001_ai_interactions_dataset.py``. Every column is additive,
nullable, and flag-gated via ``ENABLE_AI_DATASET`` — no existing code path
reads or writes any of these fields until the route schema below is
exercised.

Columns added to ``ai_interactions``
------------------------------------
§8 — Safety
  • ``confidence_score``      Float, 0..1, nullable. Model self-reported
                              confidence in the response.
  • ``risk_level``            String(32), nullable. One of:
                              ``informational`` / ``low_risk`` /
                              ``moderate_risk`` / ``high_risk``.
  • ``escalation_recommended`` Boolean, server_default false. True iff the
                              response surfaced an explicit
                              "see a physician" cue (mandatory for
                              ``high_risk``).

§14 — Hallucination control
  • ``retrieval_used``        Boolean, nullable. True iff the response was
                              grounded in retrieved chunks (RAG hit),
                              False iff the model answered without
                              retrieval. ``NULL`` = unknown / not logged.
  • ``source_quality``        Float, 0..1, nullable. Aggregate similarity
                              / source-trust score for the retrieval
                              chunks used.
  • ``unsupported_claims``    Integer, nullable. Count of assertions in
                              the response that the safety post-processor
                              could not back with a retrieval ref.
  • ``fallback_generation``   Boolean, server_default false. True iff the
                              primary model failed and a fallback (rule
                              engine / smaller model / canned response)
                              produced the answer.
  • ``safety_flags``          JSON / JSONB. Free-form list of additional
                              safety markers (e.g. ``["pii_detected",
                              "prompt_injection_suspected"]``). Forward-
                              compatible — new flags don't require schema
                              changes.

Indexes
-------
  • ``ix_ai_interactions_risk_level`` — analytics queries filter heavily
    on risk class.
  • ``ix_ai_interactions_escalation`` — operator dashboards listing
    escalated interactions.

Production-safety rules
-----------------------
  • All operations are idempotent (``_has_column`` / ``_index_exists``).
  • All new columns nullable or have a ``server_default`` — existing rows
    (currently zero, but the rule still holds) remain valid.
  • Zero ``UPDATE`` against existing rows — additive only.
  • Migration runs in O(table-locks-only) time; no row scan.

Downgrade drops the columns + indexes in reverse order. Safe to round-trip
on a clean DB; production rollback should be coordinated with the route
schema rollback (the route will simply stop accepting the new fields and
return defaults).
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


revision      = "20260511_0002"
down_revision = "20260511_0001"
branch_labels = None
depends_on    = None


# ─── Helpers ─────────────────────────────────────────────────────────────────
# Local copies kept consistent with the surrounding migrations
# (20260511_0001, 20260506_0001). A future consolidation into
# backend/migrations/helpers.py is tracked separately in directive §17A.

def _table_exists(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def _has_column(table: str, column: str) -> bool:
    insp = inspect(op.get_bind())
    if not insp.has_table(table):
        return False
    return any(c["name"] == column for c in insp.get_columns(table))


def _index_exists(index: str) -> bool:
    inspector = inspect(op.get_bind())
    for table in inspector.get_table_names():
        if any(i["name"] == index for i in inspector.get_indexes(table)):
            return True
    return False


def _pg() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def _json_col() -> sa.types.TypeEngine:
    return postgresql.JSONB if _pg() else sa.JSON


# ─── Upgrade ─────────────────────────────────────────────────────────────────

_TABLE = "ai_interactions"

_NEW_COLUMNS = [
    # name,                     factory
    ("confidence_score",        lambda: sa.Column("confidence_score", sa.Float(), nullable=True)),
    ("risk_level",              lambda: sa.Column("risk_level", sa.String(32), nullable=True)),
    ("escalation_recommended",  lambda: sa.Column("escalation_recommended", sa.Boolean(),
                                                  nullable=False, server_default=sa.text("false"))),
    ("retrieval_used",          lambda: sa.Column("retrieval_used", sa.Boolean(), nullable=True)),
    ("source_quality",          lambda: sa.Column("source_quality", sa.Float(), nullable=True)),
    ("unsupported_claims",      lambda: sa.Column("unsupported_claims", sa.Integer(), nullable=True)),
    ("fallback_generation",     lambda: sa.Column("fallback_generation", sa.Boolean(),
                                                  nullable=False, server_default=sa.text("false"))),
    ("safety_flags",            lambda: sa.Column("safety_flags", _json_col(), nullable=True)),
]


def upgrade() -> None:
    # Defensive: if the base table is missing we cannot extend it.
    # 20260511_0001 must have run first (alembic chain enforces this).
    if not _table_exists(_TABLE):
        return

    for name, factory in _NEW_COLUMNS:
        if not _has_column(_TABLE, name):
            op.add_column(_TABLE, factory())

    if not _index_exists("ix_ai_interactions_risk_level"):
        op.create_index("ix_ai_interactions_risk_level", _TABLE, ["risk_level"])
    if not _index_exists("ix_ai_interactions_escalation"):
        op.create_index("ix_ai_interactions_escalation", _TABLE, ["escalation_recommended"])


# ─── Downgrade ───────────────────────────────────────────────────────────────

def downgrade() -> None:
    if not _table_exists(_TABLE):
        return

    for idx in ("ix_ai_interactions_escalation", "ix_ai_interactions_risk_level"):
        if _index_exists(idx):
            try:
                op.drop_index(idx, table_name=_TABLE)
            except Exception:
                pass

    for name, _ in reversed(_NEW_COLUMNS):
        if _has_column(_TABLE, name):
            try:
                op.drop_column(_TABLE, name)
            except Exception:
                pass
