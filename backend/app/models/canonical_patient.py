from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import backref, relationship

from app._compat import UTC

from ..database import Base


class CanonicalPatient(Base):
    __tablename__ = "canonical_patients"
    __table_args__ = (
        Index("ix_canonical_patients_nid_hash", "national_id_hash"),
        Index("ix_canonical_patients_name", "full_name"),
        Index("ix_canonical_patients_source", "source_system", "source_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="SET NULL"), nullable=True, index=True)
    national_id_hash = Column(String(255), nullable=True)
    health_id = Column(String(20), nullable=True, index=True)
    full_name = Column(String(300), nullable=False)
    full_name_ar = Column(String(300), nullable=True)
    date_of_birth = Column(DateTime(timezone=True), nullable=True)
    gender = Column(String(1), nullable=True)
    phone = Column(String(30), nullable=True)
    email = Column(String(200), nullable=True)
    address = Column(String(500), nullable=True)
    province = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    blood_type = Column(String(5), nullable=True)
    mpi_score = Column(Float, nullable=True)
    is_verified = Column(Boolean, nullable=True, server_default="false")
    is_deceased = Column(Boolean, nullable=True, server_default="false")
    source_system = Column(String(50), nullable=True)
    source_id = Column(String(100), nullable=True)
    version = Column(Integer, nullable=False, server_default="1")

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    patient_links = relationship("PatientLink", back_populates="canonical", lazy="dynamic")
    citizen_links = relationship("CitizenLink", back_populates="canonical", lazy="dynamic")


class PatientLink(Base):
    __tablename__ = "patient_links"
    __table_args__ = (
        Index("ix_patient_links_patient", "patient_id"),
        Index("ix_patient_links_canonical", "canonical_id"),
        Index("ix_patient_links_method", "linkage_method"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    patient_id = Column(
        Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False,
    )
    canonical_id = Column(
        BigInteger, ForeignKey("canonical_patients.id", ondelete="CASCADE"), nullable=False,
    )
    linkage_method = Column(String(30), nullable=False)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    patient = relationship("Patient", backref=backref("canonical_links", lazy="dynamic"))
    canonical = relationship("CanonicalPatient", back_populates="patient_links")


class CitizenLink(Base):
    __tablename__ = "citizen_links"
    __table_args__ = (
        Index("ix_citizen_links_citizen", "citizen_id"),
        Index("ix_citizen_links_canonical", "canonical_id"),
        Index("ix_citizen_links_method", "linkage_method"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    citizen_id = Column(
        BigInteger, ForeignKey("citizens.id", ondelete="RESTRICT"), nullable=False,
    )
    canonical_id = Column(
        BigInteger, ForeignKey("canonical_patients.id", ondelete="CASCADE"), nullable=False,
    )
    linkage_method = Column(String(30), nullable=False)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    citizen = relationship("Citizen", backref=backref("canonical_links", lazy="dynamic"))
    canonical = relationship("CanonicalPatient", back_populates="citizen_links")
