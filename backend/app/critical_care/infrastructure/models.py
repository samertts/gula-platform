from __future__ import annotations

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text

from app.national.base import TenantAuditEntity, TenantEntity


class ICUAdmissionModel(TenantAuditEntity):
    __tablename__ = "critical_care_admissions"

    patient_id = Column(String(100), nullable=False, index=True)
    patient_name = Column(String(200), nullable=True)
    medical_record_number = Column(String(100), nullable=True)
    icu_type = Column(String(50), default="adult_icu")
    admission_type = Column(String(50), default="emergency")
    admission_source = Column(String(200), nullable=True)
    admission_diagnosis = Column(Text, nullable=True)
    admitting_physician = Column(String(200), nullable=True)
    bed_id = Column(String(100), nullable=True)
    room_id = Column(String(100), nullable=True)
    unit_id = Column(String(100), nullable=True)
    facility_id = Column(String(100), nullable=True)
    status = Column(String(50), default="stable")
    isolation_type = Column(String(50), default="standard")
    isolation_reason = Column(Text, nullable=True)
    admitting_notes = Column(Text, nullable=True)
    primary_problem_list = Column(JSON, nullable=True)
    allergies = Column(JSON, nullable=True)
    code_status = Column(String(50), default="full_code")
    organ_donor_status = Column(Boolean, default=False)
    expected_discharge_date = Column(DateTime(timezone=True), nullable=True)
    discharged_at = Column(DateTime(timezone=True), nullable=True)
    discharge_summary = Column(Text, nullable=True)
    discharge_destination = Column(String(200), nullable=True)
    discharge_reason = Column(String(200), nullable=True)
    readmission_within_48h = Column(Boolean, default=False)


class ICUBedModel(TenantEntity):
    __tablename__ = "critical_care_beds"

    bed_label = Column(String(100), nullable=False)
    room_id = Column(String(100), nullable=True)
    unit_id = Column(String(100), nullable=True)
    facility_id = Column(String(100), nullable=True)
    icu_type = Column(String(50), default="adult_icu")
    is_occupied = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    current_patient_id = Column(String(100), nullable=True)
    current_admission_id = Column(String(100), nullable=True)
    has_ventilator = Column(Boolean, default=False)
    has_monitor = Column(Boolean, default=False)
    has_infusion_pump = Column(Boolean, default=False)
    has_dialysis = Column(Boolean, default=False)
    supported_ventilator_types = Column(JSON, nullable=True)
    last_cleaned_at = Column(DateTime(timezone=True), nullable=True)


class ICUAssessmentModel(TenantAuditEntity):
    __tablename__ = "critical_care_assessments"

    admission_id = Column(String(100), ForeignKey("critical_care_admissions.id"), nullable=True, index=True)
    patient_id = Column(String(100), nullable=True)
    assessment_date = Column(DateTime(timezone=True), nullable=False)
    assessed_by = Column(String(200), nullable=True)
    clinical_assessment = Column(Text, nullable=True)
    respiratory_assessment = Column(Text, nullable=True)
    cardiovascular_assessment = Column(Text, nullable=True)
    neurological_assessment = Column(Text, nullable=True)
    renal_assessment = Column(Text, nullable=True)
    gi_assessment = Column(Text, nullable=True)
    skin_assessment = Column(Text, nullable=True)
    pain_assessment = Column(Text, nullable=True)
    sedation_assessment = Column(Text, nullable=True)
    delirium_assessment = Column(Text, nullable=True)
    mobility_assessment = Column(Text, nullable=True)
    plan = Column(Text, nullable=True)


class VitalSignsRecordModel(TenantEntity):
    __tablename__ = "critical_care_vital_signs"

    patient_id = Column(String(100), nullable=False, index=True)
    admission_id = Column(String(100), ForeignKey("critical_care_admissions.id"), nullable=True)
    recorded_at = Column(DateTime(timezone=True), nullable=False)
    recorded_by = Column(String(200), nullable=True)
    heart_rate = Column(Integer, nullable=True)
    respiratory_rate = Column(Integer, nullable=True)
    systolic_bp = Column(Integer, nullable=True)
    diastolic_bp = Column(Integer, nullable=True)
    mean_arterial_pressure = Column(Float, nullable=True)
    temperature = Column(Float, nullable=True)
    oxygen_saturation = Column(Float, nullable=True)
    fi_o2 = Column(Float, nullable=True)
    pao2 = Column(Float, nullable=True)
    paco2 = Column(Float, nullable=True)
    ph = Column(Float, nullable=True)
    hco3 = Column(Float, nullable=True)
    lactate = Column(Float, nullable=True)
    glucose = Column(Float, nullable=True)
    cvp = Column(Float, nullable=True)
    cardiac_output = Column(Float, nullable=True)
    cardiac_index = Column(Float, nullable=True)
    svr = Column(Float, nullable=True)
    pvr = Column(Float, nullable=True)
    sv_o2 = Column(Float, nullable=True)
    gcs_total = Column(Integer, nullable=True)
    gcs_eye = Column(Integer, nullable=True)
    gcs_verbal = Column(Integer, nullable=True)
    gcs_motor = Column(Integer, nullable=True)
    pupil_right = Column(String(50), nullable=True)
    pupil_left = Column(String(50), nullable=True)
    pain_score = Column(Integer, nullable=True)
    sedation_score = Column(Integer, nullable=True)
    sedation_scale = Column(String(50), default="rass")
    ricam_icu = Column(Boolean, nullable=True)
    notes = Column(Text, nullable=True)


