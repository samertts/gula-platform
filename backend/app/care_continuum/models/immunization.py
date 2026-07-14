from app.care_continuum.base import CareContinuumTenantAuditEntity
from app.care_continuum.enums import VaccinationStatus
from sqlalchemy import JSON, Boolean, Column, Date, DateTime, Enum as SAEnum, Float, ForeignKey, Index, Integer, String, Text


class ImmunizationSchedule(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_immunization_schedules"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)
    practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=True, index=True)

    vaccine_name = Column(String(200), nullable=False)
    vaccine_code = Column(String(50), nullable=False, index=True)
    schedule_type = Column(String(50), nullable=False)

    dose_number = Column(Integer, nullable=False)
    total_doses = Column(Integer, nullable=True)
    age_required_months = Column(Integer, nullable=True)
    age_max_months = Column(Integer, nullable=True)

    due_date = Column(Date, nullable=False)
    status = Column(SAEnum(VaccinationStatus), nullable=False, default=VaccinationStatus.SCHEDULED)

    contraindication_id = Column(String(26), ForeignKey("cc_contraindications.id", ondelete="SET NULL"), nullable=True)
    contraindication_note = Column(Text, nullable=True)

    administered_at = Column(DateTime(timezone=True), nullable=True)
    administered_by = Column(String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True)
    administration_facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="SET NULL"), nullable=True)

    lot_number = Column(String(50), nullable=True)
    manufacturer = Column(String(100), nullable=True)
    expiry_date = Column(Date, nullable=True)
    route = Column(String(50), nullable=True)
    site = Column(String(50), nullable=True)
    dosage_ml = Column(Float, nullable=True)

    adverse_event = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_immunization_sched_patient", "patient_id"),
        Index("ix_cc_immunization_sched_vaccine", "vaccine_code"),
        Index("ix_cc_immunization_sched_due", "due_date"),
        Index("ix_cc_immunization_sched_status", "status"),
        Index("ix_cc_immunization_sched_patient_vaccine", "patient_id", "vaccine_code", "dose_number", unique=True),
        {"extend_existing": True},
    )


class VaccinationRecord(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_vaccination_records"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    schedule_id = Column(String(26), ForeignKey("cc_immunization_schedules.id", ondelete="SET NULL"), nullable=True, index=True)

    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)
    administered_by = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=False, index=True)

    vaccine_name = Column(String(200), nullable=False)
    vaccine_code = Column(String(50), nullable=False, index=True)
    dose_number = Column(Integer, nullable=True)
    administration_date = Column(DateTime(timezone=True), nullable=False)

    lot_number = Column(String(50), nullable=True)
    manufacturer = Column(String(100), nullable=True)
    expiry_date = Column(Date, nullable=True)
    route = Column(String(50), nullable=True)
    site = Column(String(50), nullable=True)
    dosage_ml = Column(Float, nullable=True)

    is_booster = Column(Boolean, default=False)
    is_catchup = Column(Boolean, default=False)
    is_emergency = Column(Boolean, default=False)

    informed_consent_obtained = Column(Boolean, default=True)
    contraindications_screened = Column(Boolean, default=True)
    contraindication_found = Column(Boolean, default=False)
    contraindication_details = Column(Text, nullable=True)

    adverse_event = Column(Text, nullable=True)
    adverse_event_reported = Column(Boolean, default=False)
    anaphylaxis_observed = Column(Boolean, default=False)
    observation_period_minutes = Column(Integer, nullable=True)

    vaccine_stock_id = Column(String(26), ForeignKey("cc_vaccine_inventory.id", ondelete="SET NULL"), nullable=True)
    status = Column(SAEnum(VaccinationStatus), nullable=False, default=VaccinationStatus.GIVEN)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_vaccination_patient", "patient_id"),
        Index("ix_cc_vaccination_vaccine", "vaccine_code"),
        Index("ix_cc_vaccination_date", "administration_date"),
        Index("ix_cc_vaccination_schedule", "schedule_id"),
        {"extend_existing": True},
    )


