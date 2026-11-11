"""SQLAlchemy models for the Medical Ontology Core.

See migration ``20260908_0001_medical_ontology_core.py`` for the table-level
schema rationale and the seeding contract. Models are read-only from a
runtime perspective — writes happen exclusively through
``scripts/seed_medical_ontology.py`` and the (future) physician review
console. Runtime read paths are gated on ``ENABLE_MEDICAL_ONTOLOGY``.
"""

# mypy: ignore-errors
# SQLAlchemy 2.0's Mypy plugin flags legacy-style declarative columns
# ("Can't infer type from ORM mapped expression"). Every existing GULA
# model uses the same legacy style; migrating this one file to Mapped[T]
# in isolation would create style drift with the rest of models/.
# Silencing at file scope keeps the model consistent with the rest of the
# codebase and mirrors the baseline diagnostic count of the sibling models.
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
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import relationship

from ..database import Base

# Portable UUID across PostgreSQL (native UUID) and SQLite (CHAR(32)); the
# actual PG column type is created by the Alembic migration.
_UUID = Uuid(as_uuid=True)
_JSON = JSON


def _uuid_pk() -> Column:
    return Column(_UUID, primary_key=True, default=uuid.uuid4, nullable=False)


class MedicalOntologyConcept(Base):
    __tablename__ = "medical_ontology_concepts"

    id = _uuid_pk()
    concept_key = Column(String(128), nullable=False, unique=True)
    category = Column(String(32), nullable=False, index=True)
    display_en = Column(String(256), nullable=True)
    display_ar = Column(String(256), nullable=True)
    description_en = Column(Text, nullable=True)
    description_ar = Column(Text, nullable=True)
    canonical_unit_key = Column(String(128), nullable=True)
    default_specimen_key = Column(String(128), nullable=True)
    attributes = Column(_JSON, nullable=True)
    status = Column(String(16), nullable=False, default="active", index=True)
    version = Column(Integer, nullable=False, default=1)
    source_provenance = Column(String(256), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    codes = relationship(
        "MedicalOntologyCode",
        backref="concept",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    synonyms = relationship(
        "MedicalOntologySynonym",
        backref="concept",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    reference_ranges = relationship(
        "MedicalOntologyReferenceRange",
        backref="concept",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class MedicalOntologyCode(Base):
    __tablename__ = "medical_ontology_codes"
    __table_args__ = (
        UniqueConstraint(
            "code_system", "code", "concept_id", name="uq_medonto_codes_system_code_concept"
        ),
    )

    id = _uuid_pk()
    concept_id = Column(
        _UUID,
        ForeignKey("medical_ontology_concepts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code_system = Column(String(32), nullable=False)
    code = Column(String(64), nullable=False)
    display = Column(String(256), nullable=True)
    is_primary = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False)


class MedicalOntologySynonym(Base):
    __tablename__ = "medical_ontology_synonyms"
    __table_args__ = (
        UniqueConstraint(
            "concept_id", "term_normalized", "locale", name="uq_medonto_syn_concept_norm_locale"
        ),
    )

    id = _uuid_pk()
    concept_id = Column(
        _UUID,
        ForeignKey("medical_ontology_concepts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    term = Column(String(256), nullable=False)
    term_normalized = Column(String(256), nullable=False, index=True)
    locale = Column(String(16), nullable=False)
    variant = Column(String(24), nullable=True)
    source = Column(String(64), nullable=True)
    confidence = Column(Float, nullable=False, default=1.0)
    created_at = Column(DateTime(timezone=True), nullable=False)


class MedicalOntologyRelation(Base):
    __tablename__ = "medical_ontology_relations"
    __table_args__ = (
        UniqueConstraint(
            "source_concept_id",
            "target_concept_id",
            "relation_type",
            name="uq_medonto_rel_src_tgt_type",
        ),
    )

    id = _uuid_pk()
    source_concept_id = Column(
        _UUID,
        ForeignKey("medical_ontology_concepts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_concept_id = Column(
        _UUID,
        ForeignKey("medical_ontology_concepts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relation_type = Column(String(32), nullable=False, index=True)
    strength = Column(Float, nullable=True)
    provenance = Column(String(128), nullable=True)
    attributes = Column(_JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)


class MedicalOntologyReferenceRange(Base):
    __tablename__ = "medical_ontology_reference_ranges"

    id = _uuid_pk()
    concept_id = Column(
        _UUID,
        ForeignKey("medical_ontology_concepts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    unit_key = Column(String(128), nullable=False)
    age_min_years = Column(Float, nullable=True)
    age_max_years = Column(Float, nullable=True)
    sex = Column(String(8), nullable=False, default="any")
    pregnancy_status = Column(String(24), nullable=False, default="any")
    specimen_key = Column(String(128), nullable=True)
    analyzer = Column(String(64), nullable=True)
    lab_id = Column(
        Integer,
        ForeignKey("labs.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    low = Column(Float, nullable=True)
    high = Column(Float, nullable=True)
    critical_low = Column(Float, nullable=True)
    critical_high = Column(Float, nullable=True)
    severity_bands = Column(_JSON, nullable=True)
    source = Column(String(64), nullable=False)
    source_version = Column(String(64), nullable=True)
    source_url = Column(String(512), nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(16), nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class MedicalOntologyUnitConversion(Base):
    __tablename__ = "medical_ontology_unit_conversions"
    __table_args__ = (
        UniqueConstraint(
            "from_unit_key",
            "to_unit_key",
            "concept_scope_key",
            name="uq_medonto_units_from_to_scope",
        ),
    )

    id = _uuid_pk()
    from_unit_key = Column(String(128), nullable=False)
    to_unit_key = Column(String(128), nullable=False)
    factor = Column(Float, nullable=False)
    offset = Column(Float, nullable=False, default=0.0)
    concept_scope_key = Column(String(128), nullable=True)
    source = Column(String(128), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
