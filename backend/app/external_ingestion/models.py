"""Isolated metadata and entity-resolution models for external sources.

These tables intentionally do not contain raw names, phone numbers, national IDs,
passwords, or clinical records. Raw files belong in an independently protected
quarantine object store; the database keeps only bounded metadata and HMAC-based
matching features.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from app._compat import UTC
from app.database import Base


class ExternalSource(Base):
    __tablename__ = "external_ingestion_sources"
    __table_args__ = (
        UniqueConstraint("source_key", name="uq_external_ingestion_source_key"),
        Index("ix_external_ingestion_source_active", "is_enabled", "contract_status"),
        Index("ix_external_ingestion_source_binding", "service_account_id", "is_enabled"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_key = Column(String(80), nullable=False)
    source_kind = Column(String(40), nullable=False)
    display_name = Column(String(200), nullable=False)
    contract_status = Column(String(30), nullable=False, default="pending")
    contract_expires_at = Column(DateTime(timezone=True), nullable=True)
    schema_version = Column(Integer, nullable=False, default=1)
    allowed_fields = Column(JSON, nullable=False, default=list)
    is_enabled = Column(Boolean, nullable=False, default=False)
    service_account_id = Column(Integer, ForeignKey("service_accounts.id", ondelete="RESTRICT"), nullable=True)
    vault_reference = Column(String(240), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    version = Column(Integer, nullable=False, default=1)


class ExternalImportBatch(Base):
    __tablename__ = "external_ingestion_batches"
    __table_args__ = (
        UniqueConstraint("source_id", "idempotency_key", name="uq_external_ingestion_batch_idempotency"),
        UniqueConstraint("source_id", "export_id", "content_sha256", name="uq_external_ingestion_batch_export_digest"),
        Index("ix_external_ingestion_batch_status", "status", "received_at"),
        Index("ix_external_ingestion_batch_source", "source_id", "received_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("external_ingestion_sources.id", ondelete="RESTRICT"), nullable=False)
    export_id = Column(String(160), nullable=False)
    idempotency_key = Column(String(240), nullable=False)
    content_sha256 = Column(String(64), nullable=False)
    object_uri = Column(String(512), nullable=False)
    schema_version = Column(Integer, nullable=False)
    declared_record_count = Column(Integer, nullable=False, default=0)
    status = Column(String(30), nullable=False, default="received")
    received_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    staged_record_count = Column(Integer, nullable=False, default=0)
    rejected_record_count = Column(Integer, nullable=False, default=0)
    review_record_count = Column(Integer, nullable=False, default=0)
    accepted_record_count = Column(Integer, nullable=False, default=0)
    auto_matched_count = Column(Integer, nullable=False, default=0)
    manifest = Column(JSON, nullable=False, default=dict)
    rejection_reason = Column(Text, nullable=True)
    created_by = Column(Integer, nullable=True)
    committed_by = Column(Integer, nullable=True)
    committed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    version = Column(Integer, nullable=False, default=1)


class ExternalProfessionalEntity(Base):
    __tablename__ = "external_professional_entities"
    __table_args__ = (
        UniqueConstraint("entity_key_hmac", name="uq_external_professional_entity_key"),
        Index("ix_external_professional_entity_profession", "profession", "state"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_key_hmac = Column(String(64), nullable=False)
    profession = Column(String(60), nullable=False)
    state = Column(String(30), nullable=False, default="provisional")
    source_count = Column(Integer, nullable=False, default=0)
    gula_account_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    version = Column(Integer, nullable=False, default=1)


class ExternalProfessionalRecord(Base):
    __tablename__ = "external_professional_records"
    __table_args__ = (
        UniqueConstraint("batch_id", "source_record_id_hmac", name="uq_external_professional_record_batch_source_id"),
        Index("ix_external_professional_record_nid", "national_id_hmac"),
        Index("ix_external_professional_record_license", "license_hmac", "profession"),
        Index("ix_external_professional_record_entity", "canonical_entity_id"),
        Index("ix_external_professional_record_resolution", "resolution_status"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(Integer, ForeignKey("external_ingestion_batches.id", ondelete="CASCADE"), nullable=False)
    source_key = Column(String(80), nullable=False)
    source_record_id_hmac = Column(String(64), nullable=False)
    source_record_version = Column(String(80), nullable=True)
    person_ref_hmac = Column(String(64), nullable=False)
    national_id_hmac = Column(String(64), nullable=True)
    license_hmac = Column(String(64), nullable=True)
    license_authority = Column(String(120), nullable=True)
    profession = Column(String(60), nullable=False)
    specialty_hmac = Column(String(64), nullable=True)
    name_hmac = Column(String(64), nullable=False)
    name_tokens_hmac = Column(JSON, nullable=False, default=list)
    phone_hmac = Column(String(64), nullable=True)
    birth_date_hmac = Column(String(64), nullable=True)
    employer_ref_hmac = Column(String(64), nullable=True)
    employment_status = Column(String(40), nullable=True)
    canonical_entity_id = Column(Integer, ForeignKey("external_professional_entities.id", ondelete="RESTRICT"), nullable=True)
    resolution_status = Column(String(30), nullable=False, default="unresolved")
    resolution_method = Column(String(40), nullable=True)
    resolution_score = Column(Integer, nullable=True)
    resolution_features = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    version = Column(Integer, nullable=False, default=1)


class ExternalProfessionalMatchReview(Base):
    __tablename__ = "external_professional_match_reviews"
    __table_args__ = (
        UniqueConstraint("record_id", name="uq_external_professional_match_review_record"),
        Index("ix_external_professional_match_review_status", "status", "created_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(Integer, ForeignKey("external_professional_records.id", ondelete="CASCADE"), nullable=False)
    candidate_entity_id = Column(Integer, ForeignKey("external_professional_entities.id", ondelete="RESTRICT"), nullable=True)
    status = Column(String(30), nullable=False, default="pending")
    reason = Column(Text, nullable=False)
    evidence = Column(JSON, nullable=False, default=dict)
    decided_by = Column(Integer, nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    version = Column(Integer, nullable=False, default=1)
