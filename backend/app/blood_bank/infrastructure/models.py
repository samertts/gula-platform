from __future__ import annotations

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
)

from app.national.base import TenantAuditEntity, TenantEntity


class BloodDonorModel(TenantEntity):
    __tablename__ = "blood_bank_donors"

    citizen_id = Column(String(100), nullable=True, index=True)
    national_id = Column(String(100), nullable=True)
    full_name = Column(String(200), nullable=False)
    phone = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    date_of_birth = Column(String(20), nullable=True)
    gender = Column(String(20), nullable=True)
    blood_group = Column(String(20), default="unknown")
    rh_factor = Column(String(20), default="unknown")
    weight_kg = Column(Float, nullable=True)
    height_cm = Column(Float, nullable=True)
    hemoglobin_g_dl = Column(Float, nullable=True)
    status = Column(String(50), default="active")
    total_donations = Column(Integer, default=0)
    total_volume_ml = Column(Float, default=0.0)
    last_donation_date = Column(DateTime(timezone=True), nullable=True)
    next_eligible_date = Column(DateTime(timezone=True), nullable=True)
    is_regular_donor = Column(Boolean, default=False)
    consent_signed = Column(Boolean, default=False)
    consent_date = Column(DateTime(timezone=True), nullable=True)
    emergency_contact = Column(String(200), nullable=True)
    emergency_phone = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=True)


class DonorDeferralModel(TenantEntity):
    __tablename__ = "blood_bank_donor_deferrals"

    donor_id = Column(String(100), ForeignKey("blood_bank_donors.id"), nullable=False, index=True)
    deferral_type = Column(String(50), default="temporary")
    reason = Column(String(100), default="other")
    reason_detail = Column(Text, nullable=True)
    deferral_days = Column(Integer, default=0)
    deferred_from = Column(DateTime(timezone=True), nullable=False)
    deferred_until = Column(DateTime(timezone=True), nullable=True)
    deferred_by = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)


class BloodDonationModel(TenantEntity):
    __tablename__ = "blood_bank_donations"

    donor_id = Column(String(100), ForeignKey("blood_bank_donors.id"), nullable=False, index=True)
    donation_type = Column(String(50), default="whole_blood")
    collection_method = Column(String(50), default="manual")
    status = Column(String(50), default="registered")
    volume_ml = Column(Float, default=450.0)
    collection_site = Column(String(200), nullable=True)
    collection_date = Column(DateTime(timezone=True), nullable=False)
    phlebotomist_id = Column(String(100), nullable=True)
    pulse_before = Column(Integer, nullable=True)
    bp_systolic_before = Column(Integer, nullable=True)
    bp_diastolic_before = Column(Integer, nullable=True)
    temperature_before = Column(Float, nullable=True)
    hemoglobin_pre = Column(Float, nullable=True)
    pulse_after = Column(Integer, nullable=True)
    bp_systolic_after = Column(Integer, nullable=True)
    bp_diastolic_after = Column(Integer, nullable=True)
    adverse_event = Column(Text, nullable=True)
    bag_identifier = Column(String(100), nullable=True, unique=True)
    isbt_128_code = Column(String(100), nullable=True, unique=True)
    barcode = Column(String(100), nullable=True, unique=True)
    notes = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=True)


class ScreeningResultModel(TenantEntity):
    __tablename__ = "blood_bank_screening_results"

    donation_id = Column(String(100), ForeignKey("blood_bank_donations.id"), nullable=False, index=True)
    test = Column(String(50), nullable=False)
    result = Column(String(50), default="pending")
    result_value = Column(String(200), nullable=True)
    analyzer_id = Column(String(100), nullable=True)
    operator_id = Column(String(100), nullable=True)
    test_date = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(String(100), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    kit_lot_number = Column(String(100), nullable=True)
    kit_expiry = Column(String(20), nullable=True)
    notes = Column(Text, nullable=True)


class BloodComponentModel(TenantEntity):
    __tablename__ = "blood_bank_components"

    donation_id = Column(String(100), ForeignKey("blood_bank_donations.id"), nullable=False, index=True)
    component = Column(String(50), default="packed_rbc")
    status = Column(String(50), default="pending_processing")
    volume_ml = Column(Float, nullable=True)
    parent_component_id = Column(String(100), nullable=True)
    bag_identifier = Column(String(100), nullable=True, unique=True)
    isbt_128_code = Column(String(100), nullable=True, unique=True)
    barcode = Column(String(100), nullable=True, unique=True)
    storage_condition = Column(String(50), default="refrigerated")
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    processing_date = Column(DateTime(timezone=True), nullable=True)
    processed_by = Column(String(100), nullable=True)
    leukocyte_reduced = Column(Boolean, default=False)
    irradiated = Column(Boolean, default=False)
    washed = Column(Boolean, default=False)
    pathogen_reduced = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)


