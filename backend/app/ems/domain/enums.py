from __future__ import annotations

from enum import Enum


class IncidentCategory(Enum):
    MEDICAL = "medical"
    TRAUMA = "trauma"
    CARDIAC = "cardiac"
    STROKE = "stroke"
    RESPIRATORY = "respiratory"
    OBSTETRIC = "obstetric"
    PEDIATRIC = "pediatric"
    PSYCHIATRIC = "psychiatric"
    OVERDOSE = "overdose"
    BURN = "burn"
    DROWNING = "drowning"
    ELECTROCUTION = "electrocution"
    MASS_CASUALTY = "mass_casualty"
    DISASTER = "disaster"
    OTHER = "other"


class IncidentPriority(Enum):
    ALPHA = "alpha"
    BRAVO = "bravo"
    CHARLIE = "charlie"
    DELTA = "delta"
    ECHO = "echo"


class IncidentStatus(Enum):
    PENDING = "pending"
    DISPATCHED = "dispatched"
    EN_ROUTE = "en_route"
    ON_SCENE = "on_scene"
    TRANSPORTING = "transporting"
    AT_DESTINATION = "at_destination"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    CLOSED = "closed"
    ENTERED_IN_ERROR = "entered_in_error"


class DispatchStatus(Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    ACKNOWLEDGED = "acknowledged"
    EN_ROUTE = "en_route"
    ON_SCENE = "on_scene"
    TRANSPORTING = "transporting"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AmbulanceStatus(Enum):
    AVAILABLE = "available"
    EN_ROUTE = "en_route"
    ON_SCENE = "on_scene"
    TRANSPORTING = "transporting"
    AT_HOSPITAL = "at_hospital"
    OUT_OF_SERVICE = "out_of_service"
    MAINTENANCE = "maintenance"
    STANDBY = "standby"


class AmbulanceType(Enum):
    BASIC_LIFE_SUPPORT = "bls"
    ADVANCED_LIFE_SUPPORT = "als"
    MOBILE_ICU = "mobile_icu"
    AMBULANCE_BUS = "ambulance_bus"
    AIR_AMBULANCE = "air_ambulance"
    RAPID_RESPONSE = "rapid_response"
    PATIENT_TRANSPORT = "patient_transport"
    COMMAND = "command"


class VehicleStatus(Enum):
    ACTIVE = "active"
    IN_MAINTENANCE = "in_maintenance"
    DECOMMISSIONED = "decommissioned"
    RESERVE = "reserve"


class CrewRole(Enum):
    PARAMEDIC = "paramedic"
    EMERGENCY_MEDICAL_TECHNICIAN = "emt"
    ADVANCED_EMT = "aemt"
    CRITICAL_CARE_PARAMEDIC = "cc_paramedic"
    EMERGENCY_PHYSICIAN = "emergency_physician"
    NURSE = "nurse"
    DRIVER = "driver"
    DISPATCHER = "dispatcher"
    COMMANDER = "commander"
    FIRST_RESPONDER = "first_responder"
    VOLUNTEER = "volunteer"


class ShiftStatus(Enum):
    SCHEDULED = "scheduled"
    CHECKED_IN = "checked_in"
    ON_DUTY = "on_duty"
    ON_BREAK = "on_break"
    OFF_DUTY = "off_duty"
    CANCELLED = "cancelled"


class TriageCategory(Enum):
    IMMEDIATE = "immediate"
    DELAYED = "delayed"
    MINOR = "minor"
    EXPECTANT = "expectant"
    DECEASED = "deceased"


class TriageSystem(Enum):
    START = "start"
    JUMP_START = "jump_start"
    SMART = "smart"
    SALT = "salt"
    MASS = "mass"
    CBRN = "cbrn"


class DisasterType(Enum):
    EARTHQUAKE = "earthquake"
    FLOOD = "flood"
    FIRE = "fire"
    EXPLOSION = "explosion"
    TERRORIST_ATTACK = "terrorist_attack"
    CHEMICAL = "chemical"
    BIOLOGICAL = "biological"
    RADIOLOGICAL = "radiological"
    NUCLEAR = "nuclear"
    TRANSPORTATION = "transportation"
    INDUSTRIAL = "industrial"
    PANDEMIC = "pandemic"
    CONFLICT = "conflict"
    OTHER = "other"


class DisasterPhase(Enum):
    PREPARATION = "preparation"
    RESPONSE = "response"
    RECOVERY = "recovery"
    MITIGATION = "mitigation"
    CLOSED = "closed"


class IncidentCommandRole(Enum):
    INCIDENT_COMMANDER = "incident_commander"
    OPERATIONS_CHIEF = "operations_chief"
    PLANNING_CHIEF = "planning_chief"
    LOGISTICS_CHIEF = "logistics_chief"
    FINANCE_CHIEF = "finance_chief"
    SAFETY_OFFICER = "safety_officer"
    LIAISON_OFFICER = "liaison_officer"
    PUBLIC_INFORMATION = "public_information"
    MEDICAL_DIRECTOR = "medical_director"


class DestinationType(Enum):
    EMERGENCY_DEPARTMENT = "emergency_department"
    TRAUMA_CENTER = "trauma_center"
    BURN_CENTER = "burn_center"
    STROKE_CENTER = "stroke_center"
    CATH_LAB = "cath_lab"
    PRIMARY_CARE = "primary_care"
    OTHER = "other"


class HospitalCapability(Enum):
    LEVEL_1_TRAUMA = "level_1_trauma"
    LEVEL_2_TRAUMA = "level_2_trauma"
    LEVEL_3_TRAUMA = "level_3_trauma"
    STROKE_CENTER = "stroke_center"
    STEMI_CENTER = "stemi_center"
    BURN_CENTER = "burn_center"
    PEDIATRIC = "pediatric"
    MATERNITY = "maternity"
    PSYCHIATRIC = "psychiatric"
    GENERAL = "general"
