from __future__ import annotations

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    SmallInteger,
    String,
)

from app.health_data.base import TenantAuditHealthDataEntity


class PatientSummary(TenantAuditHealthDataEntity):
    __tablename__ = "hd_ods_patient_summary"

    patient_id = Column(String(26), nullable=False, index=True)
    patient_ulid = Column(String(26), nullable=True, index=True)

    full_name = Column(String(400), nullable=False)
    gender = Column(String(10), nullable=True)
    age = Column(SmallInteger, nullable=True)
    date_of_birth = Column(String(10), nullable=True)
    total_encounters = Column(Integer, default=0)
    total_orders = Column(Integer, default=0)
    total_results = Column(Integer, default=0)
    last_encounter_date = Column(DateTime(timezone=True), nullable=True)
    last_order_date = Column(DateTime(timezone=True), nullable=True)
    last_result_date = Column(DateTime(timezone=True), nullable=True)
    active_orders = Column(Integer, default=0)
    critical_results = Column(Integer, default=0)

    is_active = Column(Boolean, default=True)
    summary_data = Column(JSON, nullable=True)
    refreshed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_hd_ods_patient_summary_lab", "lab_id", "patient_id", unique=True),
        {"extend_existing": True},
    )


class EncounterSummary(TenantAuditHealthDataEntity):
    __tablename__ = "hd_ods_encounter_summary"

    encounter_id = Column(String(26), nullable=False, index=True)
    patient_id = Column(String(26), nullable=False, index=True)

    encounter_type = Column(String(50), nullable=True)
    status = Column(String(20), nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Integer, nullable=True)

    diagnosis_count = Column(Integer, default=0)
    procedure_count = Column(Integer, default=0)
    medication_count = Column(Integer, default=0)
    lab_order_count = Column(Integer, default=0)
    has_critical_results = Column(Boolean, default=False)

    summary_data = Column(JSON, nullable=True)
    refreshed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_hd_ods_encounter_summary_patient", "patient_id"),
        {"extend_existing": True},
    )


class LabResultSummary(TenantAuditHealthDataEntity):
    __tablename__ = "hd_ods_lab_result_summary"

    result_id = Column(String(26), nullable=False, index=True)
    order_id = Column(String(26), nullable=True, index=True)
    patient_id = Column(String(26), nullable=True, index=True)

    test_code = Column(String(50), nullable=True)
    test_name = Column(String(200), nullable=True)
    value = Column(String(100), nullable=True)
    unit = Column(String(50), nullable=True)
    flag = Column(String(20), nullable=True)
    is_critical = Column(Boolean, default=False)
    is_abnormal = Column(Boolean, default=False)

    reference_range_low = Column(String(50), nullable=True)
    reference_range_high = Column(String(50), nullable=True)

    performed_at = Column(DateTime(timezone=True), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    summary_data = Column(JSON, nullable=True)
    refreshed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_hd_ods_lab_result_summary_order", "order_id"),
        Index("ix_hd_ods_lab_result_summary_patient", "patient_id"),
        {"extend_existing": True},
    )


class OrderSummary(TenantAuditHealthDataEntity):
    __tablename__ = "hd_ods_order_summary"

    order_id = Column(String(26), nullable=False, index=True)
    patient_id = Column(String(26), nullable=False, index=True)

    order_type = Column(String(50), nullable=True)
    status = Column(String(20), nullable=True)
    priority = Column(String(20), nullable=True)
    test_count = Column(Integer, default=0)
    completed_test_count = Column(Integer, default=0)
    pending_test_count = Column(Integer, default=0)
    has_critical = Column(Boolean, default=False)
    has_abnormal = Column(Boolean, default=False)

    ordered_at = Column(DateTime(timezone=True), nullable=True)
    collected_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    turnaround_hours = Column(Float, nullable=True)

    summary_data = Column(JSON, nullable=True)
    refreshed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_hd_ods_order_summary_patient", "patient_id"),
        Index("ix_hd_ods_order_summary_status", "status"),
        {"extend_existing": True},
    )
