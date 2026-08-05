"""Phase 4 — Runbook Generation.

Automatically generate runbooks for incidents, recovery, monitoring,
production, maintenance, scaling, backup, and rollback. A runbook is the
live procedure an operator executes; the Learner keeps them current from
deployment and incident knowledge so operations never depend on memory.
Runbooks persist in `.ai/core/runbooks/`.
"""

from __future__ import annotations

import re
from pathlib import Path

from scripts.kernel.core import REPO_ROOT, utcnow
from scripts.learner.core import (
    RUNBOOK_KINDS,
    Extraction,
    KnowledgeItem,
)

RUNBOOK_DIR = REPO_ROOT / ".ai" / "core" / "runbooks"
ID_RE = re.compile(r"RUNBOOK-(\d{6})")

# Deterministic procedure skeleton per runbook kind.
RUNBOOK_STEPS: dict[str, tuple[str, ...]] = {
    "incidents": (
        "Detect the incident from health or alert signals",
        "Assess severity and scope of impact",
        "Open the incident record with timestamp and symptoms",
        "Apply the recovery procedure for the affected component",
        "Verify service restored on all health endpoints",
        "Record the incident, root cause, and lesson",
    ),
    "recovery": (
        "Confirm the failure mode from error signals",
        "Identify the snapshot or backup to restore",
        "Restore configuration and data",
        "Verify data integrity and service health",
        "Hand back to production and monitor",
    ),
    "monitoring": (
        "Check health endpoints and key metrics",
        "Review recent errors and latency signals",
        "Verify storage and connection pools",
        "Compare metrics against baseline",
        "Escalate anomalies and record observations",
    ),
    "production": (
        "Verify the deployed version and environment",
        "Confirm all health components pass",
        "Check secrets, certificates, and expiry dates",
        "Review recent logs for anomalies",
        "Confirm backup freshness",
        "Document the production state",
    ),
    "maintenance": (
        "Schedule maintenance during a low-traffic window",
        "Capture a pre-maintenance snapshot",
        "Apply the maintenance change",
        "Verify health after the change",
        "Roll back immediately if health regresses",
    ),
    "scaling": (
        "Measure current utilization and saturation",
        "Decide the scaling dimension (replicas, workers, storage)",
        "Apply the scaling change",
        "Verify load distribution and health",
        "Record the new capacity baseline",
    ),
    "backup": (
        "Verify the backup schedule and retention policy",
        "Run a fresh backup of data and configuration",
        "Verify backup integrity and restore readability",
        "Record backup metadata (time, size, location)",
        "Audit recovery-point and recovery-time objectives",
    ),
    "rollback": (
        "Confirm the failing version and its snapshot",
        "Apply version rollback from the pre-deploy snapshot",
        "Restore configuration to the previous known-good state",
        "Verify all health components pass",
        "Record the rollback lesson for the next release",
    ),
}


def next_runbook_id() -> str:
    """Return the next sequential runbook ID."""
    if not RUNBOOK_DIR.exists():
        return "RUNBOOK-000001"
    highest = 0
    for path in RUNBOOK_DIR.glob("*.md"):
        match = ID_RE.search(path.name)
        if match:
            highest = max(highest, int(match.group(1)))
    return f"RUNBOOK-{highest + 1:06d}"


def generate_runbook(
    kind: str,
    extraction: Extraction | None = None,
    *,
    title: str = "",
) -> KnowledgeItem | None:
    """Generate a runbook for a kind; None when the kind is unknown."""
    if kind not in RUNBOOK_KINDS:
        return None
    runbook_id = next_runbook_id()
    steps = RUNBOOK_STEPS[kind]
    body = _render(runbook_id, title or kind, kind, steps, extraction)
    return KnowledgeItem(
        item_id=runbook_id,
        kind="runbook",
        title=title or f"{kind.title()} Runbook",
        status="verified",
        confidence="verified",
        tags=["runbook", kind],
        body=body,
    )


def persist_runbook(runbook: KnowledgeItem) -> Path:
    RUNBOOK_DIR.mkdir(parents=True, exist_ok=True)
    slug = _slug(runbook.title)
    path = RUNBOOK_DIR / f"{runbook.item_id}_{slug}.md"
    path.write_text(runbook.body, encoding="utf-8")
    return path


def runbook_exists(title: str) -> bool:
    needle = _slug(title)
    if not RUNBOOK_DIR.exists():
        return False
    return any(_slug(p.stem.split("_", 1)[-1]) == needle for p in RUNBOOK_DIR.glob("*.md"))


def find_runbook_by_title(title: str) -> KnowledgeItem | None:
    """Return the existing runbook matching a title (reuse, never duplicate)."""
    needle = _slug(title)
    if not RUNBOOK_DIR.exists():
        return None
    for path in RUNBOOK_DIR.glob("*.md"):
        if _slug(path.stem.split("_", 1)[-1]) == needle:
            match = ID_RE.search(path.name)
            if match:
                return KnowledgeItem(
                    item_id=match.group(0),
                    kind="runbook",
                    title=title,
                    status="verified",
                    confidence="verified",
                    body=path.read_text(encoding="utf-8", errors="replace"),
                )
    return None


def _render(runbook_id: str, title: str, kind: str,
            steps: tuple[str, ...], extraction: Extraction | None) -> str:
    lines = [
        "---",
        f"id: {runbook_id}",
        "type: runbook",
        f"title: {title}",
        'version: "1.0"',
        f'created: "{utcnow()[:10]}"',
        "status: verified",
        f"kind: {kind}",
        "---",
        "",
        f"# {runbook_id}: {title}",
        "",
        "## Purpose",
        f"Operate the {kind} procedure reliably and repeatably.",
        "",
        "## Prerequisites",
        "- Access to the environment and its health endpoints",
        "- Verified snapshot or backup when applicable",
        "",
        "## Procedure",
    ]
    for index, step in enumerate(steps, start=1):
        lines.append(f"{index}. {step}")
    if extraction and extraction.solution:
        lines.extend(["", "## Context", extraction.solution])
    lines.extend([
        "",
        "## Success Criteria",
        "All health components pass; service state matches the runbook goal.",
        "",
    ])
    return "\n".join(lines)


def _slug(text: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in text.lower()).strip("_")
    return cleaned[:48]
