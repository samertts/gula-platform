from __future__ import annotations

from enum import Enum


class ICUType(Enum):
    ADULT_ICU = "adult_icu"
    NEONATAL_ICU = "nicu"
    PEDIATRIC_ICU = "picu"
    CARDIAC_ICU = "ccu"
    BURN_ICU = "burn_icu"
    NEURO_ICU = "neuro_icu"
    SURGICAL_ICU = "surgical_icu"
    MEDICAL_ICU = "medical_icu"
    TRAUMA_ICU = "trauma_icu"
    HIGH_DEPENDENCY = "hdu"
    STEP_DOWN = "step_down"


class AdmissionType(Enum):
    EMERGENCY = "emergency"
    ELECTIVE = "elective"
    TRANSFER = "transfer"


class ICUStatus(Enum):
    STABLE = "stable"
    IMPROVING = "improving"
    DETERIORATING = "deteriorating"
    CRITICAL = "critical"
    DISCHARGED = "discharged"
    TRANSFERRED = "transferred"
    DECEASED = "deceased"


class VentilatorMode(Enum):
    ASSIST_CONTROL = "ac"
    SIMV = "simv"
    PSV = "psv"
    CPAP = "cpap"
    BIPAP = "bipap"
    APRV = "aprv"
    HFOV = "hfov"
    PRVC = "prvc"
    NIV = "niv"
    SPONTANEOUS = "spontaneous"


class VentilatorType(Enum):
    INVASIVE = "invasive"
    NON_INVASIVE = "non_invasive"
    HIGH_FREQUENCY = "high_frequency"


class OxygenDevice(Enum):
    NASAL_CANNULA = "nasal_cannula"
    SIMPLE_MASK = "simple_mask"
    NON_REBREATHER = "non_rebreather"
    VENTURI_MASK = "venturi_mask"
    HIGH_FLOW_NASAL = "high_flow_nasal"
    CPAP = "cpap"
    BIPAP = "bipap"
    MECHANICAL_VENTILATOR = "mechanical_ventilator"


class HemodynamicMonitor(Enum):
    ARTERIAL_LINE = "arterial_line"
    CENTRAL_VENOUS = "central_venous"
    PULMONARY_ARTERY = "pulmonary_artery"
    PICCO = "picco"
    LIDCO = "lidco"
    FLOTRAC = "flotrac"
    NICOM = "nicom"
    NIBP = "nibp"


class SedationScale(Enum):
    RASS = "rass"
    SAS = "sas"
    RAMSAY = "ramsay"


class DeliriumScale(Enum):
    CAM_ICU = "cam_icu"
    ICDSC = "icdsc"


class PainScale(Enum):
    CPOT = "cpot"
    NRS = "nrs"
    FLACC = "flacc"
    COMFORT_B = "comfort_b"
    NIPS = "nips"
    CRIES = "cries"


class OrganFailure(Enum):
    CARDIOVASCULAR = "cardiovascular"
    RESPIRATORY = "respiratory"
    RENAL = "renal"
    HEPATIC = "hepatic"
    COAGULATION = "coagulation"
    NEUROLOGICAL = "neurological"


class RenalReplacementType(Enum):
    CONTINUOUS = "crrt"
    SUSTAINED_LOW_EFFICIENCY = "sled"
    INTERMITTENT_HEMODIALYSIS = "ihd"
    PERITONEAL_DIALYSIS = "pd"


class NutritionRoute(Enum):
    ENTERAL = "enteral"
    PARENTERAL = "parenteral"
    ORAL = "oral"
    COMBINED = "combined"


class MonitoringFrequency(Enum):
    CONTINUOUS = "continuous"
    EVERY_15_MIN = "q15min"
    EVERY_30_MIN = "q30min"
    EVERY_1_HOUR = "q1h"
    EVERY_2_HOURS = "q2h"
    EVERY_4_HOURS = "q4h"
    EVERY_8_HOURS = "q8h"
    EVERY_12_HOURS = "q12h"
    DAILY = "daily"


class CriticalAlertSeverity(Enum):
    INFORMATION = "information"
    WARNING = "warning"
    CRITICAL = "critical"
    LIFE_THREATENING = "life_threatening"


class IsolationType(Enum):
    STANDARD = "standard"
    CONTACT = "contact"
    DROPLET = "droplet"
    AIRBORNE = "airborne"
    PROTECTIVE = "protective"
    STRICT = "strict"
