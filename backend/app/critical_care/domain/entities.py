from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.critical_care.domain.enums import (
    AdmissionType,
    CriticalAlertSeverity,
    ICUStatus,
    ICUType,
    IsolationType,
    VentilatorMode,
    VentilatorType,
)


@dataclass
class ICUAdmission:
    id: str
    patient_id: str = ""
    patient_name: str = ""
    medical_record_number: str = ""
    icu_type: ICUType = ICUType.ADULT_ICU
    admission_type: AdmissionType = AdmissionType.EMERGENCY
    admission_source: str = ""
    admission_diagnosis: str = ""
    admitting_physician: str = ""
    bed_id: str = ""
    room_id: str = ""
    unit_id: str = ""
    facility_id: str = ""
    status: ICUStatus = ICUStatus.STABLE
    isolation_type: IsolationType = IsolationType.STANDARD
    isolation_reason: str = ""
    admitting_notes: str = ""
    primary_problem_list: list[str] = field(default_factory=list)
    allergies: list[str] = field(default_factory=list)
    code_status: str = "full_code"
    organ_donor_status: bool = False
    admission_note_id: str = ""
    expected_discharge_date: datetime | None = None
    discharged_at: datetime | None = None
    discharge_summary: str = ""
    discharge_destination: str = ""
    discharge_reason: str = ""
    readmission_within_48h: bool = False
    created_by: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def length_of_stay_days(self) -> float | None:
        if self.discharged_at and self.created_at:
            return (self.discharged_at - self.created_at).total_seconds() / 86400
        return None


@dataclass
class ICUBed:
    id: str
    bed_label: str = ""
    room_id: str = ""
    unit_id: str = ""
    facility_id: str = ""
    icu_type: ICUType = ICUType.ADULT_ICU
    is_occupied: bool = False
    is_active: bool = True
    current_patient_id: str = ""
    current_admission_id: str = ""
    has_ventilator: bool = False
    has_monitor: bool = False
    has_infusion_pump: bool = False
    has_dialysis: bool = False
    supported_ventilator_types: list[str] = field(default_factory=list)
    last_cleaned_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ICUAssessment:
    id: str
    admission_id: str = ""
    patient_id: str = ""
    assessment_date: datetime = field(default_factory=lambda: datetime.now(UTC))
    assessed_by: str = ""
    clinical_assessment: str = ""
    respiratory_assessment: str = ""
    cardiovascular_assessment: str = ""
    neurological_assessment: str = ""
    renal_assessment: str = ""
    gi_assessment: str = ""
    skin_assessment: str = ""
    pain_assessment: str = ""
    sedation_assessment: str = ""
    delirium_assessment: str = ""
    mobility_assessment: str = ""
    plan: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class VitalSignsRecord:
    id: str
    patient_id: str = ""
    admission_id: str = ""
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    recorded_by: str = ""
    heart_rate: int | None = None
    respiratory_rate: int | None = None
    systolic_bp: int | None = None
    diastolic_bp: int | None = None
    mean_arterial_pressure: float | None = None
    temperature: float | None = None
    oxygen_saturation: float | None = None
    fi_o2: float | None = None
    pao2: float | None = None
    paco2: float | None = None
    ph: float | None = None
    hco3: float | None = None
    lactate: float | None = None
    glucose: float | None = None
    cvp: float | None = None
    cardiac_output: float | None = None
    cardiac_index: float | None = None
    svr: float | None = None
    pvr: float | None = None
    sv_o2: float | None = None
    gcs_total: int | None = None
    gcs_eye: int | None = None
    gcs_verbal: int | None = None
    gcs_motor: int | None = None
    pupil_right: str = ""
    pupil_left: str = ""
    pain_score: int | None = None
    sedation_score: int | None = None
    sedation_scale: str = "rass"
    ricam_icu: bool | None = None
    notes: str = ""


@dataclass
class VentilatorSetting:
    id: str
    patient_id: str = ""
    admission_id: str = ""
    setting_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    set_by: str = ""
    mode: VentilatorMode = VentilatorMode.ASSIST_CONTROL
    ventilator_type: VentilatorType = VentilatorType.INVASIVE
    tidal_volume_ml: int | None = None
    respiratory_rate_set: int | None = None
    respiratory_rate_total: int | None = None
    peep_cmh2o: float | None = None
    pressure_support: float | None = None
    peak_inspiratory_pressure: float | None = None
    plateau_pressure: float | None = None
    mean_airway_pressure: float | None = None
    fi_o2: float | None = None
    inspiratory_time: float | None = None
    ie_ratio: str = ""
    minute_ventilation: float | None = None
    static_compliance: float | None = None
    driving_pressure: float | None = None
    rsbi: float | None = None
    etco2: float | None = None
    spontaneous_breathing_trials: bool = False
    weaning_protocol: str = ""
    sedation_hold: bool = False
    notes: str = ""


