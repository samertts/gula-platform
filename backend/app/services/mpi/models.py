from __future__ import annotations

"""Master Patient Index — national-layer identity service.

Three tables:
  - Citizen      — canonical identity, one row per real human being (48M scale)
  - IdentityClaim — bridge row from (lab_id, patient_id) → citizen_id

  - MergeAudit   — append-only, hash-chained ledger of identity decisions

Boundary rules (see architecture/FOUNDATION.md §4):
  - Never scoped by lab_id.
  - Raw national IDs never land here — only HMAC-SHA256 hashes via
    backend/app/services/identity.hash_national_id().
  - Rows are never deleted; status transitions (active → merged/deceased).
  - Reads must follow the merged_into_id chain to the surviving record.
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app._compat import UTC

from ...database import Base


class Citizen(Base):
    """Canonical national identity — one row per real person.

    Externally identified by `citizen_ulid` (never by `id`, never by NID).
    """

    __tablename__ = "citizens"
    __table_args__ = (
        # Blocking index for probabilistic matching (name + dob + gender)
        Index("ix_citizens_blocking", "name_blocking_key", "birth_year", "gender"),
        Index("ix_citizens_phone", "phone_last10"),
        Index("ix_citizens_family", "family_id_hash"),
        Index("ix_citizens_merged", "merged_into_id"),
        Index("ix_citizens_status", "status"),
        # Partial unique index on nid_hash is created in the migration
        # (SQLAlchemy's Index() doesn't express WHERE NOT NULL portably).
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    citizen_ulid = Column(String(26), nullable=False, unique=True, index=True)

    # Deterministic identity (strongest signal)
    nid_hash = Column(String(255), nullable=True)  # HMAC via hash_national_id()
    nid_verified = Column(Boolean, nullable=False, default=False)

    # Probabilistic features
    phone_last10 = Column(String(10), nullable=True)  # last 10 digits of E.164
    birth_year = Column(SmallInteger, nullable=True)
    birth_month = Column(SmallInteger, nullable=True)
    birth_day = Column(SmallInteger, nullable=True)
    gender = Column(String(1), nullable=True)  # 'M' / 'F'

    # Name (normalized — never the raw submitted form)
    name_canonical = Column(String(255), nullable=False)
    name_blocking_key = Column(String(20), nullable=False)

    # Family linkage (same hash as Patient.family_id_hash — reuses hash_family_id())
    family_id_hash = Column(String(255), nullable=True)

    # Lifecycle
    merged_into_id = Column(
        BigInteger, ForeignKey("citizens.id", ondelete="RESTRICT"), nullable=True,
    )
    status = Column(String(20), nullable=False, default="active")
    version = Column(Integer, nullable=False, default=1)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Self-reference for merge chain (reads must follow to the survivor)
    merged_into = relationship("Citizen", remote_side=[id], foreign_keys=[merged_into_id])
    claims = relationship("IdentityClaim", back_populates="citizen", lazy="dynamic")

    def canonical(self) -> Citizen:
        """Follow merged_into chain to the surviving citizen.

        Bounded at 10 hops — in practice merges never chain that deep, but we
        never loop forever even on a corrupt chain.
        """
        current = self
        for _ in range(10):
            if current.merged_into_id is None:
                return current
            current = current.merged_into
            if current is None:
                return self  # broken chain — return self to avoid NoneType errors
        return current


class IdentityClaim(Base):
    """Bridge row: LIMS patient (lab_id, patient_id) → canonical citizen.

    Exactly one claim per (lab_id, local_patient_id). Created by
    MPI resolver when the lab first registers a patient.
    """

    __tablename__ = "identity_claims"
    __table_args__ = (
        UniqueConstraint("lab_id", "local_patient_id", name="uq_identity_claims_lab_patient"),
        Index("ix_identity_claims_citizen", "citizen_id"),
        Index("ix_identity_claims_lab_patient", "lab_id", "local_patient_id"),
        Index("ix_identity_claims_method", "match_method"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    citizen_id = Column(BigInteger, ForeignKey("citizens.id", ondelete="RESTRICT"), nullable=False)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False)
    local_patient_id = Column(
        Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False,
    )

    match_method = Column(String(20), nullable=False)
    # 'nid_exact' | 'probabilistic' | 'manual' | 'pending_review'
    match_score = Column(Numeric(4, 3), nullable=True)  # 0.000..1.000 (NULL for nid_exact)
    match_features = Column(JSON, nullable=True)  # per-feature contributions for audit

    claimed_by_user_id = Column(
        Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True,
    )
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    citizen = relationship("Citizen", back_populates="claims")


class MergeAudit(Base):
    """Append-only, hash-chained ledger of identity decisions.

    Never UPDATE or DELETE at the application layer. Each row's entry_hash
    is SHA-256 over (prev_hash || canonical_json(row)). Tampering is
    detectable by re-walking the chain.
    """

    __tablename__ = "mpi_merge_audit"
    __table_args__ = (
        Index("ix_merge_audit_primary", "primary_citizen_id"),
        Index("ix_merge_audit_secondary", "secondary_citizen_id"),
        Index("ix_merge_audit_occurred", "occurred_at"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    event_type = Column(String(20), nullable=False)
    # 'auto_merge' | 'manual_merge' | 'split' | 'reassign' | 'create'

    primary_citizen_id = Column(
        BigInteger, ForeignKey("citizens.id", ondelete="RESTRICT"), nullable=False,
    )
    secondary_citizen_id = Column(
        BigInteger, ForeignKey("citizens.id", ondelete="RESTRICT"), nullable=True,
    )

    match_score = Column(Numeric(4, 3), nullable=True)
    match_features = Column(JSON, nullable=True)
    decision_reason = Column(String(500), nullable=True)

    decided_by_user_id = Column(
        Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True,
    )
    occurred_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # Hash chain
    prev_hash = Column(String(64), nullable=False)  # 64 hex chars
    entry_hash = Column(String(64), nullable=False, unique=True)
