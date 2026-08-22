"""SQLAlchemy ORM models for the AI Interaction Dataset.

See migration ``20260511_0001_ai_interactions_dataset.py`` for the
table-level schema rationale and the anonymisation invariant.
"""

from __future__ import annotations

import uuid

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, relationship

from ..database import Base

# ── Cross-dialect type helpers ───────────────────────────────────────────────
# Production runs PostgreSQL; the test suite runs SQLite in-memory (see
# tests/conftest.py). SQLAlchemy 2.0's portable Uuid type maps to native
# PG UUID on PostgreSQL and CHAR(32) on SQLite, with bidirectional bind/result
# conversion handled by SQLAlchemy. The generic JSON type maps to PG JSONB-
# compatible storage on PG (both deserialise to Python dict/list) and to
# native JSON on SQLite. The actual PG column type (UUID, JSONB) is created
# by the Alembic migration; the ORM declarations only need to be portable
# enough for the SQLite test substrate.
_UUID = Uuid(as_uuid=True)
_JSON = JSON


def _uuid_pk() -> Column[uuid.UUID]:
    return Column(_UUID, primary_key=True, default=uuid.uuid4, nullable=False)


class AIInteraction(Base):
    __tablename__ = "ai_interactions"

    id = _uuid_pk()
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    anonymous_session_id = Column(String(128), nullable=False, index=True)
    language = Column(String(8), nullable=True)
    region = Column(String(64), nullable=True)
    intent = Column(String(64), nullable=True, index=True)
    prompt = Column(Text, nullable=True)
    prompt_redacted = Column(Boolean, nullable=False, default=False)
    response = Column(Text, nullable=True)
    response_model = Column(String(64), nullable=True)
    retrieval_strategy = Column(String(64), nullable=True)
    retrieval_count = Column(Integer, nullable=True)
    biomarkers = Column(_JSON, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False, default="ok", index=True)
    error_code = Column(String(64), nullable=True)

    # Safety layer (directive §8). All nullable: existing rows pre-migration
    # remain valid; new writes are responsible for populating risk_level
    # whenever the AI gateway can compute it. ``escalation_recommended`` is
    # mandatory whenever risk_level == 'high_risk' (enforced in the route).
    confidence_score = Column(Float, nullable=True)
    risk_level = Column(String(32), nullable=True, index=True)
    escalation_recommended = Column(Boolean, nullable=False, default=False, index=True)

    # Hallucination control (directive §14). retrieval_used = None means
    # "not logged"; True/False are explicit. unsupported_claims is a count
    # (0 == clean); fallback_generation is True when a secondary path
    # produced the response.
    retrieval_used = Column(Boolean, nullable=True)
    source_quality = Column(Float, nullable=True)
    unsupported_claims = Column(Integer, nullable=True)
    fallback_generation = Column(Boolean, nullable=False, default=False)
    safety_flags = Column(_JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, index=True)

    retrieval_refs: Mapped[list[AIRetrievalRef]] = relationship(
        "AIRetrievalRef",
        backref="interaction",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    feedback: Mapped[list[AIFeedback]] = relationship(
        "AIFeedback",
        backref="interaction",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class AIRetrievalRef(Base):
    __tablename__ = "ai_retrieval_refs"

    id = _uuid_pk()
    interaction_id: Mapped[uuid.UUID] = Column(
        _UUID, ForeignKey("ai_interactions.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    source = Column(String(64), nullable=True)
    doc_id = Column(String(128), nullable=True)
    doc_title = Column(String(256), nullable=True)
    chunk_text = Column(Text, nullable=True)
    similarity = Column(Float, nullable=True)
    rank = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)


class AIFeedback(Base):
    __tablename__ = "ai_feedback"

    id = _uuid_pk()
    interaction_id: Mapped[uuid.UUID] = Column(
        _UUID, ForeignKey("ai_interactions.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    anonymous_session_id = Column(String(128), nullable=False)
    signal = Column(String(32), nullable=False, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)


class AIUnresolvedQuestion(Base):
    __tablename__ = "ai_unresolved_questions"

    id = _uuid_pk()
    interaction_id: Mapped[uuid.UUID | None] = Column(
        _UUID, ForeignKey("ai_interactions.id", ondelete="SET NULL"), nullable=True,
    )
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    anonymous_session_id = Column(String(128), nullable=True)
    question = Column(Text, nullable=False)
    language = Column(String(8), nullable=True)
    category = Column(String(64), nullable=True)
    status = Column(String(20), nullable=False, default="open", index=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)


class MedicalTerminologyNormalized(Base):
    __tablename__ = "medical_terminology_normalized"

    id = _uuid_pk()
    term_en = Column(String(256), nullable=True)
    term_ar = Column(String(256), nullable=True)
    term_ar_iq = Column(String(256), nullable=True)
    code = Column(String(64), nullable=True)
    code_system = Column(String(32), nullable=True)
    category = Column(String(64), nullable=True, index=True)
    synonyms = Column(_JSON, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
