"""Phase 6 — Technical Debt.

Continuously detect and track technical debt: duplicated logic, deprecated
code, temporary fixes, architecture drift, dependency problems,
configuration drift, and documentation drift. Debt is detected from
deterministic repo evidence, prioritized by impact and severity, and stored
as durable records so it can be reduced over time instead of accumulating.
"""

from __future__ import annotations

from pathlib import Path

from scripts.kernel.core import REPO_ROOT, utcnow
from scripts.optimizer.core import (
    DEBT_DIR,
    DEBT_KINDS,
    DebtItem,
    DebtStatus,
    read_json,
    write_json,
)

DEBT_PATH = DEBT_DIR / "debt.json"

# Signals that prove a debt category exists in the repo.
DEBT_SIGNALS: dict[str, tuple[str, ...]] = {
    "duplicated-logic": ("# duplicate", "FIXME: duplicate", "copy of "),
    "deprecated-code": ("@deprecated", "# deprecated", "deprecated("),
    "temporary-fixes": ("# HACK", "# TEMP", "todo: remove", "todo: fix",
                        "# temporary", "# workaround"),
    "architecture-drift": ("app.ehr import app.national", "circular import",
                           "noqa: E402"),
    "dependency-problems": ("todo: upgrade", "pinned via", "insecure", "cve"),
    "configuration-drift": ("todo: config", "fixme: env", "# env-var"),
    "documentation-drift": ("todo: docs", "fixme: document", "see code"),
}


def detect_debt(root: Path = REPO_ROOT) -> list[DebtItem]:
    """Detect technical-debt records from deterministic repo evidence."""
    items: list[DebtItem] = []
    for kind in DEBT_KINDS:
        signals = DEBT_SIGNALS.get(kind, ())
        evidence = _collect_evidence(root, kind, signals)
        if not evidence:
            continue
        items.append(DebtItem(
            debt_id=f"DEBT-{len(items) + 1:06d}",
            kind=kind,
            area=_debt_area(kind),
            impact=_debt_impact(kind),
            severity=_debt_severity(kind),
            recommendation=_debt_recommendation(kind),
            created_at=utcnow(),
        ))
    return items


def persist_debt(items: list[DebtItem]) -> Path:
    payload = {"debt": [d.to_dict() for d in items], "updated_at": utcnow()}
    write_json(DEBT_PATH, payload)
    return DEBT_PATH


def load_debt() -> list[DebtItem]:
    data = read_json(DEBT_PATH)
    return [DebtItem(**item) for item in data.get("debt", [])]


def set_debt_status(debt_id: str, status: str) -> DebtItem | None:
    """Update a debt record's status (idempotent)."""
    if status not in {ds.value for ds in DebtStatus}:
        raise ValueError(f"invalid debt status: {status}")
    items = load_debt()
    for item in items:
        if item.debt_id == debt_id:
            item.status = status
            persist_debt(items)
            return item
    return None


def _collect_evidence(root: Path, kind: str, signals: tuple[str, ...]) -> list[str]:
    """Scan a bounded set of source files for debt signals."""
    evidence: list[str] = []
    for base in ("backend/app", "scripts", "shared", "config"):
        directory = root / base
        if not directory.exists():
            continue
        for path in directory.rglob("*.py"):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            lowered = text.lower()
            if any(signal.lower() in lowered for signal in signals):
                evidence.append(path.relative_to(root).as_posix())
                if len(evidence) >= 5:
                    return evidence
    return evidence


def _debt_area(kind: str) -> str:
    mapping = {
        "duplicated-logic": "code",
        "deprecated-code": "code",
        "temporary-fixes": "code",
        "architecture-drift": "architecture",
        "dependency-problems": "dependencies",
        "configuration-drift": "configuration",
        "documentation-drift": "documentation",
    }
    return mapping.get(kind, "code")


def _debt_impact(kind: str) -> str:
    mapping = {
        "duplicated-logic": "Fixing one copy does not fix the others; drift silently diverges.",
        "deprecated-code": "Deprecated paths linger and grow stale security surface.",
        "temporary-fixes": "Temporary fixes become permanent and hide the real cause.",
        "architecture-drift": "Modules cross boundaries and erode the intended architecture.",
        "dependency-problems": "Outdated or vulnerable dependencies block safe upgrades.",
        "configuration-drift": "Environments diverge; behavior differs where it should not.",
        "documentation-drift": "Docs no longer match reality, so engineers trust code instead.",
    }
    return mapping.get(kind, "Reduces maintainability.")


def _debt_severity(kind: str) -> str:
    high = {"architecture-drift", "dependency-problems", "temporary-fixes"}
    return "high" if kind in high else "medium"


def _debt_recommendation(kind: str) -> str:
    mapping = {
        "duplicated-logic": "Extract the shared behavior into a reusable core module.",
        "deprecated-code": "Remove the deprecated path once call sites are migrated.",
        "temporary-fixes": "Replace the temporary fix with a permanent, tested solution.",
        "architecture-drift": "Restore the intended module boundaries and break the cycle.",
        "dependency-problems": "Upgrade dependencies in small, reviewed, tested batches.",
        "configuration-drift": "Source configuration from a single shared core.",
        "documentation-drift": "Update the documentation to match the implemented reality.",
    }
    return mapping.get(kind, "Prioritize and reduce the debt by impact.")