@dataclass
class ContinuousInfusion:
    id: str
    patient_id: str = ""
    admission_id: str = ""
    medication: str = ""
    medication_dose: str = ""
    rate: str = ""
    rate_units: str = "ml/hr"
    route: str = "iv"
    start_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    end_time: datetime | None = None
    initiated_by: str = ""
    pump_id: str = ""
    titrated_to: str = ""
    titration_history: list[dict[str, Any]] = field(default_factory=list)
    compatible_with: list[str] = field(default_factory=list)
    incompatible_with: list[str] = field(default_factory=list)
    bag_volume_ml: float | None = None
    bag_remaining_ml: float | None = None
    line_type: str = "peripheral"
    line_site: str = ""
    site_assessment: str = ""
    is_pca: bool = False
    notes: str = ""
    status: str = "active"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class FluidBalance:
    id: str
    patient_id: str = ""
    admission_id: str = ""
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    recorded_by: str = ""
    total_intake_ml: float = 0.0
    total_output_ml: float = 0.0
    net_balance_ml: float = 0.0
    cumulative_balance_ml: float = 0.0
    iv_fluids_ml: float = 0.0
    enteral_feeding_ml: float = 0.0
    oral_intake_ml: float = 0.0
    blood_products_ml: float = 0.0
    urine_output_ml: float = 0.0
    stool_output_ml: float = 0.0
    ng_output_ml: float = 0.0
    drain_output_ml: float = 0.0
    estimated_blood_loss_ml: float = 0.0
    insensible_losses_ml: float = 0.0
    notes: str = ""


@dataclass
class EarlyWarningScore:
    id: str
    patient_id: str = ""
    admission_id: str = ""
    score_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    score_system: str = "news2"
    score_value: int = 0
    heart_rate_score: int = 0
    respiratory_rate_score: int = 0
    systolic_bp_score: int = 0
    temperature_score: int = 0
    consciousness_score: int = 0
    oxygen_score: int = 0
    supplemental_oxygen: bool = False
    risk_category: str = "low"
    recommended_frequency: str = "q4h"
    triggers_escalation: bool = False
    calculated_by: str = ""


@dataclass
class ICUScore:
    id: str
    patient_id: str = ""
    admission_id: str = ""
    score_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    score_type: str = ""
    score_value: int = 0
    score_components: dict[str, int] = field(default_factory=dict)
    mortality_prediction: float | None = None
    calculated_by: str = ""


@dataclass
class CriticalAlert:
    id: str
    patient_id: str = ""
    admission_id: str = ""
    alert_type: str = ""
    severity: CriticalAlertSeverity = CriticalAlertSeverity.WARNING
    alert_message: str = ""
    alert_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    triggered_by: str = ""
    parameter: str = ""
    value: str = ""
    threshold: str = ""
    acknowledged_by: str = ""
    acknowledged_at: datetime | None = None
    resolved_by: str = ""
    resolved_at: datetime | None = None
    action_taken: str = ""
    is_active: bool = True


@dataclass
class DeviceIntegration:
    id: str
    patient_id: str = ""
    admission_id: str = ""
    device_type: str = ""
    device_id: str = ""
    device_name: str = ""
    vendor: str = ""
    model: str = ""
    connectivity: str = "network"
    is_connected: bool = False
    last_data_received: datetime | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    settings: dict[str, Any] = field(default_factory=dict)
    alerts: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class DailyChecklist:
    id: str
    admission_id: str = ""
    patient_id: str = ""
    checklist_date: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_by: str = ""
    ventilator_bundle: bool = False
    central_line_bundle: bool = False
    catheter_bundle: bool = False
    vte_prophylaxis: bool = False
    stress_ulcer_prophylaxis: bool = False
    sedation_vacation: bool = False
    spontaneous_breathing_trial: bool = False
    spontaneous_awakening_trial: bool = False
    glucose_control: bool = False
    nutrition_assessment: bool = False
    mobilization: bool = False
    family_communication: bool = False
    goals_of_care: bool = False
    plan_for_day: str = ""
    issues: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class RoundRecord:
    id: str
    admission_id: str = ""
    patient_id: str = ""
    round_date: datetime = field(default_factory=lambda: datetime.now(UTC))
    attending_physician: str = ""
    team_members: list[str] = field(default_factory=list)
    overnight_events: str = ""
    review_of_systems: str = ""
    assessment: str = ""
    plan: str = ""
    medications_reviewed: bool = False
    imaging_reviewed: bool = False
    labs_reviewed: bool = False
    microbiology_reviewed: bool = False
    follow_up_items: list[str] = field(default_factory=list)
    created_by: str = ""
