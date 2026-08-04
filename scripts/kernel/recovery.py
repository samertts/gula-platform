"""Phase 14 — Failure Recovery.

Support retry, resume, checkpoint, rollback, recovery, escalation, human
approval, failure classification, and incident recording. Builds on the
Governor's checkpoint system (Phase 7) without duplicating it.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from scripts.governor.loop_protection import LoopCounters
from scripts.governor.resource_governor import create_checkpoint, resume_checkpoint

from .core import STATE_DIR, read_json, utcnow, write_json

INCIDENTS_FILE = STATE_DIR / "incidents.json"

# Classifying signals found in exception messages.
_CLASSIFIER_KEYWORDS: dict[str, tuple[str, ...]] = {
    "transient": ("timeout", "temporarily", "connection reset", "econnreset", "5xx"),
    "resource": ("memoryerror", "out of memory", "disk", "no space", "too many"),
    "environment": ("env", "configuration", "missing environment", "not found in path"),
    "validation": ("assert", "validation", "invalid", "schema"),
    "security": ("permission", "unauthorized", "forbidden", "secret", "access denied"),
}

HUMAN_APPROVAL_CLASSES: set[str] = {"security", "permanent"}


@dataclass
class RetryPolicy:
    """A deterministic retry policy with linear backoff."""

    max_retries: int = 3
    backoff_seconds: float = 0.1


@dataclass
class Incident:
    """A recorded failure incident (auditable, searchable)."""

    incident_id: str
    mission_id: str
    failure_class: str
    message: str
    recorded_at: str = field(default_factory=utcnow)
    resolved: bool = False
    resolution: str = ""


def classify_failure(message: str) -> str:
    """Classify a failure into one of the standard failure classes."""
    lowered = message.lower()
    for failure_class, keywords in _CLASSIFIER_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return failure_class
    return "permanent"


def requires_human_approval(failure_class: str) -> bool:
    return failure_class in HUMAN_APPROVAL_CLASSES


def _should_retry(failure_class: str) -> bool:
    return failure_class in {"transient", "resource", "environment"}


def plan_recovery(
    mission_id: str,
    failure_class: str,
    counters: LoopCounters,
    checkpoint: dict | None = None,
) -> dict[str, str]:
    """Decide the recovery strategy for a failed mission phase.

    Deterministic decision table:
      - transient/resource/environment -> retry (bounded by loop counters)
      - validation -> resume from the last checkpoint
      - permanent -> rollback
      - security -> rollback + human approval
    """
    strategy: str
    if _should_retry(failure_class) and counters.retries < 3:
        strategy = "retry"
    elif failure_class == "validation":
        strategy = "resume" if checkpoint else "replay"
    elif failure_class == "security":
        strategy = "rollback_with_approval"
    else:
        strategy = "rollback"
    return {
        "mission_id": mission_id,
        "failure_class": failure_class,
        "strategy": strategy,
        "human_approval": "required" if requires_human_approval(failure_class) else "not-required",
        "checkpoint": checkpoint.get("phase", "") if checkpoint else "",
    }


def retry(fn, retry_policy: RetryPolicy | None = None, *args, **kwargs):
    """Execute ``fn`` with bounded retries; raises the final error after retries."""
    policy = retry_policy or RetryPolicy()
    last_error: Exception | None = None
    for attempt in range(policy.max_retries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            last_error = exc
            if attempt < policy.max_retries:
                time.sleep(policy.backoff_seconds * (attempt + 1))
    if last_error is not None:
        raise last_error
    return None  # pragma: no cover - unreachable


def record_incident(incident: Incident) -> None:
    data = read_json(INCIDENTS_FILE)
    incidents = data.get("incidents", [])
    incidents.append(vars(incident))
    write_json(INCIDENTS_FILE, {"incidents": incidents})


def resolve_incident(incident_id: str, resolution: str) -> Incident | None:
    data = read_json(INCIDENTS_FILE)
    for raw in data.get("incidents", []):
        if raw.get("incident_id") == incident_id:
            raw["resolved"] = True
            raw["resolution"] = resolution
            write_json(INCIDENTS_FILE, data)
            return Incident(**raw)
    return None


def load_incidents() -> list[Incident]:
    data = read_json(INCIDENTS_FILE)
    return [Incident(**raw) for raw in data.get("incidents", [])]


def checkpoint(mission_id: str, phase: str, payload: dict) -> str:
    path = create_checkpoint(mission_id, phase, payload)
    return str(path)


def resume(mission_id: str, phase: str) -> dict | None:
    return resume_checkpoint(mission_id, phase)
