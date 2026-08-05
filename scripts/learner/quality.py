"""Phase 8 — Knowledge Quality.

Verify the knowledge store against the seven quality checks: duplicate IDs,
broken references, registry consistency, graph consistency, version
consistency, confidence levels, and knowledge coverage. Produce a
QualityReport with a health score so knowledge quality is continuously
measurable and never silently degrades.
"""

from __future__ import annotations

import re
from pathlib import Path

from scripts.kernel.core import REPO_ROOT
from scripts.learner.core import (
    CONFIDENCE_LEVELS,
    QUALITY_CHECKS,
    QualityReport,
)

SKILL_DIR = REPO_ROOT / ".ai" / "core" / "skills"
PLAYBOOK_DIR = REPO_ROOT / ".ai" / "core" / "playbooks"
RUNBOOK_DIR = REPO_ROOT / ".ai" / "core" / "runbooks"
MEMORY_DIR = REPO_ROOT / ".ai" / "core" / "memory"
REGISTRY = REPO_ROOT / ".ai" / "core" / "registry" / "REGISTRY.md"
GRAPH_INDEX = REPO_ROOT / ".ai" / "core" / "graph" / "knowledge_graph.json"
ID_RE = re.compile(r"(?:SKILL|PLAYBOOK|RUNBOOK|KNOW)-\d{6}")


def run_quality() -> QualityReport:
    """Run all seven knowledge-quality checks and return the report."""
    report = QualityReport()
    checks = {
        "duplicate-ids": _check_duplicate_ids(report),
        "broken-references": _check_broken_references(report),
        "registry-consistency": _check_registry(report),
        "graph-consistency": _check_graph(report),
        "version-consistency": _check_versions(report),
        "confidence-levels": _check_confidence(report),
        "knowledge-coverage": _check_coverage(report),
    }
    report.checks = {name: "pass" if ok else "fail" for name, ok in checks.items()}
    report.health_score = _health_score(report)
    return report


def render_markdown(report: QualityReport) -> str:
    lines = [
        "# Knowledge Quality Report",
        "",
        "| Check | Status |",
        "|---|---|",
    ]
    for name in QUALITY_CHECKS:
        status = report.checks.get(name, "fail")
        lines.append(f"| {name} | {status} |")
    lines.extend([
        "",
        f"Total knowledge items: **{report.total_items}**",
        f"Health score: **{report.health_score}/100**",
        f"Coverage: **{report.coverage_pct:.0f}%**",
        "",
        f"Duplicate IDs: {len(report.duplicate_ids)}",
        f"Broken references: {len(report.broken_references)}",
        "",
        "## Verdict",
        "",
    ])
    if report.health_score >= 90:
        verdict = "**PASS** — knowledge store is healthy."
    elif report.health_score >= 70:
        verdict = "**PASS WITH WARNINGS** — resolve broken references and inconsistencies."
    else:
        verdict = "**REJECT** — knowledge store needs repair before further learning."
    lines.append(verdict)
    lines.append("")
    return "\n".join(lines)


def _knowledge_items() -> list[tuple[str, Path]]:
    """Collect (id, path) for every persisted knowledge item."""
    items: list[tuple[str, Path]] = []
    for directory in (SKILL_DIR, PLAYBOOK_DIR, RUNBOOK_DIR, MEMORY_DIR):
        if not directory.exists():
            continue
        for path in directory.glob("*.md"):
            match = ID_RE.search(path.name)
            if match:
                items.append((match.group(0), path))
    return items


def _check_duplicate_ids(report: QualityReport) -> bool:
    items = _knowledge_items()
    report.total_items = len(items)
    seen: dict[str, int] = {}
    for item_id, _path in items:
        seen[item_id] = seen.get(item_id, 0) + 1
    report.duplicate_ids = [item_id for item_id, count in seen.items() if count > 1]
    return not report.duplicate_ids


def _check_broken_references(report: QualityReport) -> bool:
    """Find references to artifacts that no longer exist."""
    known = {item_id for item_id, _path in _knowledge_items()}
    known.add("SKILL-000000")
    broken: list[str] = []
    for item_id, path in _knowledge_items():
        text = path.read_text(encoding="utf-8", errors="replace")
        for referenced in set(ID_RE.findall(text)):
            if referenced != item_id and referenced not in known:
                broken.append(f"{item_id} -> {referenced}")
    report.broken_references = sorted(set(broken))[:20]
    return not report.broken_references


def _check_registry(report: QualityReport) -> bool:
    if not REGISTRY.exists():
        report.registry_consistent = False
        return False
    text = REGISTRY.read_text(encoding="utf-8", errors="replace")
    for item_id, _path in _knowledge_items():
        if ID_RE.match(item_id) and item_id not in text:
            report.registry_consistent = False
            return False
    report.registry_consistent = True
    return True


def _check_graph(report: QualityReport) -> bool:
    if not GRAPH_INDEX.exists():
        report.graph_consistent = False
        return False
    try:
        import json
        graph = json.loads(GRAPH_INDEX.read_text(encoding="utf-8"))
        nodes = graph.get("nodes", [])
        known = {node.get("id") for node in nodes}
        known |= {item_id for item_id, _path in _knowledge_items()}
        valid = all(
            related in known
            for node in nodes
            for related in node.get("related", [])
        )
        report.graph_consistent = valid
        return valid
    except (json.JSONDecodeError, OSError):
        report.graph_consistent = False
        return False


def _check_versions(report: QualityReport) -> bool:
    """All persisted knowledge items must declare version 1.0 frontmatter."""
    consistent = True
    for _item_id, path in _knowledge_items():
        text = path.read_text(encoding="utf-8", errors="replace")
        if 'version: "1.0"' not in text:
            consistent = False
            break
    report.version_consistent = consistent
    return consistent


def _check_confidence(report: QualityReport) -> bool:
    """Confidence must use the allowed vocabulary or a numeric legacy value."""
    allowed = set(CONFIDENCE_LEVELS)
    for _item_id, path in _knowledge_items():
        text = path.read_text(encoding="utf-8", errors="replace")
        match = re.search(r"confidence:\s*(\d+(?:\.\d+)?%?|\w+)", text)
        if match and match.group(1) not in allowed and not re.fullmatch(
            r"\d+(?:\.\d+)?%?", match.group(1)
        ):
            report.confidence_consistent = False
            return False
    report.confidence_consistent = True
    return True


def _check_coverage(report: QualityReport) -> bool:
    """Estimated coverage: present categories vs expected categories."""
    expected_categories = {
        "skill", "playbook", "runbook", "memory",
    }
    present_categories: set[str] = set()
    for item_id, _path in _knowledge_items():
        prefix = item_id.split("-", 1)[0].lower()
        present_categories.add(prefix)
    coverage = len(present_categories) / len(expected_categories)
    report.coverage_pct = round(coverage * 100, 1)
    return coverage >= 0.5


def _health_score(report: QualityReport) -> int:
    score = 100
    score -= 10 * len(report.duplicate_ids)
    score -= 5 * min(len(report.broken_references), 6)
    if not report.registry_consistent:
        score -= 10
    if not report.graph_consistent:
        score -= 10
    if not report.version_consistent:
        score -= 5
    if not report.confidence_consistent:
        score -= 5
    if report.coverage_pct < 50:
        score -= 10
    return max(0, min(100, score))
