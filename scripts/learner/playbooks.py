"""Phase 3 — Playbook Generation.

Automatically generate playbooks for deployment, recovery, debugging,
performance, security, testing, and infrastructure. A playbook captures the
step-by-step procedure behind a solved problem so any future agent can
execute it without re-deriving it. Playbooks persist in `.ai/core/playbooks/`.
"""

from __future__ import annotations

import re
from pathlib import Path

from scripts.kernel.core import REPO_ROOT, utcnow
from scripts.learner.core import (
    PLAYBOOK_KINDS,
    Extraction,
    KnowledgeItem,
)

PLAYBOOK_DIR = REPO_ROOT / ".ai" / "core" / "playbooks"
ID_RE = re.compile(r"PLAYBOOK-(\d{6})")

# Deterministic procedure skeleton per playbook kind.
PLAYBOOK_STEPS: dict[str, tuple[str, ...]] = {
    "deployment": (
        "Confirm the release is reviewed and gated",
        "Validate the semantic version and environment",
        "Run the deterministic build pipeline",
        "Verify security areas pass before promotion",
        "Capture a pre-deployment snapshot",
        "Deploy and verify all health components",
    ),
    "recovery": (
        "Identify the failed component from health signals",
        "Confirm the latest snapshot and version",
        "Apply version and configuration rollback",
        "Restore the database from backup",
        "Verify restore completeness before returning to service",
        "Record the incident and lesson",
    ),
    "debugging": (
        "Reproduce the failure with the smallest input",
        "Trace the failing path through logs and metrics",
        "Isolate the root cause with a minimal experiment",
        "Apply the fix and add a regression test",
        "Verify the full suite passes",
    ),
    "performance": (
        "Establish a baseline benchmark",
        "Profile the hot path (CPU, memory, latency)",
        "Identify the bottleneck and propose alternatives",
        "Apply the change and re-benchmark",
        "Record the measured improvement",
    ),
    "security": (
        "Run the secret and dependency scans",
        "Verify TLS, certificates, and least privilege",
        "Review authentication and authorization paths",
        "Apply hardening and re-scan",
        "Confirm no critical findings remain",
    ),
    "testing": (
        "Map the change to the affected surfaces",
        "Add unit tests for every new behavior",
        "Add regression tests for every fixed bug",
        "Run the full suite and confirm zero failures",
        "Verify lint and type checks pass",
    ),
    "infrastructure": (
        "Inspect the current infrastructure state",
        "Plan the change against the desired state",
        "Apply the change idempotently",
        "Verify health endpoints and storage",
        "Document the new state",
    ),
}


def next_playbook_id() -> str:
    """Return the next sequential playbook ID."""
    if not PLAYBOOK_DIR.exists():
        return "PLAYBOOK-000001"
    highest = 0
    for path in PLAYBOOK_DIR.glob("*.md"):
        match = ID_RE.search(path.name)
        if match:
            highest = max(highest, int(match.group(1)))
    return f"PLAYBOOK-{highest + 1:06d}"


def generate_playbook(
    kind: str,
    extraction: Extraction | None = None,
    *,
    title: str = "",
) -> KnowledgeItem | None:
    """Generate a playbook for a kind; None when the kind is unknown."""
    if kind not in PLAYBOOK_KINDS:
        return None
    playbook_id = next_playbook_id()
    steps = PLAYBOOK_STEPS[kind]
    body = _render(playbook_id, title or kind, kind, steps, extraction)
    return KnowledgeItem(
        item_id=playbook_id,
        kind="playbook",
        title=title or f"{kind.title()} Playbook",
        status="verified",
        confidence="verified",
        tags=["playbook", kind],
        body=body,
    )


def persist_playbook(playbook: KnowledgeItem) -> Path:
    PLAYBOOK_DIR.mkdir(parents=True, exist_ok=True)
    slug = _slug(playbook.title)
    path = PLAYBOOK_DIR / f"{playbook.item_id}_{slug}.md"
    path.write_text(playbook.body, encoding="utf-8")
    return path


def playbook_exists(title: str) -> bool:
    needle = _slug(title)
    if not PLAYBOOK_DIR.exists():
        return False
    return any(_slug(p.stem.split("_", 1)[-1]) == needle for p in PLAYBOOK_DIR.glob("*.md"))


def find_playbook_by_title(title: str) -> KnowledgeItem | None:
    """Return the existing playbook matching a title (reuse, never duplicate)."""
    needle = _slug(title)
    if not PLAYBOOK_DIR.exists():
        return None
    for path in PLAYBOOK_DIR.glob("*.md"):
        if _slug(path.stem.split("_", 1)[-1]) == needle:
            match = ID_RE.search(path.name)
            if match:
                return KnowledgeItem(
                    item_id=match.group(0),
                    kind="playbook",
                    title=title,
                    status="verified",
                    confidence="verified",
                    body=path.read_text(encoding="utf-8", errors="replace"),
                )
    return None


def _render(playbook_id: str, title: str, kind: str,
            steps: tuple[str, ...], extraction: Extraction | None) -> str:
    lines = [
        "---",
        f"id: {playbook_id}",
        "type: playbook",
        f"title: {title}",
        'version: "1.0"',
        f'created: "{utcnow()[:10]}"',
        "status: verified",
        f"kind: {kind}",
        "---",
        "",
        f"# {playbook_id}: {title}",
        "",
        "## Goal",
        f"Execute the {kind} procedure reliably and repeatably.",
        "",
        "## Prerequisites",
        "- Access to the target environment and its health endpoints",
        "- Verified snapshot or backup when recovery applies",
        "",
        "## Steps",
    ]
    for index, step in enumerate(steps, start=1):
        lines.append(f"{index}. {step}")
    if extraction and extraction.solution:
        lines.extend(["", "## Context", extraction.solution])
    lines.extend([
        "",
        "## Verification",
        "All steps complete without error; health components pass.",
        "",
    ])
    return "\n".join(lines)


def _slug(text: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in text.lower()).strip("_")
    return cleaned[:48]
