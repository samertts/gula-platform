"""Findings persistence with recurrence memory.

The registry merges newly detected occurrences with the recorded history so the
platform can answer: is this new, is this still open, or has a finding that was
previously fixed come back?
"""
from __future__ import annotations

import json
import pathlib
from typing import Any

from .model import CheckResult, FindingState

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
STATE_PATH = REPO_ROOT / "docs" / "architecture" / "gula_intel_state.json"

NEW = "NEW"
STILL_OPEN = "STILL_OPEN"
RECURRED = "RECURRED"
RESOLVED = "RESOLVED"


def load_state(path: pathlib.Path | None = None) -> dict[str, Any]:
    target = path or STATE_PATH
    if not target.is_file():
        return {"occurrences": {}}
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {"occurrences": {}}


def reconcile(results: list[CheckResult], state: dict[str, Any], commit: str) -> dict[str, Any]:
    """Classify every occurrence against history without mutating the input."""
    known: dict[str, Any] = dict(state.get("occurrences") or {})
    seen: set[str] = set()
    transitions: dict[str, str] = {}

    for result in results:
        for finding in result.findings:
            oid = finding.occurrence_id
            seen.add(oid)
            previous = known.get(oid)
            if previous is None:
                transitions[oid] = NEW
            elif previous.get("state") in {FindingState.FIXED.value, FindingState.VERIFIED.value}:
                transitions[oid] = RECURRED
            else:
                transitions[oid] = STILL_OPEN
            known[oid] = {
                "rule_id": finding.rule_id,
                "title": finding.title,
                "severity": finding.severity.value,
                "state": FindingState.OPEN.value,
                "last_seen_commit": commit,
                "first_seen_commit": (previous or {}).get("first_seen_commit", commit),
                "evidence": finding.evidence,
            }

    # An occurrence previously open but no longer detected by a detector that ran
    # cleanly is resolved. A detector that did not run cannot resolve anything.
    ran_rules = {r.rule_id for r in results if r.detector_state.name.startswith("RAN")}
    for oid, record in known.items():
        if oid in seen or record.get("rule_id") not in ran_rules:
            continue
        if record.get("state") not in {FindingState.FIXED.value, FindingState.VERIFIED.value}:
            transitions[oid] = RESOLVED
            record["state"] = FindingState.FIXED.value
            record["fixed_at_commit"] = commit

    return {"occurrences": known, "transitions": transitions}


def save_state(state: dict[str, Any], path: pathlib.Path | None = None) -> pathlib.Path:
    target = path or STATE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return target
