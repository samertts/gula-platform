from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)

from app._compat import UTC

from ..database import Base

MONEY = Numeric(18, 2)


def now_utc() -> datetime:
    return datetime.now(UTC)


class PopularClinic(Base):
    __tablename__ = "popular_clinics"
    __table_args__ = (
        UniqueConstraint(
            "province_id",
            "administrative_unit_code",
            name="uq_popular_clinic_admin_unit",
        ),
        Index("ix_popular_clinics_lab_active", "lab_id", "is_active"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    province_id = Column(Integer, nullable=False, index=True)
    administrative_unit_code = Column(String(64), nullable=False)
    name = Column(String(200), nullable=False)
    address = Column(String(500), nullable=True)
    phone = Column(String(32), nullable=True)
    opening_time = Column(String(5), nullable=False, default="14:00")
    closing_time = Column(String(5), nullable=False, default="18:00")
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now_utc)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=now_utc, onupdate=now_utc)


class ChronicPatientProfile(Base):
    __tablename__ = "popular_chronic_patient_profiles"
    __table_args__ = (
        UniqueConstraint("clinic_id", "patient_id", name="uq_popular_chronic_clinic_patient"),
        Index("ix_popular_chronic_patient_clinic", "clinic_id", "patient_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    clinic_id = Column(Integer, ForeignKey("popular_clinics.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    attending_doctor_id = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    conditions = Column(JSON, nullable=False, default=list)
    notes = Column(Text, nullable=True)
    status = Column(String(24), nullable=False, default="active", index=True)
    enrolled_at = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now_utc)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=now_utc, onupdate=now_utc)


class TreatmentPlan(Base):
    __tablename__ = "popular_treatment_plans"
    __table_args__ = (
        Index("ix_popular_treatment_patient_status", "patient_profile_id", "status"),
        CheckConstraint("quantity > 0", name="ck_popular_treatment_quantity_positive"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_profile_id = Column(
        Integer,
        ForeignKey("popular_chronic_patient_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    prescribed_by_id = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    medication_name = Column(String(255), nullable=False)
    medication_code = Column(String(128), nullable=True)
    quantity = Column(Integer, nullable=False)
    dosage = Column(String(255), nullable=False)
    instructions = Column(Text, nullable=True)
    status = Column(String(24), nullable=False, default="active", index=True)
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now_utc)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=now_utc, onupdate=now_utc)


class MonthlyDispensation(Base):
    __tablename__ = "popular_monthly_dispensations"
    __table_args__ = (
        UniqueConstraint(
            "clinic_id",
            "patient_id",
            "dispense_year",
            "dispense_month",
            name="uq_popular_monthly_dispense_once",
        ),
        Index("ix_popular_dispensation_clinic_month", "clinic_id", "dispense_year", "dispense_month"),
        CheckConstraint("dispense_month >= 1 AND dispense_month <= 12", name="ck_popular_dispense_month"),
        CheckConstraint("quantity > 0", name="ck_popular_dispense_quantity_positive"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    clinic_id = Column(Integer, ForeignKey("popular_clinics.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    treatment_plan_id = Column(Integer, ForeignKey("popular_treatment_plans.id", ondelete="SET NULL"), nullable=True)
    approved_by_id = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    dispensed_by_id = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    dispense_year = Column(Integer, nullable=False)
    dispense_month = Column(Integer, nullable=False)
    dispensed_at = Column(DateTime(timezone=True), nullable=False, default=now_utc)
    medication_name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    dosage = Column(String(255), nullable=False)
    blood_pressure = Column(String(64), nullable=True)
    blood_tests = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(24), nullable=False, default="dispensed", index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now_utc)


class PopularServiceCatalog(Base):
    __tablename__ = "popular_service_catalog"
    __table_args__ = (
        UniqueConstraint("clinic_id", "service_code", name="uq_popular_service_code"),
        CheckConstraint("price_cash >= 0 AND price_electronic >= 0", name="ck_popular_service_prices"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    clinic_id = Column(Integer, ForeignKey("popular_clinics.id", ondelete="CASCADE"), nullable=False)
    service_code = Column(String(64), nullable=False)
    name = Column(String(200), nullable=False)
    category = Column(String(64), nullable=False)
    price_cash = Column(MONEY, nullable=False, default=Decimal("0.00"))
    price_electronic = Column(MONEY, nullable=False, default=Decimal("0.00"))
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now_utc)


class PopularServiceVisit(Base):
    __tablename__ = "popular_service_visits"
    __table_args__ = (Index("ix_popular_service_visit_patient", "clinic_id", "patient_id", "created_at"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    clinic_id = Column(Integer, ForeignKey("popular_clinics.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=True)
    service_id = Column(Integer, ForeignKey("popular_service_catalog.id", ondelete="RESTRICT"), nullable=False)
    provider_id = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    report = Column(JSON, nullable=True)
    status = Column(String(24), nullable=False, default="completed", index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now_utc)


class PopularClinicalRecord(Base):
    __tablename__ = "popular_clinical_records"
    __table_args__ = (Index("ix_popular_clinical_record_patient", "clinic_id", "patient_id", "created_at"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    clinic_id = Column(Integer, ForeignKey("popular_clinics.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    record_type = Column(String(64), nullable=False)
    payload = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now_utc)


class PopularClinicTicket(Base):
    __tablename__ = "popular_clinic_tickets"
    __table_args__ = (
        UniqueConstraint("clinic_id", "ticket_number", name="uq_popular_ticket_number"),
        Index("ix_popular_ticket_clinic_status", "clinic_id", "status"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    clinic_id = Column(Integer, ForeignKey("popular_clinics.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="SET NULL"), nullable=True)
    ticket_number = Column(String(64), nullable=False)
    service_code = Column(String(64), nullable=False)
    payment_method = Column(String(24), nullable=False)
    amount = Column(MONEY, nullable=False)
    payment_invoice_id = Column(String(36), nullable=True, index=True)
    payment_intent_id = Column(String(36), nullable=True, index=True)
    issued_by_id = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    captured_by_id = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    cash_shift_id = Column(String(36), nullable=True, index=True)
    payment_reference = Column(String(128), nullable=True)
    status = Column(String(24), nullable=False, default="payment_pending", index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now_utc)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)


class PopularClinicWorker(Base):
    __tablename__ = "popular_clinic_workers"
    __table_args__ = (
        UniqueConstraint("clinic_id", "user_id", "worker_role", name="uq_popular_clinic_worker_role"),
        Index("ix_popular_clinic_worker_active", "clinic_id", "active"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    clinic_id = Column(Integer, ForeignKey("popular_clinics.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("lab_users.id", ondelete="CASCADE"), nullable=False)
    worker_role = Column(String(64), nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    starts_on = Column(Date, nullable=False)
    ends_on = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now_utc)