class Contraindication(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_contraindications"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)

    vaccine_code = Column(String(50), nullable=False, index=True)
    vaccine_name = Column(String(200), nullable=True)
    contraindication_type = Column(String(100), nullable=False)

    is_permanent = Column(Boolean, default=False)
    severity = Column(String(50), nullable=False, default="moderate")
    recorded_by = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=False, index=True)
    recorded_at = Column(DateTime(timezone=True), nullable=False)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="SET NULL"), nullable=True)

    condition = Column(Text, nullable=False)
    icd10_code = Column(String(20), nullable=True)
    details = Column(Text, nullable=True)

    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_contraindication_patient", "patient_id"),
        Index("ix_cc_contraindication_vaccine", "vaccine_code"),
        Index("ix_cc_contraindication_active", "is_active"),
        {"extend_existing": True},
    )


class VaccineInventory(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_vaccine_inventory"

    vaccine_code = Column(String(50), nullable=False, index=True)
    vaccine_name = Column(String(200), nullable=False)
    manufacturer = Column(String(100), nullable=True)

    lot_number = Column(String(50), nullable=False, index=True)
    expiry_date = Column(Date, nullable=False)
    quantity_received = Column(Integer, nullable=False, default=0)
    quantity_available = Column(Integer, nullable=False, default=0)
    quantity_administered = Column(Integer, nullable=False, default=0)
    quantity_wasted = Column(Integer, nullable=False, default=0)
    quantity_expired = Column(Integer, nullable=False, default=0)
    quantity_returns = Column(Integer, nullable=False, default=0)
    unit = Column(String(20), default="dose")

    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=False, index=True)
    storage_location = Column(String(100), nullable=True)

    received_date = Column(Date, nullable=True)
    last_inventory_date = Column(Date, nullable=True)
    reorder_level = Column(Integer, nullable=True)
    reorder_quantity = Column(Integer, nullable=True)

    is_available = Column(Boolean, default=True)
    is_quarantined = Column(Boolean, default=False)
    quarantine_reason = Column(Text, nullable=True)

    cold_chain_monitor_id = Column(String(26), ForeignKey("cc_cold_chain_monitors.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_vaccine_inventory_code", "vaccine_code"),
        Index("ix_cc_vaccine_inventory_lot", "lot_number"),
        Index("ix_cc_vaccine_inventory_facility", "facility_id"),
        Index("ix_cc_vaccine_inventory_expiry", "expiry_date"),
        {"extend_existing": True},
    )


class ColdChainMonitor(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_cold_chain_monitors"

    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=False, index=True)
    equipment_type = Column(String(100), nullable=False)
    equipment_name = Column(String(200), nullable=True)
    equipment_identifier = Column(String(100), nullable=True)

    temperature_celsius = Column(Float, nullable=True)
    min_temperature_celsius = Column(Float, nullable=True)
    max_temperature_celsius = Column(Float, nullable=True)
    humidity_percent = Column(Float, nullable=True)

    reading_time = Column(DateTime(timezone=True), nullable=False)
    recorded_by = Column(String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True)

    is_within_range = Column(Boolean, default=True)
    breach_alert = Column(Boolean, default=False)
    breach_duration_minutes = Column(Integer, nullable=True)
    breach_action_taken = Column(Text, nullable=True)

    power_outage = Column(Boolean, default=False)
    generator_running = Column(Boolean, nullable=True)
    alarm_triggered = Column(Boolean, default=False)

    vaccine_codes_affected = Column(JSON, nullable=True)
    stock_affected = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_cold_chain_facility", "facility_id"),
        Index("ix_cc_cold_chain_time", "reading_time"),
        Index("ix_cc_cold_chain_breach", "breach_alert"),
        {"extend_existing": True},
    )


class ReminderSchedule(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_reminder_schedules"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)

    vaccine_code = Column(String(50), nullable=True, index=True)
    due_date = Column(Date, nullable=False)
    reminder_type = Column(String(50), nullable=False)

    channel = Column(String(50), nullable=False)
    recipient_phone = Column(String(20), nullable=True)
    recipient_email = Column(String(255), nullable=True)

    reminder_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    sent_status = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)

    reminder_number = Column(Integer, default=1)
    max_reminders = Column(Integer, default=3)
    next_reminder_date = Column(Date, nullable=True)

    was_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_reminder_patient", "patient_id"),
        Index("ix_cc_reminder_due", "due_date"),
        Index("ix_cc_reminder_sent", "reminder_sent"),
        {"extend_existing": True},
    )
