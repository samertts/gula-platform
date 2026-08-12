from dataclasses import dataclass

from app.national.events.base import NationalDomainEvent


@dataclass
class PilotPhaseStarted(NationalDomainEvent):
    event_type: str = "pilot_platform.phase.started"
    pilot_id: str = ""
    module: str = ""
    phase: str = ""
    facilities: list[str] = None


@dataclass
class PilotPhaseCompleted(NationalDomainEvent):
    event_type: str = "pilot_platform.phase.completed"
    pilot_id: str = ""
    module: str = ""
    phase: str = ""
    result: str = ""


@dataclass
class GoNoGoDecision(NationalDomainEvent):
    event_type: str = "pilot_platform.go_no_go.decision"
    pilot_id: str = ""
    module: str = ""
    gate: str = ""
    decision: str = ""
    approved_by: str = ""


@dataclass
class ReadinessAssessmentComplete(NationalDomainEvent):
    event_type: str = "pilot_platform.readiness.complete"
    assessment_id: str = ""
    facility_id: str = ""
    overall_score: float = 0.0
    level: str = ""


@dataclass
class PilotRolledBack(NationalDomainEvent):
    event_type: str = "pilot_platform.rolled_back"
    pilot_id: str = ""
    module: str = ""
    phase: str = ""
    reason: str = ""