class VentilatorSettingModel(TenantAuditEntity):
    __tablename__ = "critical_care_ventilator_settings"

    patient_id = Column(String(100), nullable=False, index=True)
    admission_id = Column(String(100), ForeignKey("critical_care_admissions.id"), nullable=True)
    setting_time = Column(DateTime(timezone=True), nullable=False)
    set_by = Column(String(200), nullable=True)
    mode = Column(String(50), default="ac")
    ventilator_type = Column(String(50), default="invasive")
    tidal_volume_ml = Column(Integer, nullable=True)
    respiratory_rate_set = Column(Integer, nullable=True)
    respiratory_rate_total = Column(Integer, nullable=True)
    peep_cmh2o = Column(Float, nullable=True)
    pressure_support = Column(Float, nullable=True)
    peak_inspiratory_pressure = Column(Float, nullable=True)
    plateau_pressure = Column(Float, nullable=True)
    mean_airway_pressure = Column(Float, nullable=True)
    fi_o2 = Column(Float, nullable=True)
    inspiratory_time = Column(Float, nullable=True)
    ie_ratio = Column(String(20), nullable=True)
    minute_ventilation = Column(Float, nullable=True)
    static_compliance = Column(Float, nullable=True)
    driving_pressure = Column(Float, nullable=True)
    rsbi = Column(Float, nullable=True)
    etco2 = Column(Float, nullable=True)
    spontaneous_breathing_trials = Column(Boolean, default=False)
    weaning_protocol = Column(String(100), nullable=True)
    sedation_hold = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)


class ContinuousInfusionModel(TenantAuditEntity):
    __tablename__ = "critical_care_infusions"

    patient_id = Column(String(100), nullable=False, index=True)
    admission_id = Column(String(100), ForeignKey("critical_care_admissions.id"), nullable=True)
    medication = Column(String(200), nullable=False)
    medication_dose = Column(String(100), nullable=True)
    rate = Column(String(100), nullable=True)
    rate_units = Column(String(50), default="ml/hr")
    route = Column(String(50), default="iv")
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    initiated_by = Column(String(200), nullable=True)
    pump_id = Column(String(100), nullable=True)
    titrated_to = Column(String(200), nullable=True)
    titration_history = Column(JSON, nullable=True)
    compatible_with = Column(JSON, nullable=True)
    incompatible_with = Column(JSON, nullable=True)
    bag_volume_ml = Column(Float, nullable=True)
    bag_remaining_ml = Column(Float, nullable=True)
    line_type = Column(String(50), default="peripheral")
    line_site = Column(String(100), nullable=True)
    site_assessment = Column(Text, nullable=True)
    is_pca = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    status = Column(String(50), default="active")


class FluidBalanceModel(TenantEntity):
    __tablename__ = "critical_care_fluid_balance"

    patient_id = Column(String(100), nullable=False, index=True)
    admission_id = Column(String(100), ForeignKey("critical_care_admissions.id"), nullable=True)
    recorded_at = Column(DateTime(timezone=True), nullable=False)
    recorded_by = Column(String(200), nullable=True)
    total_intake_ml = Column(Float, default=0.0)
    total_output_ml = Column(Float, default=0.0)
    net_balance_ml = Column(Float, default=0.0)
    cumulative_balance_ml = Column(Float, default=0.0)
    iv_fluids_ml = Column(Float, default=0.0)
    enteral_feeding_ml = Column(Float, default=0.0)
    oral_intake_ml = Column(Float, default=0.0)
    blood_products_ml = Column(Float, default=0.0)
    urine_output_ml = Column(Float, default=0.0)
    stool_output_ml = Column(Float, default=0.0)
    ng_output_ml = Column(Float, default=0.0)
    drain_output_ml = Column(Float, default=0.0)
    estimated_blood_loss_ml = Column(Float, default=0.0)
    insensible_losses_ml = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)


