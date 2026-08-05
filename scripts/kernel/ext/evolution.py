"""GULA-KERNEL-EXT-001 Phase 8 — Continuous Evolution System.

Detect repeated fixes, bugs, and decisions; propose constitution-compliant
improvements only through the RFC-before-KUP workflow
(.ai/core/kup/RFC_WORKFLOW.md). Signals become RFC proposals with
evidence; proposals are tracked through open/accepted/rejected and are
never applied directly — no bypass of the RFC gate.

Reuses self-governance review semantics (scripts/governor/self_governance.
py); no I/O at import time.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..core import utcnow

EVOLUTION_DIR = ".ai/core/evolution/"

SIGNAL_KINDS = ("repeated_fix", "repeated_bug", "repeated_decision", "stagnation")
PROPOSAL_STATES = ("open", "accepted", "rejected", "archived")


class EvolutionError(Exception):
    """Raised for invalid evolution operations."""


@dataclass
class EvolutionSignal:
    """A detected pattern that may justify an RFC proposal."""

    id: str
    kind: str
    area: str
    evidence: list[str] = field(default_factory=list)
    count: int = 1
    severity: str = "low"
    detected_at: str = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        if not self.id.startswith("EVO-"):
            raise EvolutionError(f"signal id must start with EVO-: {self.id!r}")
        if self.kind not in SIGNAL_KINDS:
            raise EvolutionError(f"unknown signal kind: {self.kind!r}")
        if self.count < 1:
            raise EvolutionError("signal count must be positive")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "area": self.area,
            "evidence": list(self.evidence),
            "count": self.count,
            "severity": self.severity,
            "detected_at": self.detected_at,
        }


@dataclass
class RfcProposal:
    """An RFC proposal derived from a detected signal."""

    id: str
    signal_id: str
    title: str
    rationale: str
    status: str = "open"
    created_at: str = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        if not self.id.startswith("RFC-"):
            raise EvolutionError(f"rfc id must start with RFC-: {self.id!r}")
        if self.status not in PROPOSAL_STATES:
            raise EvolutionError(f"unknown proposal state: {self.status!r}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "signal_id": self.signal_id,
            "title": self.title,
            "rationale": self.rationale,
            "status": self.status,
            "created_at": self.created_at,
        }


class EvolutionEngine:
    """Tracks observations, detects signals, and gates RFC proposals."""

    def __init__(self, threshold: int = 3) -> None:
        self._threshold = threshold
        self._observations: dict[tuple[str, str], list[str]] = {}
        self._signals: dict[str, EvolutionSignal] = {}
        self._proposals: dict[str, RfcProposal] = {}
        self._history: list[dict[str, Any]] = []

    def record(self, kind: str, area: str, evidence: str = "") -> None:
        self._observations.setdefault((kind, area), []).append(evidence or utcnow())
        self._history.append({"event": "observed", "kind": kind, "area": area, "at": utcnow()})

    def detect(self) -> list[EvolutionSignal]:
        """Return signals whose observation count meets the threshold."""
        for (kind, area), events in self._observations.items():
            count = len(events)
            if count < self._threshold:
                continue
            signal_id = f"EVO-{abs(hash((kind, area))) % 1000000:06d}"
            if signal_id in self._signals:
                continue
            self._signals[signal_id] = EvolutionSignal(
                id=signal_id,
                kind=kind,
                area=area,
                evidence=events[-3:],
                count=count,
                severity="medium" if count >= self._threshold * 2 else "low",
            )
        return list(self._signals.values())

    def signals(self, kind: str | None = None) -> list[EvolutionSignal]:
        if kind is None:
            return list(self._signals.values())
        return [s for s in self._signals.values() if s.kind == kind]

    def propose(self, signal_id: str, title: str, rationale: str) -> RfcProposal:
        if signal_id not in self._signals:
            raise EvolutionError(f"unknown signal: {signal_id}")
        signal = self._signals[signal_id]
        rfc_id = f"RFC-{signal.id.split('-')[1]}"
        if rfc_id in self._proposals:
            raise EvolutionError(f"proposal already exists: {rfc_id}")
        proposal = RfcProposal(rfc_id, signal_id, title, rationale)
        self._proposals[rfc_id] = proposal
        self._history.append({"event": "proposed", "id": rfc_id, "signal": signal_id, "at": utcnow()})
        return proposal

    def decide(self, rfc_id: str, verdict: str) -> RfcProposal:
        try:
            proposal = self._proposals[rfc_id]
        except KeyError:
            raise EvolutionError(f"unknown proposal: {rfc_id}") from None
        if verdict not in {"accepted", "rejected"}:
            raise EvolutionError(f"verdict must be accepted or rejected: {verdict!r}")
        proposal.status = verdict
        self._history.append({"event": f"{verdict}", "id": rfc_id, "at": utcnow()})
        return proposal

    def proposals(self, status: str | None = None) -> list[RfcProposal]:
        if status is None:
            return list(self._proposals.values())
        return [p for p in self._proposals.values() if p.status == status]

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0.0",
            "threshold": self._threshold,
            "signals": [s.to_dict() for s in self._signals.values()],
            "proposals": [p.to_dict() for p in self._proposals.values()],
            "history": list(self._history),
        }

    def save(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.snapshot(), indent=2) + "\n", encoding="utf-8")
        return path