class BloodInventoryModel(TenantEntity):
    __tablename__ = "blood_bank_inventory"

    facility_id = Column(String(100), nullable=False, index=True)
    blood_group = Column(String(20), nullable=False)
    rh_factor = Column(String(20), nullable=False)
    component = Column(String(50), nullable=False)
    quantity = Column(Integer, default=0)
    reserved_quantity = Column(Integer, default=0)
    minimum_stock = Column(Integer, default=10)
    critical_threshold = Column(Integer, default=5)
    storage_location = Column(String(200), nullable=True)
    storage_condition = Column(String(50), default="refrigerated")
    last_updated = Column(DateTime(timezone=True), nullable=True)


class BloodUnitModel(TenantEntity):
    __tablename__ = "blood_bank_units"

    component_id = Column(String(100), nullable=True)
    facility_id = Column(String(100), nullable=True)
    blood_group = Column(String(20), nullable=False)
    rh_factor = Column(String(20), nullable=False)
    component = Column(String(50), nullable=False)
    bag_identifier = Column(String(100), nullable=True, unique=True)
    isbt_128_code = Column(String(100), nullable=True, unique=True)
    barcode = Column(String(100), nullable=True, unique=True)
    volume_ml = Column(Float, nullable=True)
    collection_date = Column(DateTime(timezone=True), nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True, index=True)
    donor_id = Column(String(100), nullable=True)
    donor_name = Column(String(200), nullable=True)
    status = Column(String(50), default="available")
    storage_location = Column(String(200), nullable=True)
    location_facility_id = Column(String(100), nullable=True)
    screening_complete = Column(Boolean, default=False)
    processing_complete = Column(Boolean, default=False)
    crossmatch_compatible = Column(String(50), nullable=True)
    issued_to = Column(String(200), nullable=True)
    issued_at = Column(DateTime(timezone=True), nullable=True)
    transfused_at = Column(DateTime(timezone=True), nullable=True)
    discarded_at = Column(DateTime(timezone=True), nullable=True)
    discard_reason = Column(Text, nullable=True)
    recalled = Column(Boolean, default=False)
    recall_reason = Column(Text, nullable=True)


class CrossmatchModel(TenantEntity):
    __tablename__ = "blood_bank_crossmatches"

    patient_id = Column(String(100), nullable=False, index=True)
    patient_name = Column(String(200), nullable=True)
    patient_blood_group = Column(String(20), nullable=True)
    patient_rh_factor = Column(String(20), nullable=True)
    unit_id = Column(String(100), nullable=True)
    unit_identifier = Column(String(100), nullable=True)
    blood_group = Column(String(20), nullable=True)
    crossmatch_type = Column(String(50), default="full")
    status = Column(String(50), default="pending")
    abo_compatible = Column(Boolean, default=False)
    rh_compatible = Column(Boolean, default=False)
    crossmatch_result = Column(String(200), nullable=True)
    performed_by = Column(String(100), nullable=True)
    performed_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(String(100), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)


