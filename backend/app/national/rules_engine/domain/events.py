from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.national.events.base import NationalDomainEvent
from app.national.rules_engine.domain.enums import RuleCategory


@dataclass
class RuleCreatedEvent(NationalDomainEvent):
    event_type: str = "national.rules_engine.rule.created"
    aggregate_type: str = "RuleDefinition"
    rule_id: str = ""
    rule_name: str = ""
    category: RuleCategory | None = None
    rule_version: int = 1


@dataclass
class RuleUpdatedEvent(NationalDomainEvent):
    event_type: str = "national.rules_engine.rule.updated"
    aggregate_type: str = "RuleDefinition"
    rule_id: str = ""
    rule_name: str = ""
    category: RuleCategory | None = None
    rule_version: int = 1
    changes: dict[str, Any] | None = None


@dataclass
class RuleActivatedEvent(NationalDomainEvent):
    event_type: str = "national.rules_engine.rule.activated"
    aggregate_type: str = "RuleDefinition"
    rule_id: str = ""
    rule_name: str = ""


@dataclass
class RuleDeactivatedEvent(NationalDomainEvent):
    event_type: str = "national.rules_engine.rule.deactivated"
    aggregate_type: str = "RuleDefinition"
    rule_id: str = ""
    rule_name: str = ""


@dataclass
class RuleEvaluatedEvent(NationalDomainEvent):
    event_type: str = "national.rules_engine.rule.evaluated"
    aggregate_type: str = "RuleDefinition"
    rule_id: str = ""
    context: dict[str, Any] | None = None
    result: dict[str, Any] | None = None
    trigger: str = ""


@dataclass
class RuleViolationEvent(NationalDomainEvent):
    event_type: str = "national.rules_engine.rule.violation"
    aggregate_type: str = "RuleDefinition"
    rule_id: str = ""
    rule_name: str = ""
    severity: str = ""
    resource_type: str = ""
    resource_id: str = ""
    message: str = ""
    context: dict[str, Any] | None = None


@dataclass
class RuleSimulationEvent(NationalDomainEvent):
    event_type: str = "national.rules_engine.rule.simulation"
    aggregate_type: str = "RuleDefinition"
    rule_id: str = ""
    context: dict[str, Any] | None = None
    result: dict[str, Any] | None = None
    simulated: bool = True
