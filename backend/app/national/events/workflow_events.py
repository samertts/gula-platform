from dataclasses import dataclass

from app.national.events.base import NationalDomainEvent


@dataclass
class WorkflowStarted(NationalDomainEvent):
    event_type: str = "national.workflow.started"
    aggregate_type: str = "Workflow"


@dataclass
class WorkflowStepCompleted(NationalDomainEvent):
    event_type: str = "national.workflow.step_completed"
    aggregate_type: str = "Workflow"


@dataclass
class WorkflowCompleted(NationalDomainEvent):
    event_type: str = "national.workflow.completed"
    aggregate_type: str = "Workflow"


@dataclass
class WorkflowFailed(NationalDomainEvent):
    event_type: str = "national.workflow.failed"
    aggregate_type: str = "Workflow"


@dataclass
class WorkflowCompensated(NationalDomainEvent):
    event_type: str = "national.workflow.compensated"
    aggregate_type: str = "Workflow"
