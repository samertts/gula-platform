"""Core deterministic types for the GULA Intelligent Platform Core.

Nothing here calls a model, a network, or an AI provider.  Every value is
derived from repository content or recorded execution results.
"""
from __future__ import annotations

import dataclasses
import enum
import hashlib
from typing import Any


class Status(str, enum.Enum):
    """Verification status. UNKNOWN is never silently promoted to VERIFIED."""

    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    NOT_STARTED = "NOT_STARTED"
    DEFERRED = "DEFERRED"
    UNKNOWN = "UNKNOWN"


class DetectorState(str, enum.Enum):
    """Why a check produced (or failed to produce) a result.

    The distinction is mandatory: "no findings" from a detector that never ran
    is not evidence of health.
    """

    ABSENT = "DETECTOR_ABSENT"
    NOT_RUN = "DETECTOR_EXISTS_NOT_RUN"
    RAN_CLEAN = "DETECTOR_RAN_NO_FINDINGS"
    RAN_NO_EVIDENCE = "DETECTOR_RAN_EVIDENCE_UNAVAILABLE"
    RAN_FOUND = "DETECTOR_RAN_FOUND_FINDINGS"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class Severity(str, enum.Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"
    P5 = "P5"


class FindingState(str, enum.Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    IN_PROGRESS = "IN_PROGRESS"
    FIXED = "FIXED"
    VERIFIED = "VERIFIED"
    DEFERRED = "DEFERRED"
    WONT_FIX = "WONT_FIX"
    BLOCKED = "BLOCKED"


class Health(str, enum.Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


def stable_id(*parts: str) -> str:
    """A short, deterministic identity for an object or finding occurrence."""
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()
    return digest[:16]


@dataclasses.dataclass(frozen=True)
class Rule:
    """A deterministic detector definition."""

    id: str
    category: str
    severity: Severity
    title: str
    rationale: str
    remediation: str
    verification: str
    architecture_decision_required: bool = False


@dataclasses.dataclass
class Finding:
    """One detected defect occurrence, carrying its own evidence."""

    rule_id: str
    occurrence_id: str
    title: str
    severity: Severity
    category: str
    domain: str
    affected: list[str]
    evidence: str
    detector_state: DetectorState = DetectorState.RAN_FOUND
    state: FindingState = FindingState.OPEN
    blocker: bool = False
    architecture_decision_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        data = dataclasses.asdict(self)
        for key in ("severity", "detector_state", "state"):
            data[key] = getattr(self, key).value
        return data


@dataclasses.dataclass
class CheckResult:
    """The outcome of running one rule, including the not-run cases."""

    rule_id: str
    detector_state: DetectorState
    findings: list[Finding] = dataclasses.field(default_factory=list)
    note: str = ""

    @property
    def status(self) -> Status:
        if self.detector_state is DetectorState.RAN_CLEAN:
            return Status.VERIFIED
        if self.detector_state is DetectorState.RAN_FOUND:
            return Status.FAILED
        if self.detector_state is DetectorState.NOT_APPLICABLE:
            return Status.NOT_STARTED
        if self.detector_state is DetectorState.RAN_NO_EVIDENCE:
            return Status.PARTIALLY_VERIFIED
        return Status.UNKNOWN

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "detector_state": self.detector_state.value,
            "status": self.status.value,
            "findings": [f.to_dict() for f in self.findings],
            "note": self.note,
        }