class TransfusionModel(TenantAuditEntity):
    __tablename__ = "blood_bank_transfusions"

    patient_id = Column(String(100), nullable=False, index=True)
    patient_name = Column(String(200), nullable=True)
    patient_blood_group = Column(String(20), nullable=True)
    patient_rh_factor = Column(String(20), nullable=True)
    medical_record_number = Column(String(100), nullable=True)
    unit_id = Column(String(100), nullable=True)
    unit_identifier = Column(String(100), nullable=True)
    blood_group = Column(String(20), nullable=True)
    component = Column(String(50), nullable=True)
    volume_ml = Column(Float, nullable=True)
    crossmatch_id = Column(String(100), nullable=True)
    ordered_by = Column(String(200), nullable=True)
    order_datetime = Column(DateTime(timezone=True), nullable=True)
    administered_by = Column(String(200), nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    pre_vitals = Column(JSON, nullable=True)
    post_vitals = Column(JSON, nullable=True)
    status = Column(String(50), default="ordered")
    verification_method = Column(String(50), default="manual")
    verified_by = Column(String(200), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    patient_verified = Column(Boolean, default=False)
    unit_verified = Column(Boolean, default=False)
    consent_verified = Column(Boolean, default=False)
    rate_ml_per_hour = Column(Float, nullable=True)
    infusion_pump_id = Column(String(100), nullable=True)
    bedside_verification_complete = Column(Boolean, default=False)
    reaction_occurred = Column(Boolean, default=False)
    reaction_type = Column(String(100), nullable=True)
    reaction_severity = Column(String(50), nullable=True)
    reaction_time = Column(DateTime(timezone=True), nullable=True)
    reaction_description = Column(Text, nullable=True)
    reaction_intervention = Column(Text, nullable=True)
    outcome = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)


class BloodRequestModel(TenantEntity):
    __tablename__ = "blood_bank_requests"

    patient_id = Column(String(100), nullable=False)
    patient_name = Column(String(200), nullable=True)
    medical_record_number = Column(String(100), nullable=True)
    facility_id = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    requested_by = Column(String(200), nullable=True)
    physician_name = Column(String(200), nullable=True)
    blood_group = Column(String(20), nullable=True)
    rh_factor = Column(String(20), nullable=True)
    component = Column(String(50), nullable=True)
    units_requested = Column(Integer, default=1)
    urgency = Column(String(50), default="routine")
    indication = Column(Text, nullable=True)
    crossmatch_required = Column(Boolean, default=True)
    status = Column(String(50), default="pending")
    approved_by = Column(String(200), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    fulfilled_units = Column(Integer, default=0)


class InventoryMovementModel(TenantEntity):
    __tablename__ = "blood_bank_inventory_movements"

    unit_id = Column(String(100), nullable=True)
    facility_id = Column(String(100), nullable=True)
    from_location = Column(String(200), nullable=True)
    to_location = Column(String(200), nullable=True)
    movement_type = Column(String(50), nullable=False)
    performed_by = Column(String(200), nullable=True)
    performed_at = Column(DateTime(timezone=True), nullable=False)
    notes = Column(Text, nullable=True)


class PatientBloodSampleModel(TenantAuditEntity):
    __tablename__ = "blood_bank_patient_samples"

    patient_id = Column(String(100), nullable=False, index=True)
    encounter_id = Column(String(100), nullable=True, index=True)
    facility_id = Column(String(100), nullable=False, index=True)
    specimen_identifier = Column(String(120), nullable=False, unique=True, index=True)
    status = Column(String(40), nullable=False, default="collected", index=True)
    collected_by = Column(String(100), nullable=False)
    collected_at = Column(DateTime(timezone=True), nullable=False)
    received_at = Column(DateTime(timezone=True), nullable=True)
    validated_by = Column(String(100), nullable=True)
    validated_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    rejection_reason = Column(Text, nullable=True)


class BloodReservationModel(TenantAuditEntity):
    __tablename__ = "blood_bank_reservations"

    order_id = Column(String(100), nullable=False, index=True)
    patient_id = Column(String(100), nullable=False, index=True)
    encounter_id = Column(String(100), nullable=True, index=True)
    unit_id = Column(String(100), nullable=False, index=True)
    component_id = Column(String(100), nullable=True)
    facility_id = Column(String(100), nullable=False, index=True)
    requested_by = Column(String(100), nullable=False)
    status = Column(String(40), nullable=False, default="reserved", index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    released_at = Column(DateTime(timezone=True), nullable=True)
    release_reason = Column(Text, nullable=True)


class TransfusionReactionModel(TenantAuditEntity):
    __tablename__ = "blood_bank_reactions"

    patient_id = Column(String(100), nullable=False, index=True)
    transfusion_id = Column(String(100), nullable=False, index=True)
    unit_id = Column(String(100), nullable=False, index=True)
    component_id = Column(String(100), nullable=True)
    encounter_id = Column(String(100), nullable=True)
    facility_id = Column(String(100), nullable=False, index=True)
    reporter_id = Column(String(100), nullable=False)
    status = Column(String(40), nullable=False, default="suspected", index=True)
    severity = Column(String(40), nullable=True)
    symptoms = Column(JSON, nullable=False, default=dict)
    investigation = Column(JSON, nullable=False, default=dict)
    related_sample_ids = Column(JSON, nullable=False, default=list)
    outcome = Column(Text, nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)


class BloodTraceabilityEventModel(TenantAuditEntity):
    __tablename__ = "blood_bank_traceability_events"

    unit_id = Column(String(100), nullable=False, index=True)
    facility_id = Column(String(100), nullable=False, index=True)
    event_type = Column(String(60), nullable=False, index=True)
    object_type = Column(String(60), nullable=False)
    object_id = Column(String(100), nullable=False, index=True)
    actor_id = Column(String(100), nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False, index=True)
    reason = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=False, default=dict)

    # No update/delete API is exposed for this model; history is append-only.
