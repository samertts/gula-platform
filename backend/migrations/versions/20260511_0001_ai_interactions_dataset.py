"""AI Interaction Dataset — operational medical-intelligence collection pipeline.

Revision ID: 20260511_0001
Revises    : 20260506_0001
Create Date: 2026-05-11

Introduced as part of the 2026-05-11 production launch. Establishes the
structured storage substrate for the AI feedback loop, RAG retrieval-ref
audit trail, and Iraqi-Arabic / regional medical-terminology dataset that
GULA will accumulate over time (see docs/ai/IRAQI_HEALTHCARE_INTELLIGENCE.md).

Production-safety rules
-----------------------
- All operations are idempotent (``_table_exists`` / ``_index_exists`` guards).
- No NOT NULL columns except primary keys + ``lab_id`` + foreign keys to
  rows that exist by construction (tenant isolation invariant).
- No long locks: every table is brand new with zero rows on first apply.
- ``ENABLE_AI_DATASET`` defaults to OFF — the tables exist but no code path
  reads or writes until the flag is flipped. This decouples the schema
  rollout from the application rollout.

Tables created
--------------
  1. ai_interactions               — every user↔AI exchange. Carries the
                                     anonymised session id, language code,
                                     detected medical intent, the prompt,
                                     the AI response, latency, retrieval
                                     refs, and a denormalised lab_id.
  2. ai_retrieval_refs             — per-interaction list of retrieved
                                     documents/chunks (RAG audit trail).
  3. ai_feedback                   — explicit feedback signals bound to
                                     an interaction (helpful / not /
                                     unclear / need_doctor / incorrect).
  4. ai_unresolved_questions       — questions the AI explicitly could not
                                     answer or that were escalated.
  5. medical_terminology_normalized — normalised Iraqi-Arabic + English
                                     biomarker / test-name vocabulary.

Anonymisation invariant
-----------------------
``anonymous_session_id`` is the only correlation key on every row. The
schema deliberately has **no** columns for national_id, phone, email,
full name, or any other patient identifier. ``user_id`` and ``patient_id``
are explicitly omitted from these tables. See
``docs/ai/AI_ARCHITECTURE_CONSTRAINTS.md`` § "Data protection contract".

Tenant isolation
----------------
``lab_id`` is required on ``ai_interactions``, ``ai_feedback``, and
``ai_unresolved_questions``. ``ai_retrieval_refs`` inherits isolation
through its FK to ``ai_interactions``. ``medical_terminology_normalized``
is global (no lab_id) — it is shared reference data.
"""
from __future__ import annotations

from alembic import context, op
import sqlalchemy as sa
from sqlalchemy import inspect, text
from sqlalchemy.dialects import postgresql
import contextlib


revision      = "20260511_0001"
down_revision = "20260506_0001"
branch_labels = None
depends_on    = None


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _table_exists(table: str) -> bool:
    if context.is_offline_mode():
        return True
    return inspect(op.get_bind()).has_table(table)


def _index_exists(index: str) -> bool:
    if context.is_offline_mode():
        return False
    inspector = inspect(op.get_bind())
    for table in inspector.get_table_names():
        if any(i["name"] == index for i in inspector.get_indexes(table)):
            return True
    return False


def _pg() -> bool:
    if context.is_offline_mode():
        return True
    return op.get_bind().dialect.name == "postgresql"


def _uuid_col() -> sa.types.TypeEngine:
    return postgresql.UUID(as_uuid=True) if _pg() else sa.String(36)


def _json_col() -> sa.types.TypeEngine:
    return postgresql.JSONB if _pg() else sa.JSON


# ─── Upgrade ─────────────────────────────────────────────────────────────────

