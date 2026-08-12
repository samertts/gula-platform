from app._compat import StrEnum


class EmergencyLevel(StrEnum):
    LEVEL_1_MINOR = "level_1_minor"
    LEVEL_2_MODERATE = "level_2_moderate"
    LEVEL_3_MAJOR = "level_3_major"
    LEVEL_4_CATASTROPHIC = "level_4_catastrophic"


class EmergencyStatus(StrEnum):
    STANDBY = "standby"
    ACTIVE = "active"
    DE_ESCALATING = "de_escalating"
    RESOLVED = "resolved"
    POST_INCIDENT = "post_incident"


class EmergencyType(StrEnum):
    NATURAL_DISASTER = "natural_disaster"
    DISEASE_OUTBREAK = "disease_outbreak"
    TERRORIST_INCIDENT = "terrorist_incident"
    MASS_CASUALTY = "mass_casualty"
    INFRASTRUCTURE_FAILURE = "infrastructure_failure"
    CYBER_ATTACK = "cyber_attack"
    CHEMICAL_SPILL = "chemical_spill"
    RADIOLOGICAL = "radiological"
    OTHER = "other"


class CommandRole(StrEnum):
    INCIDENT_COMMANDER = "incident_commander"
    OPERATIONS_CHIEF = "operations_chief"
    LOGISTICS_CHIEF = "logistics_chief"
    PLANNING_CHIEF = "planning_chief"
    FINANCE_CHIEF = "finance_chief"
    MEDICAL_OFFICER = "medical_officer"
    SAFETY_OFFICER = "safety_officer"
    LIAISON_OFFICER = "liaison_officer"
    PUBLIC_INFO_OFFICER = "public_information_officer"


class ResourceType(StrEnum):
    VEHICLE = "vehicle"
    PERSONNEL = "personnel"
    BED = "bed"
    VENTILATOR = "ventilator"
    BLOOD_PRODUCT = "blood_product"
    MEDICATION = "medication"
    EQUIPMENT = "equipment"
    FACILITY = "facility"


class ResourceStatus(StrEnum):
    AVAILABLE = "available"
    DEPLOYED = "deployed"
    DEPLETED = "depleted"
    RESERVED = "reserved"
    RECHARGING = "recharging"
    OFFLINE = "offline"


class CoordinationPriority(StrEnum):
    IMMEDIATE = "immediate"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class OperationalPeriod(StrEnum):
    DAY = "day"
    NIGHT = "night"
    EXTENDED = "extended"
    CONTINUOUS = "continuous"


class AfterActionRating(StrEnum):
    EXCELLENT = "excellent"
    GOOD = "good"
    SATISFACTORY = "satisfactory"
    NEEDS_IMPROVEMENT = "needs_improvement"
    UNACCEPTABLE = "unacceptable"