class EarlyWarningScoreModel(TenantEntity):
    __tablename__ = "critical_care_early_warning_scores"

    patient_id = Column(String(100), nullable=False, index=True)
    admission_id = Column(String(100), ForeignKey("critical_care_admissions.id"), nullable=True)
    score_time = Column(DateTime(timezone=True), nullable=False)
    score_system = Column(String(50), default="news2")
    score_value = Column(Integer, default=0)
    heart_rate_score = Column(Integer, default=0)
    respiratory_rate_score = Column(Integer, default=0)
    systolic_bp_score = Column(Integer, default=0)
    temperature_score = Column(Integer, default=0)
    consciousness_score = Column(Integer, default=0)
    oxygen_score = Column(Integer, default=0)
    supplemental_oxygen = Column(Boolean, default=False)
    risk_category = Column(String(50), default="low")
    recommended_frequency = Column(String(50), default="q4h")
    triggers_escalation = Column(Boolean, default=False)
    calculated_by = Column(String(200), nullable=True)


class ICUScoreModel(TenantEntity):
    __tablename__ = "critical_care_scores"

    patient_id = Column(String(100), nullable=False, index=True)
    admission_id = Column(String(100), ForeignKey("critical_care_admissions.id"), nullable=True)
    score_time = Column(DateTime(timezone=True), nullable=False)
    score_type = Column(String(50), nullable=False)
    score_value = Column(Integer, nullable=False)
    score_components = Column(JSON, nullable=True)
    mortality_prediction = Column(Float, nullable=True)
    calculated_by = Column(String(200), nullable=True)


class CriticalAlertModel(TenantEntity):
    __tablename__ = "critical_care_alerts"

    patient_id = Column(String(100), nullable=False, index=True)
    admission_id = Column(String(100), ForeignKey("critical_care_admissions.id"), nullable=True)
    alert_type = Column(String(100), nullable=False)
    severity = Column(String(50), default="warning")
    alert_message = Column(Text, nullable=True)
    alert_time = Column(DateTime(timezone=True), nullable=False)
    triggered_by = Column(String(200), nullable=True)
    parameter = Column(String(100), nullable=True)
    value = Column(String(100), nullable=True)
    threshold = Column(String(100), nullable=True)
    acknowledged_by = Column(String(200), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(200), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    action_taken = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)


class DeviceIntegrationModel(TenantEntity):
    __tablename__ = "critical_care_device_integrations"

    patient_id = Column(String(100), nullable=True)
    admission_id = Column(String(100), nullable=True)
    device_type = Column(String(100), nullable=False)
    device_id = Column(String(100), nullable=False)
    device_name = Column(String(200), nullable=True)
    vendor = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    connectivity = Column(String(50), default="network")
    is_connected = Column(Boolean, default=False)
    last_data_received = Column(DateTime(timezone=True), nullable=True)
    parameters = Column(JSON, nullable=True)
    settings = Column(JSON, nullable=True)
    alerts = Column(JSON, nullable=True)


class DailyChecklistModel(TenantAuditEntity):
    __tablename__ = "critical_care_daily_checklists"

    admission_id = Column(String(100), ForeignKey("critical_care_admissions.id"), nullable=True)
    patient_id = Column(String(100), nullable=True)
    checklist_date = Column(DateTime(timezone=True), nullable=False)
    completed_by = Column(String(200), nullable=True)
    ventilator_bundle = Column(Boolean, default=False)
    central_line_bundle = Column(Boolean, default=False)
    catheter_bundle = Column(Boolean, default=False)
    vte_prophylaxis = Column(Boolean, default=False)
    stress_ulcer_prophylaxis = Column(Boolean, default=False)
    sedation_vacation = Column(Boolean, default=False)
    spontaneous_breathing_trial = Column(Boolean, default=False)
    spontaneous_awakening_trial = Column(Boolean, default=False)
    glucose_control = Column(Boolean, default=False)
    nutrition_assessment = Column(Boolean, default=False)
    mobilization = Column(Boolean, default=False)
    family_communication = Column(Boolean, default=False)
    goals_of_care = Column(Boolean, default=False)
    plan_for_day = Column(Text, nullable=True)
    issues = Column(Text, nullable=True)


class RoundRecordModel(TenantAuditEntity):
    __tablename__ = "critical_care_rounds"

    admission_id = Column(String(100), ForeignKey("critical_care_admissions.id"), nullable=True)
    patient_id = Column(String(100), nullable=True)
    round_date = Column(DateTime(timezone=True), nullable=False)
    attending_physician = Column(String(200), nullable=True)
    team_members = Column(JSON, nullable=True)
    overnight_events = Column(Text, nullable=True)
    review_of_systems = Column(Text, nullable=True)
    assessment = Column(Text, nullable=True)
    plan = Column(Text, nullable=True)
    medications_reviewed = Column(Boolean, default=False)
    imaging_reviewed = Column(Boolean, default=False)
    labs_reviewed = Column(Boolean, default=False)
    microbiology_reviewed = Column(Boolean, default=False)
    follow_up_items = Column(JSON, nullable=True)