def upgrade() -> None:
    if _pg():
        op.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))

    pk_default = sa.text("gen_random_uuid()") if _pg() else None

    # 1. ai_interactions
    if not _table_exists("ai_interactions"):
        op.create_table(
            "ai_interactions",
            sa.Column("id", _uuid_col(), primary_key=True,
                      server_default=pk_default, nullable=False),
            sa.Column("lab_id", sa.Integer(),
                      sa.ForeignKey("labs.id", ondelete="CASCADE"),
                      nullable=False),
            sa.Column("anonymous_session_id", sa.String(128), nullable=False),
            sa.Column("language",          sa.String(8),  nullable=True),  # 'ar' / 'ar-IQ' / 'en'
            sa.Column("region",            sa.String(64), nullable=True),  # 'Baghdad' / 'Basra' / ...
            sa.Column("intent",            sa.String(64), nullable=True),  # 'interpret_result' / 'navigate' / 'explain_biomarker' / ...
            sa.Column("prompt",            sa.Text(),     nullable=True),
            sa.Column("prompt_redacted",   sa.Boolean(),  nullable=False, server_default=sa.text("false")),
            sa.Column("response",          sa.Text(),     nullable=True),
            sa.Column("response_model",    sa.String(64), nullable=True),
            sa.Column("retrieval_strategy", sa.String(64), nullable=True),
            sa.Column("retrieval_count",   sa.Integer(),  nullable=True),
            sa.Column("biomarkers",        _json_col(),   nullable=True),  # array of normalised biomarker codes
            sa.Column("latency_ms",        sa.Integer(),  nullable=True),
            sa.Column("status",            sa.String(20), nullable=False, server_default="ok"),  # ok / error / guardrail_blocked / escalated
            sa.Column("error_code",        sa.String(64), nullable=True),
            sa.Column("created_at",        sa.DateTime(timezone=True),
                      server_default=sa.func.now(), nullable=False),
        )

    if not _index_exists("ix_ai_interactions_lab_created"):
        op.create_index("ix_ai_interactions_lab_created", "ai_interactions",
                        ["lab_id", "created_at"])
    if not _index_exists("ix_ai_interactions_session"):
        op.create_index("ix_ai_interactions_session", "ai_interactions",
                        ["anonymous_session_id"])
    if not _index_exists("ix_ai_interactions_intent"):
        op.create_index("ix_ai_interactions_intent", "ai_interactions",
                        ["intent"])
    if not _index_exists("ix_ai_interactions_status"):
        op.create_index("ix_ai_interactions_status", "ai_interactions",
                        ["status"])

    # 2. ai_retrieval_refs
    if not _table_exists("ai_retrieval_refs"):
        op.create_table(
            "ai_retrieval_refs",
            sa.Column("id", _uuid_col(), primary_key=True,
                      server_default=pk_default, nullable=False),
            sa.Column("interaction_id", _uuid_col(),
                      sa.ForeignKey("ai_interactions.id", ondelete="CASCADE"),
                      nullable=False),
            sa.Column("source",       sa.String(64),  nullable=True),  # 'loinc' / 'snomed' / 'internal_glossary' / 'guideline'
            sa.Column("doc_id",       sa.String(128), nullable=True),
            sa.Column("doc_title",    sa.String(256), nullable=True),
            sa.Column("chunk_text",   sa.Text(),      nullable=True),
            sa.Column("similarity",   sa.Float(),     nullable=True),
            sa.Column("rank",         sa.Integer(),   nullable=True),
            sa.Column("created_at",   sa.DateTime(timezone=True),
                      server_default=sa.func.now(), nullable=False),
        )

    if not _index_exists("ix_ai_retrieval_refs_interaction"):
        op.create_index("ix_ai_retrieval_refs_interaction", "ai_retrieval_refs",
                        ["interaction_id"])

    # 3. ai_feedback
    if not _table_exists("ai_feedback"):
        op.create_table(
            "ai_feedback",
            sa.Column("id", _uuid_col(), primary_key=True,
                      server_default=pk_default, nullable=False),
            sa.Column("interaction_id", _uuid_col(),
                      sa.ForeignKey("ai_interactions.id", ondelete="CASCADE"),
                      nullable=False),
            sa.Column("lab_id", sa.Integer(),
                      sa.ForeignKey("labs.id", ondelete="CASCADE"),
                      nullable=False),
            sa.Column("anonymous_session_id", sa.String(128), nullable=False),
            # One of: helpful / not_helpful / unclear / need_doctor / incorrect_interpretation
            sa.Column("signal",  sa.String(32), nullable=False),
            sa.Column("notes",   sa.Text(),     nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True),
                      server_default=sa.func.now(), nullable=False),
        )

    if not _index_exists("ix_ai_feedback_interaction"):
        op.create_index("ix_ai_feedback_interaction", "ai_feedback",
                        ["interaction_id"])
    if not _index_exists("ix_ai_feedback_lab_created"):
        op.create_index("ix_ai_feedback_lab_created", "ai_feedback",
                        ["lab_id", "created_at"])
    if not _index_exists("ix_ai_feedback_signal"):
        op.create_index("ix_ai_feedback_signal", "ai_feedback", ["signal"])

    # 4. ai_unresolved_questions
    if not _table_exists("ai_unresolved_questions"):
        op.create_table(
            "ai_unresolved_questions",
            sa.Column("id", _uuid_col(), primary_key=True,
                      server_default=pk_default, nullable=False),
            sa.Column("interaction_id", _uuid_col(),
                      sa.ForeignKey("ai_interactions.id", ondelete="SET NULL"),
                      nullable=True),
            sa.Column("lab_id", sa.Integer(),
                      sa.ForeignKey("labs.id", ondelete="CASCADE"),
                      nullable=False),
            sa.Column("anonymous_session_id", sa.String(128), nullable=True),
            sa.Column("question",  sa.Text(),     nullable=False),
            sa.Column("language",  sa.String(8),  nullable=True),
            sa.Column("category",  sa.String(64), nullable=True),
            sa.Column("status",    sa.String(20), nullable=False, server_default="open"),  # open / triaged / resolved / discarded
            sa.Column("created_at", sa.DateTime(timezone=True),
                      server_default=sa.func.now(), nullable=False),
            sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        )

    if not _index_exists("ix_ai_unresolved_status_created"):
        op.create_index("ix_ai_unresolved_status_created",
                        "ai_unresolved_questions", ["status", "created_at"])
    if not _index_exists("ix_ai_unresolved_lab"):
        op.create_index("ix_ai_unresolved_lab",
                        "ai_unresolved_questions", ["lab_id"])

    # 5. medical_terminology_normalized (global, no lab_id)
    if not _table_exists("medical_terminology_normalized"):
        op.create_table(
            "medical_terminology_normalized",
            sa.Column("id", _uuid_col(), primary_key=True,
                      server_default=pk_default, nullable=False),
            sa.Column("term_en",      sa.String(256), nullable=True),
            sa.Column("term_ar",      sa.String(256), nullable=True),
            sa.Column("term_ar_iq",   sa.String(256), nullable=True),  # Iraqi-Arabic dialect variant
            sa.Column("code",         sa.String(64),  nullable=True),
            sa.Column("code_system",  sa.String(32),  nullable=True),  # 'LOINC' / 'SNOMED' / 'ICD10' / 'internal'
            sa.Column("category",     sa.String(64),  nullable=True),  # 'biomarker' / 'test' / 'condition' / 'unit'
            sa.Column("synonyms",     _json_col(),    nullable=True),  # array of strings
            sa.Column("notes",        sa.Text(),      nullable=True),
            sa.Column("created_at",   sa.DateTime(timezone=True),
                      server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at",   sa.DateTime(timezone=True),
                      server_default=sa.func.now(), nullable=False),
        )

    if not _index_exists("ix_medterm_code"):
        op.create_index("ix_medterm_code", "medical_terminology_normalized",
                        ["code_system", "code"])
    if not _index_exists("ix_medterm_category"):
        op.create_index("ix_medterm_category",
                        "medical_terminology_normalized", ["category"])


# ─── Downgrade ───────────────────────────────────────────────────────────────

def downgrade() -> None:
    # Drop in reverse FK-dependency order.
    for tbl, idx_names in [
        ("medical_terminology_normalized",
         ["ix_medterm_code", "ix_medterm_category"]),
        ("ai_unresolved_questions",
         ["ix_ai_unresolved_status_created", "ix_ai_unresolved_lab"]),
        ("ai_feedback",
         ["ix_ai_feedback_interaction", "ix_ai_feedback_lab_created", "ix_ai_feedback_signal"]),
        ("ai_retrieval_refs",
         ["ix_ai_retrieval_refs_interaction"]),
        ("ai_interactions",
         ["ix_ai_interactions_lab_created", "ix_ai_interactions_session",
          "ix_ai_interactions_intent", "ix_ai_interactions_status"]),
    ]:
        if _table_exists(tbl):
            for idx in idx_names:
                if _index_exists(idx):
                    with contextlib.suppress(Exception):
                        op.drop_index(idx, table_name=tbl)
            op.drop_table(tbl)
