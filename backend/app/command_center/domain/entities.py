from dataclasses import dataclass, field
from typing import Any


@dataclass
class EmergencyDeclaration:
    id: str = ""
    emergency_type: str = ""
    level: str = "level_1_minor"
    status: str = "standby"
    region: str = ""
    district: str = ""
    description: str = ""
    affected_population: int = 0
    declared_by: str = ""
    declared_at: str = ""
    resolved_at: str = ""
    activation_protocol: str = ""
    ic_name: str = ""
    ic_title: str = ""
    ic_phone: str = ""
    command_post_location: str = ""
    operational_period: str = "continuous"
    objectives: list[str] = field(default_factory=list)
    situation_summary: str = ""


@dataclass
class ResourceRequest:
    id: str = ""
    emergency_id: str = ""
    resource_type: str = ""
    quantity: int = 1
    priority: str = "medium"
    status: str = "pending"
    requesting_facility: str = ""
    destination_location: str = ""
    requested_by: str = ""
    requested_at: str = ""
    fulfilled_quantity: int = 0
    fulfilled_by: str = ""
    fulfilled_at: str = ""
    notes: str = ""


@dataclass
class SituationReport:
    id: str = ""
    emergency_id: str = ""
    report_number: int = 1
    operational_period: str = ""
    summary: str = ""
    key_actions: list[dict[str, Any]] = field(default_factory=list)
    resources_deployed: list[dict[str, Any]] = field(default_factory=list)
    casualties: dict[str, int] = field(default_factory=dict)
    challenges: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)
    published_by: str = ""
    published_at: str = ""


@dataclass
class AfterActionReport:
    id: str = ""
    emergency_id: str = ""
    emergency_type: str = ""
    region: str = ""
    incident_duration_hours: int = 0
    overall_rating: str = "satisfactory"
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    response_time_minutes: int = 0
    lives_saved: int = 0
    resources_used: dict[str, Any] = field(default_factory=dict)
    completed_by: str = ""
    completed_at: str = ""


@dataclass
class UnifiedCommandDashboard:
    overall_status: str = "green"
    active_emergencies: int = 0
    active_outbreaks: int = 0
    icus_occupancy_pct: float = 0.0
    ventilators_available: int = 0
    blood_units_available: int = 0
    ambulances_available: int = 0
    ems_incidents_active: int = 0
    critical_alerts_last_24h: int = 0
    beds_available: int = 0
    national_readiness_score: float = 0.0
    response_time_avg_minutes: float = 0.0
    regional_breakdown: dict[str, Any] = field(default_factory=dict)
