from dataclasses import dataclass, field
from typing import Any


@dataclass
class PilotProgram:
    id: str = ""
    module_name: str = ""
    module_path: str = ""
    version: str = ""
    current_phase: str = "planned"
    status: str = "planned"
    strategy: str = "canary"
    pilot_lead: str = ""
    technical_lead: str = ""
    clinical_lead: str = ""
    start_date: str = ""
    target_completion: str = ""
    completed_at: str = ""
    description: str = ""
    phases: list[dict[str, Any]] = field(default_factory=list)
    facilities: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class PilotFacility:
    id: str = ""
    pilot_id: str = ""
    facility_id: str = ""
    facility_name: str = ""
    phase: str = ""
    readiness_level: str = "not_ready"
    readiness_score: float = 0.0
    enrolled_at: str = ""
    completed_at: str = ""
    go_no_go_approved: bool = False
    issues: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ReadinessChecklist:
    id: str = ""
    pilot_id: str = ""
    facility_id: str = ""
    items: list[dict[str, Any]] = field(default_factory=list)
    overall_score: float = 0.0
    level: str = "not_ready"
    assessed_by: str = ""
    assessed_at: str = ""


@dataclass
class GoNoGoGate:
    id: str = ""
    pilot_id: str = ""
    facility_id: str = ""
    gate_name: str = ""
    result: str = "not_run"
    certification_level: str = ""
    metrics: dict[str, Any] = field(default_factory=dict)
    approver: str = ""
    decided_at: str = ""
    comments: str = ""


@dataclass
class DeploymentRecord:
    id: str = ""
    pilot_id: str = ""
    module: str = ""
    version: str = ""
    facility_id: str = ""
    strategy: str = ""
    status: str = "pending"
    deployed_at: str = ""
    deployed_by: str = ""
    health_check_passed: bool = False
    rollback_at: str = ""
    rollback_reason: str = ""
    notes: str = ""
