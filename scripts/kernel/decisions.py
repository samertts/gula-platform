"""Phase 8 — Decision Engine.

Decision registry, history, ownership, confidence, risk, alternatives,
traceability, rollback, and simulation. Builds on the Governor's decision
governance (Phase 3 of GULA-GOVERNOR-001): ownership resolution, voting,
escalation, and rollback are reused — this module adds confidence, risk,
traceability, and simulation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from scripts.governor.decision_governance import (
    Decision,
    approve_decision,
    create_decision,
    rollback_decision,
)

from .core import STATE_DIR, utcnow, write_json

DECISION_HISTORY_FILE = STATE_DIR / "decision_history.json"

CATEGORY_BASE_RISK = {
    "architecture": 0.7,
    "deployment": 0.8,
    "security": 0.9,
    "database": 0.75,
    "general": 0.4,
}


@dataclass
class DecisionRecord:
    """A decision extended with confidence, risk, trace, and simulation."""

    decision: Decision
    confidence: float = 0.5
    risk: float = 0.5
    risk_level: str = "medium"
    trace: list[str] = field(default_factory=list)
    simulated_outcome: str = ""
    simulated_at: str = ""


def compute_confidence(evidence_points: int, alternatives_count: int) -> float:
    """Confidence grows with evidence and considered alternatives (0..1)."""
    base = min(0.8, evidence_points * 0.2)
    alternatives_bonus = min(0.2, alternatives_count * 0.05)
    return round(min(1.0, base + alternatives_bonus), 3)


def compute_risk(category: str, priority: str) -> float:
    """Risk combines category base risk and decision priority."""
    base = CATEGORY_BASE_RISK.get(category.lower(), 0.4)
    priority_boost = {"critical": 0.2, "high": 0.1, "medium": 0.0, "low": -0.1}.get(priority.lower(), 0.0)
    return round(max(0.0, min(1.0, base + priority_boost)), 3)


def risk_level(risk: float) -> str:
    if risk >= 0.8:
        return "high"
    if risk >= 0.5:
        return "medium"
    return "low"


def decide(
    decision_id: str,
    title: str,
    category: str = "general",
    priority: str = "medium",
    context: str = "",
    alternatives: list[str] | None = None,
    rollback_plan: str = "",
    evidence_points: int = 0,
) -> DecisionRecord:
    """Create a decision with computed confidence and risk."""
    decision = create_decision(
        decision_id=decision_id,
        title=title,
        category=category,
        priority=priority,
        context=context,
        alternatives=alternatives or [],
        rollback_plan=rollback_plan,
    )
    confidence = compute_confidence(evidence_points, len(decision.alternatives))
    risk = compute_risk(decision.category, decision.priority)
    return DecisionRecord(
        decision=decision,
        confidence=confidence,
        risk=risk,
        risk_level=risk_level(risk),
        trace=[f"{utcnow()} decided.created {decision_id}"],
    )


def trace(record: DecisionRecord, event: str) -> DecisionRecord:
    record.trace.append(f"{utcnow()} {event}")
    return record


def simulate(record: DecisionRecord, scenario: str = "normal") -> DecisionRecord:
    """Simulate the decision outcome before it is committed.

    The simulation is deterministic: an outcome succeeds when confidence is
    high enough to offset risk, and fails otherwise. A failed simulation must
    stop the mission (Phase 11 rule).
    """
    if (record.risk_level == "high" and record.confidence < 0.6) or (scenario == "adverse" and record.risk > 0.7):
        outcome = "failed"
    else:
        outcome = "succeeded"
    record.simulated_outcome = outcome
    record.simulated_at = utcnow()
    record.trace.append(f"{utcnow()} decision.simulated {scenario}:{outcome}")
    return record


def commit(record: DecisionRecord, approver: str) -> DecisionRecord:
    """Approve and commit a decision through the authority rules."""
    record.decision = approve_decision(record.decision, approver)
    record.trace.append(f"{utcnow()} decision.approved {approver}")
    return record


def rollback(record: DecisionRecord, reason: str) -> DecisionRecord:
    record.decision = rollback_decision(record.decision, reason)
    record.trace.append(f"{utcnow()} decision.rolled_back {reason}")
    return record


def save_history(records: list[DecisionRecord]) -> None:
    payload = {
        "generated_at": utcnow(),
        "decisions": [
            {
                **vars(record.decision),
                "confidence": record.confidence,
                "risk": record.risk,
                "risk_level": record.risk_level,
                "trace": record.trace,
                "simulated_outcome": record.simulated_outcome,
            }
            for record in records
        ],
    }
    write_json(DECISION_HISTORY_FILE, payload)


def load_history() -> list[DecisionRecord]:
    from .core import read_json

    data = read_json(DECISION_HISTORY_FILE)
    records: list[DecisionRecord] = []
    for raw in data.get("decisions", []):
        decision = Decision(**{k: v for k, v in raw.items() if k in vars(Decision())})
        records.append(DecisionRecord(
            decision=decision,
            confidence=raw.get("confidence", 0.5),
            risk=raw.get("risk", 0.5),
            risk_level=raw.get("risk_level", "medium"),
            trace=list(raw.get("trace", [])),
            simulated_outcome=raw.get("simulated_outcome", ""),
        ))
    return records


def export_history_json(records: list[DecisionRecord]) -> str:
    """Serialize decision history for searchability/audit."""
    return json.dumps(
        [{"id": r.decision.decision_id, "title": r.decision.title, "status": r.decision.status,
          "confidence": r.confidence, "risk": r.risk} for r in records],
        indent=2,
    )
