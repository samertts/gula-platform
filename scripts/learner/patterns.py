"""Phase 6 — Recurring Pattern Detection.

Detect recurring engineering patterns from the knowledge store: repeated
bugs, repeated refactorings, repeated design work, repeated deployment
failures, repeated performance issues, and repeated security findings.
A pattern emerges when the same area crosses a repeat threshold — the
Learner then elevates it with a remediation recommendation so the platform
breaks the cycle instead of re-solving the same problem.
"""

from __future__ import annotations

from pathlib import Path

from scripts.kernel.core import utcnow
from scripts.learner.core import (
    PATTERN_DIR,
    PATTERN_KINDS,
    Pattern,
    read_json,
    write_json,
)

AREA_ALIASES = {
    "deployment": "deployment",
    "deploy": "deployment",
    "release": "deployment",
    "rollback": "deployment",
    "security": "security",
    "secret": "security",
    "permission": "security",
    "auth": "security",
    "performance": "performance",
    "latency": "performance",
    "memory": "performance",
    "benchmark": "performance",
    "database": "database",
    "sql": "database",
    "migration": "database",
    "model": "database",
    "frontend": "frontend",
    "typescript": "frontend",
    "react": "frontend",
    "ui": "frontend",
    "backend": "backend",
    "api": "backend",
    "service": "backend",
    "testing": "testing",
    "test": "testing",
    "coverage": "testing",
    "infrastructure": "infrastructure",
    "docker": "infrastructure",
    "redis": "infrastructure",
    "ci": "infrastructure",
    "tooling": "tooling",
    "lint": "tooling",
    "env": "tooling",
    "path": "tooling",
}

# Recommendation template per pattern kind.
RECOMMENDATIONS: dict[str, str] = {
    "repeated-bug": "Add a regression test and a dedicated guard in the affected service.",
    "repeated-refactoring": "Extract the shared behavior into a reusable core module.",
    "repeated-design": "Promote the proven approach into a documented architecture decision (ADR).",
    "repeated-deployment-failure": "Automate the failing step in the deployer pipeline and add a health gate.",
    "repeated-performance-issue": "Add a benchmark, cache the hot path, and profile before the next release.",
    "repeated-security-finding": "Harden the affected surface, add a scan rule, and review related areas.",
}


def detect_patterns(items: list[tuple[str, str]]) -> list[Pattern]:
    """Detect recurring patterns from (area, text) knowledge pairs."""
    counts: dict[tuple[str, str], list[str]] = {}
    for area, text in items:
        resolved = _resolve_area(area, text)
        if resolved:
            counts.setdefault(resolved, []).append(text)
    patterns: list[Pattern] = []
    for (area, kind), evidence in sorted(counts.items()):
        if kind not in PATTERN_KINDS:
            continue
        if len(evidence) >= _threshold(kind):
            patterns.append(Pattern(
                pattern_id=f"PAT-{len(patterns) + 1:06d}",
                kind=kind,
                area=area,
                count=len(evidence),
                threshold=_threshold(kind),
                evidence=sorted(set(evidence))[:5],
                recommendation=RECOMMENDATIONS.get(kind, ""),
            ))
    return patterns


def persist_patterns(patterns: list[Pattern]) -> Path:
    PATTERN_DIR.mkdir(parents=True, exist_ok=True)
    path = PATTERN_DIR / "patterns.json"
    payload = {"patterns": [p.to_dict() for p in patterns], "updated_at": utcnow()}
    write_json(path, payload)
    return path


def load_patterns() -> list[Pattern]:
    data = read_json(PATTERN_DIR / "patterns.json")
    return [Pattern(**item) for item in data.get("patterns", [])]


def _resolve_area(area: str, text: str) -> tuple[str, str] | None:
    """Resolve (area, pattern-kind) from an explicit area + text hints."""
    kind = _classify_kind(text)
    if not kind:
        return None
    alias = AREA_ALIASES.get(area.lower(), area.lower())
    return alias, kind


def _classify_kind(text: str) -> str | None:
    lowered = text.lower()
    scoring = {
        "repeated-bug": ("bug", "regression", "failure", "error", "fix"),
        "repeated-refactoring": ("refactor", "extract", "restructure", "duplicate"),
        "repeated-design": ("design", "architecture", "module", "dependency"),
        "repeated-deployment-failure": ("deploy", "release", "rollback", "snapshot"),
        "repeated-performance-issue": ("performance", "latency", "benchmark", "memory"),
        "repeated-security-finding": ("security", "secret", "cve", "permission", "tls"),
    }
    best: tuple[str, int] | None = None
    for kind, keywords in scoring.items():
        score = sum(1 for keyword in keywords if keyword in lowered)
        if score and (best is None or score > best[1]):
            best = (kind, score)
    return best[0] if best else None


def _threshold(kind: str) -> int:
    return 3 if kind == "repeated-security-finding" else 2
