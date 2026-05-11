"""SQLAlchemy ORM models for the AI Interaction Dataset.

See migration ``20260511_0001_ai_interactions_dataset.py`` for the
table-level schema rationale and the anonymisation invariant.
"""
from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from ..database import Base


# ── Cross-dialect type helpers ───────────────────────────────────────────────
# In production the engine is PostgreSQL (see app/database.py); tests may run
# against SQLite. SQLAlchemy's PG-specific UUID/JSONB types compile correctly
# against PG and degrade gracefully via with_variant for sqlite.
_UUID = UUID(as_uuid=True)
_JSON = JSONB


def _uuid_pk() -> Column:
    return Column(_UUID, primary_key=True, default=uuid.uuid4, nullable=False)


class AIInteraction(Base):
    __tablename__ = "ai_interactions"

    id      = _uuid_pk()
    lab_id  = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"),
                     nullable=False, index=True)
    anonymous_session_id = Column(String(128), nullable=False, index=True)
    language           = Column(String(8),  nullable=True)
    region             = Column(String(64), nullable=True)
    intent             = Column(String(64), nullable=True, index=True)
    prompt             = Column(Text,       nullable=True)
    prompt_redacted    = Column(Boolean,    nullable=False, default=False)
    response           = Column(Text,       nullable=True)
    response_model     = Column(String(64), nullable=True)
    retrieval_strategy = Column(String(64), nullable=True)
    retrieval_count    = Column(Integer,    nullable=True)
    biomarkers         = Column(_JSON,      nullable=True)
    latency_ms         = Column(Integer,    nullable=True)
    status             = Column(String(20), nullable=False, default="ok", index=True)
    error_code         = Column(String(64), nullable=True)
    created_at         = Column(DateTime(timezone=True), nullable=False, index=True)

    retrieval_refs = relationship(
        "AIRetrievalRef",
        backref="interaction",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    feedback = relationship(
        "AIFeedback",
        backref="interaction",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class AIRetrievalRef(Base):
    __tablename__ = "ai_retrieval_refs"

    id             = _uuid_pk()
    interaction_id = Column(_UUID, ForeignKey("ai_interactions.id", ondelete="CASCADE"),
                            nullable=False, index=True)
    source     = Column(String(64),  nullable=True)
    doc_id     = Column(String(128), nullable=True)
    doc_title  = Column(String(256), nullable=True)
    chunk_text = Column(Text,        nullable=True)
    similarity = Column(Float,       nullable=True)
    rank       = Column(Integer,     nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)


class AIFeedback(Base):
    __tablename__ = "ai_feedback"

    id             = _uuid_pk()
    interaction_id = Column(_UUID, ForeignKey("ai_interactions.id", ondelete="CASCADE"),
                            nullable=False, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"),
                    nullable=False, index=True)
    anonymous_session_id = Column(String(128), nullable=False)
    signal     = Column(String(32), nullable=False, index=True)
    notes      = Column(Text,       nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)


class AIUnresolvedQuestion(Base):
    __tablename__ = "ai_unresolved_questions"

    id             = _uuid_pk()
    interaction_id = Column(_UUID, ForeignKey("ai_interactions.id", ondelete="SET NULL"),
                            nullable=True)
    lab_id   = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"),
                      nullable=False, index=True)
    anonymous_session_id = Column(String(128), nullable=True)
    question    = Column(Text,       nullable=False)
    language    = Column(String(8),  nullable=True)
    category    = Column(String(64), nullable=True)
    status      = Column(String(20), nullable=False, default="open", index=True)
    created_at  = Column(DateTime(timezone=True), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)


class MedicalTerminologyNormalized(Base):
    __tablename__ = "medical_terminology_normalized"

    id          = _uuid_pk()
    term_en     = Column(String(256), nullable=True)
    term_ar     = Column(String(256), nullable=True)
    term_ar_iq  = Column(String(256), nullable=True)
    code        = Column(String(64),  nullable=True)
    code_system = Column(String(32),  nullable=True)
    category    = Column(String(64),  nullable=True, index=True)
    synonyms    = Column(_JSON,       nullable=True)
    notes       = Column(Text,        nullable=True)
    created_at  = Column(DateTime(timezone=True), nullable=False)
    updated_at  = Column(DateTime(timezone=True), nullable=False)
