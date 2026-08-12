from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    Float,
    Index,
    Integer,
    SmallInteger,
    String,
)

from app.health_data.base import HealthDataBase


class DimPatient(HealthDataBase):
    __tablename__ = "hd_wh_dim_patient"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    patient_ulid = Column(String(26), nullable=False, unique=True, index=True)
    source_id = Column(Integer, nullable=True)

    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    full_name = Column(String(400), nullable=True)
    gender = Column(String(10), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    age_years = Column(SmallInteger, nullable=True)
    age_group = Column(String(20), nullable=True)

    city = Column(String(100), nullable=True)
    governorate = Column(String(100), nullable=True)
    nationality = Column(String(100), default="Iraqi")

    created_date_id = Column(Integer, nullable=True)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True), nullable=True)
    is_current = Column(Integer, default=1)

    __table_args__ = (
        Index("ix_hd_wh_dim_patient_name", "last_name", "first_name"),
        Index("ix_hd_wh_dim_patient_current", "is_current"),
        Index("ix_hd_wh_dim_patient_region", "governorate"),
        {"extend_existing": True},
    )


class DimDate(HealthDataBase):
    __tablename__ = "hd_wh_dim_date"

    id = Column(Integer, primary_key=True, autoincrement=False)
    full_date = Column(Date, nullable=False, unique=True)
    year = Column(SmallInteger, nullable=False)
    quarter = Column(SmallInteger, nullable=False)
    month = Column(SmallInteger, nullable=False)
    month_name = Column(String(20), nullable=False)
    month_name_ar = Column(String(20), nullable=True)
    week = Column(SmallInteger, nullable=False)
    day = Column(SmallInteger, nullable=False)
    day_of_week = Column(SmallInteger, nullable=False)
    day_name = Column(String(20), nullable=False)
    is_weekend = Column(Integer, default=0)
    is_holiday = Column(Integer, default=0)
    fiscal_year = Column(SmallInteger, nullable=True)
    fiscal_quarter = Column(SmallInteger, nullable=True)

    __table_args__ = (
        Index("ix_hd_wh_dim_date_year", "year"),
        Index("ix_hd_wh_dim_date_month", "year", "month"),
        {"extend_existing": True},
    )


class DimFacility(HealthDataBase):
    __tablename__ = "hd_wh_dim_facility"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    facility_ulid = Column(String(26), nullable=True, unique=True)
    lab_id = Column(Integer, nullable=False, index=True)
    name = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=True)
    facility_type = Column(String(50), nullable=True)
    facility_code = Column(String(50), nullable=True)
    city = Column(String(100), nullable=True)
    governorate = Column(String(100), nullable=True)
    is_active = Column(Integer, default=1)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True), nullable=True)
    is_current = Column(Integer, default=1)

    __table_args__ = (
        Index("ix_hd_wh_dim_facility_type", "facility_type"),
        Index("ix_hd_wh_dim_facility_region", "governorate"),
        {"extend_existing": True},
    )


class DimProvider(HealthDataBase):
    __tablename__ = "hd_wh_dim_provider"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    provider_ulid = Column(String(26), nullable=True, unique=True)
    lab_id = Column(Integer, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    full_name = Column(String(400), nullable=True)
    specialty = Column(String(200), nullable=True)
    role = Column(String(50), nullable=True)
    is_active = Column(Integer, default=1)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True), nullable=True)
    is_current = Column(Integer, default=1)

    __table_args__ = (
        Index("ix_hd_wh_dim_provider_specialty", "specialty"),
        {"extend_existing": True},
    )


class DimLabTest(HealthDataBase):
    __tablename__ = "hd_wh_dim_lab_test"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    test_code = Column(String(50), nullable=False, index=True)
    test_name = Column(String(200), nullable=False)
    test_name_ar = Column(String(200), nullable=True)
    category = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    unit = Column(String(50), nullable=True)
    loinc_code = Column(String(20), nullable=True)
    is_active = Column(Integer, default=1)

    __table_args__ = (
        Index("ix_hd_wh_dim_test_category", "category"),
        {"extend_existing": True},
    )


class FactEncounter(HealthDataBase):
    __tablename__ = "hd_wh_fact_encounter"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    encounter_ulid = Column(String(26), nullable=True, unique=True)
    patient_key = Column(BigInteger, nullable=True, index=True)
    date_key = Column(Integer, nullable=True, index=True)
    facility_key = Column(BigInteger, nullable=True, index=True)
    provider_key = Column(BigInteger, nullable=True, index=True)
    lab_id = Column(Integer, nullable=False, index=True)

    encounter_type = Column(String(50), nullable=True)
    status = Column(String(20), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    diagnosis_count = Column(Integer, default=0)
    procedure_count = Column(Integer, default=0)
    medication_count = Column(Integer, default=0)
    lab_order_count = Column(Integer, default=0)
    is_emergency = Column(Integer, default=0)
    is_readmission = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_hd_wh_fact_encounter_patient", "patient_key"),
        Index("ix_hd_wh_fact_encounter_date", "date_key"),
        Index("ix_hd_wh_fact_encounter_facility", "facility_key"),
        {"extend_existing": True},
    )


class FactLabResult(HealthDataBase):
    __tablename__ = "hd_wh_fact_lab_result"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    result_ulid = Column(String(26), nullable=True, unique=True)
    patient_key = Column(BigInteger, nullable=True, index=True)
    date_key = Column(Integer, nullable=True, index=True)
    facility_key = Column(BigInteger, nullable=True, index=True)
    test_key = Column(BigInteger, nullable=True, index=True)
    provider_key = Column(BigInteger, nullable=True, index=True)
    lab_id = Column(Integer, nullable=False, index=True)
    order_key = Column(BigInteger, nullable=True, index=True)

    value_numeric = Column(Float, nullable=True)
    value_text = Column(String(200), nullable=True)
    flag = Column(String(20), nullable=True)
    is_critical = Column(Integer, default=0)
    is_abnormal = Column(Integer, default=0)

    reference_range_low = Column(Float, nullable=True)
    reference_range_high = Column(Float, nullable=True)
    turnaround_hours = Column(Float, nullable=True)

    performed_at = Column(DateTime(timezone=True), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_hd_wh_fact_result_patient", "patient_key"),
        Index("ix_hd_wh_fact_result_date", "date_key"),
        Index("ix_hd_wh_fact_result_test", "test_key"),
        Index("ix_hd_wh_fact_result_flag", "flag"),
        {"extend_existing": True},
    )


class FactOrder(HealthDataBase):
    __tablename__ = "hd_wh_fact_order"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_ulid = Column(String(26), nullable=True, unique=True)
    patient_key = Column(BigInteger, nullable=True, index=True)
    date_key = Column(Integer, nullable=True, index=True)
    facility_key = Column(BigInteger, nullable=True, index=True)
    provider_key = Column(BigInteger, nullable=True, index=True)
    lab_id = Column(Integer, nullable=False, index=True)

    order_type = Column(String(50), nullable=True)
    status = Column(String(20), nullable=True)
    priority = Column(String(20), nullable=True)
    test_count = Column(Integer, default=0)
    completed_test_count = Column(Integer, default=0)
    turnaround_hours = Column(Float, nullable=True)
    has_critical = Column(Integer, default=0)
    has_abnormal = Column(Integer, default=0)

    ordered_at = Column(DateTime(timezone=True), nullable=True)
    collected_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_hd_wh_fact_order_patient", "patient_key"),
        Index("ix_hd_wh_fact_order_date", "date_key"),
        Index("ix_hd_wh_fact_order_status", "status"),
        {"extend_existing": True},
    )
