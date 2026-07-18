#!/usr/bin/env python3
"""
GULA Technical Debt Classification Registry
============================================
Catalogs, classifies, and tracks ALL technical debt items across the GULA monorepo.

Integrates with:
  - scripts/architecture_compliance_engine.py (L1-L7 rule violations)
  - scripts/repository_scorecard.py (10-axis health scores)
  - docs/constitution/CONSTITUTION-VALIDATION-REPORT.md (contradictions & gaps)

Classification scheme:
  P0 — Blocking (deployment, data loss, security breach)     → 24h SLA
  P1 — Critical (constitution mandates, patient safety)       → 7d SLA
  P2 — Major (best practices, technical debt accumulation)    → 30d SLA
  P3 — Minor (cosmetic, naming, documentation)                → 90d SLA

Usage:
  python scripts/technical_debt_registry.py              # full report
  python scripts/technical_debt_registry.py --summary    # compact view
  python scripts/technical_debt_registry.py --refresh    # re-scan & re-classify
  python scripts/technical_debt_registry.py --search P1  # filter by priority
  python scripts/technical_debt_registry.py --json       # output JSON only
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
ENGINE_PATH = REPO_ROOT / "scripts" / "architecture_compliance_engine.py"
SCORECARD_PATH = REPO_ROOT / "scripts" / "repository_scorecard.py"
CONSTITUTION_REPORT = REPO_ROOT / "docs" / "constitution" / "CONSTITUTION-VALIDATION-REPORT.md"
REGISTRY_DIR = REPO_ROOT / "docs" / "technical-debt"
REGISTRY_MD = REGISTRY_DIR / "REGISTRY.md"
REGISTRY_JSON = REGISTRY_DIR / "registry.json"

_RESET = "\033[0m"
_RED = "\033[91m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_CYAN = "\033[96m"
_BOLD = "\033[1m"
_MAGENTA = "\033[95m"
_WHITE = "\033[97m"

_USE_COLOR = sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    if not _USE_COLOR:
        return text
    palette = {"red": _RED, "green": _GREEN, "yellow": _YELLOW, "cyan": _CYAN,
               "bold": _BOLD, "magenta": _MAGENTA, "white": _WHITE, "reset": _RESET}
    return f"{palette.get(code, _RESET)}{text}{_RESET}"


_PRIORITY_COLORS = {"P0": _RED, "P1": _MAGENTA, "P2": _YELLOW, "P3": _CYAN}
_STATUS_EMOJI = {"open": "○", "fixing": "◔", "fixed": "✓", "waived": "—", "": "○"}

# ── Classification rules ──────────────────────────────────────────────────────

CATEGORY_LABELS: dict[str, str] = {
    "layer_violations": "Layer Violations",
    "circular_dependencies": "Circular Dependencies",
    "forbidden_imports": "Forbidden Imports",
    "cross_domain_leakage": "Cross-Domain Leakage",
    "large_files_functions": "Large Files/Functions",
    "naming_violations": "Naming Violations",
    "documentation_gaps": "Documentation Gaps",
    "coverage_deficits": "Coverage Deficits",
    "constitution_contradictions": "Constitution Contradictions",
    "missing_adrs": "Missing ADRs",
}

CATEGORY_ORDER = [
    "constitution_contradictions",
    "circular_dependencies",
    "layer_violations",
    "forbidden_imports",
    "cross_domain_leakage",
    "coverage_deficits",
    "documentation_gaps",
    "large_files_functions",
    "naming_violations",
    "missing_adrs",
]

# Default effort estimates (hours) by category and severity
EFFORT_ESTIMATES: dict[str, dict[str, int]] = {
    "layer_violations": {"P0": 8, "P1": 4, "P2": 2, "P3": 1},
    "circular_dependencies": {"P0": 16, "P1": 8, "P2": 4, "P3": 2},
    "forbidden_imports": {"P0": 4, "P1": 2, "P2": 1, "P3": 0.5},
    "cross_domain_leakage": {"P0": 12, "P1": 6, "P2": 3, "P3": 1},
    "large_files_functions": {"P0": 0, "P1": 0, "P2": 4, "P3": 2},
    "naming_violations": {"P0": 0, "P1": 0, "P2": 1, "P3": 0.5},
    "documentation_gaps": {"P0": 0, "P1": 0, "P2": 2, "P3": 1},
    "coverage_deficits": {"P0": 40, "P1": 20, "P2": 10, "P3": 0},
    "constitution_contradictions": {"P0": 8, "P1": 4, "P2": 2, "P3": 1},
    "missing_adrs": {"P0": 0, "P1": 0, "P2": 3, "P3": 1},
}

# Map constitution contradiction IDs to their remediation priority from report
CONSTITUTION_PRIORITIES: dict[str, str] = {
    "C1": "P0", "C2": "P0", "C6": "P0", "C11": "P0",
    "C3": "P1", "C5": "P1", "C7": "P1", "C10": "P1", "C12": "P1",
    "C4": "P2", "C8": "P2", "C9": "P2", "C13": "P2",
    "G1": "P3", "G2": "P3", "G3": "P2", "G4": "P3", "G5": "P3", "G6": "P3",
}

CONSTITUTION_EFFORT: dict[str, int] = {
    "C1": 16, "C2": 40, "C6": 8, "C11": 4,
    "C3": 4, "C5": 4, "C7": 4, "C10": 8, "C12": 8,
    "C4": 1, "C8": 1, "C9": 2, "C13": 16,
    "G1": 2, "G2": 2, "G3": 4, "G4": 2, "G5": 2, "G6": 1,
}


# ── Data structures ────────────────────────────────────────────────────────────

class DebtItem:
    __slots__ = (
        "id", "priority", "category", "category_key", "description",
        "file", "lines", "est_hours", "status", "owner", "source",
        "created_at", "updated_at", "extra",
    )

    def __init__(
        self,
        debt_id: str,
        priority: str,
        category_key: str,
        description: str,
        file: str = "",
        lines: str = "",
        est_hours: float = 1.0,
        status: str = "open",
        owner: str = "unassigned",
        source: str = "",
        extra: dict | None = None,
    ):
        now = datetime.now(timezone.utc).isoformat()
        self.id = debt_id
        self.priority = priority
        self.category_key = category_key
        self.category = CATEGORY_LABELS.get(category_key, category_key)
        self.description = description
        self.file = file
        self.lines = lines
        self.est_hours = est_hours
        self.status = status
        self.owner = owner
        self.source = source
        self.created_at = now
        self.updated_at = now
        self.extra = extra or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "priority": self.priority,
            "category": self.category,
            "category_key": self.category_key,
            "description": self.description,
            "file": self.file,
            "lines": self.lines,
            "est_hours": self.est_hours,
            "status": self.status,
            "owner": self.owner,
            "source": self.source,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, d: dict) -> DebtItem:
        item = cls(
            debt_id=d["id"],
            priority=d["priority"],
            category_key=d.get("category_key", d.get("category", "")),
            description=d["description"],
            file=d.get("file", ""),
            lines=d.get("lines", ""),
            est_hours=d.get("est_hours", 1),
            status=d.get("status", "open"),
            owner=d.get("owner", "unassigned"),
            source=d.get("source", ""),
            extra=d.get("extra", {}),
        )
        item.created_at = d.get("created_at", item.created_at)
        item.updated_at = d.get("updated_at", item.updated_at)
        return item

    def __repr__(self) -> str:
        return f"<DebtItem {self.id} {self.priority} {self.category}: {self.description[:50]}>"


# ── Git blame helper ───────────────────────────────────────────────────────────

def _git_blame_owner(filepath: str, lines_str: str = "") -> str:
    """Try to determine the most frequent committer for a file via git blame."""
    try:
        rel = pathlib.Path(filepath)
        if rel.is_absolute():
            try:
                rel = rel.relative_to(REPO_ROOT)
            except ValueError:
                pass

        target = REPO_ROOT / rel
        if not target.exists():
            return "unassigned"

        blame_cmd = ["git", "blame", "--line-porcelain", str(target)]
        if lines_str:
            line_nums = re.findall(r"\d+", lines_str)
            if line_nums:
                blame_cmd = ["git", "blame", "--line-porcelain",
                             f"-L{line_nums[0]},{line_nums[0]}", str(target)]

        result = subprocess.run(
            blame_cmd, capture_output=True, text=True, timeout=15,
            cwd=REPO_ROOT,
        )
        if result.returncode != 0:
            return "unassigned"

        authors: list[str] = []
        for line in result.stdout.splitlines():
            if line.startswith("author "):
                authors.append(line[7:].strip())

        if not authors:
            return "unassigned"

        most_common = Counter(authors).most_common(1)
        return most_common[0][0] if most_common else "unassigned"
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return "unassigned"


def _git_blame_for_file(filepath: str) -> str:
    """Get the most common author for a whole file."""
    return _git_blame_owner(filepath)


# ── Config loading ─────────────────────────────────────────────────────────────

COMPLIANCE_SCORE_KEY = ("score", "compliance_score")


def _load_existing_registry() -> list[DebtItem]:
    """Load existing registry.json to preserve status and ownership."""
    if REGISTRY_JSON.exists():
        try:
            data = json.loads(REGISTRY_JSON.read_text(encoding="utf-8"))
            return [DebtItem.from_dict(item) for item in data.get("items", [])]
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
    return []


def _run_compliance_engine() -> list[dict[str, Any]]:
    """Run the architecture compliance engine and return rule results."""
    if not ENGINE_PATH.exists():
        return []

    try:
        result = subprocess.run(
            [sys.executable, str(ENGINE_PATH), "--json",
             "--exclude-dirs", "tests,migrations,__pycache__"],
            capture_output=True, text=True, timeout=120, cwd=REPO_ROOT,
        )
        data = json.loads(result.stdout)
        return data.get("results", data.get("rules", []))
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError,
            subprocess.CalledProcessError):
        return []


def _run_scorecard() -> dict[str, Any]:
    """Run the repository scorecard and return axis data."""
    if not SCORECARD_PATH.exists():
        return {}

    try:
        result = subprocess.run(
            [sys.executable, str(SCORECARD_PATH), "--json"],
            capture_output=True, text=True, timeout=120, cwd=REPO_ROOT,
        )
        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError,
            subprocess.CalledProcessError):
        return {}


def _parse_constitution_contradictions() -> list[dict[str, Any]]:
    """Parse the constitution validation report for contradictions and gaps."""
    if not CONSTITUTION_REPORT.exists():
        return []

    text = CONSTITUTION_REPORT.read_text(encoding="utf-8")
    contradictions: list[dict[str, Any]] = []

    # Parse C1-C13 contradictions
    c_pattern = re.compile(
        r"### (C\d+)\.\s*(.+?)\n.*?"
        r"Priority.*?\n.*?(P[0-3])",
        re.DOTALL,
    )
    # Simpler approach: find by heading patterns
    sections = re.split(r"\n###\s+", text)

    for section in sections:
        if not section.strip():
            continue

        # Match contradiction entries
        cm = re.match(r"(C\d+)\.\s+(.+?)(?:\n|$)", section)
        gm = re.match(r"(G\d+)\.\s+(.+?)(?:\n|$)", section)

        if cm:
            cid = cm.group(1)
            title = cm.group(2).strip()
            contradictions.append({
                "id": cid,
                "title": title,
                "priority": CONSTITUTION_PRIORITIES.get(cid, "P2"),
                "effort": CONSTITUTION_EFFORT.get(cid, 4),
                "type": "contradiction",
            })
        elif gm:
            gid = gm.group(1)
            title = gm.group(2).strip()
            contradictions.append({
                "id": gid,
                "title": title,
                "priority": CONSTITUTION_PRIORITIES.get(gid, "P3"),
                "effort": CONSTITUTION_EFFORT.get(gid, 2),
                "type": "gap",
            })

    return contradictions


# ── Violation parser helpers ───────────────────────────────────────────────────

def _extract_file_and_line(violation_str: str) -> tuple[str, str]:
    """Extract file path and line number from a violation string.

    Handles formats:
      app.routes.foo:42 description
      backend/app/routes/foo.py:42 description
    """
    m = re.match(r"([\w.]+(?::\d+)?)\s+(.*)", violation_str)
    if m:
        loc = m.group(1)
        if ":" in loc:
            parts = loc.split(":", 1)
            return parts[0], parts[1]
        return loc, ""
    return "", ""


def _module_to_filepath(module_str: str) -> str:
    """Convert dotted module path to a filesystem path."""
    path = module_str.replace(".", "/")
    candidate = REPO_ROOT / "backend" / "app" / f"{path}.py"
    if candidate.exists():
        return str(candidate.relative_to(REPO_ROOT))
    candidate_init = REPO_ROOT / "backend" / "app" / path / "__init__.py"
    if candidate_init.exists():
        return str(candidate_init.relative_to(REPO_ROOT))
    return f"backend/app/{path}.py"


# ── Compliance engine result classifiers ───────────────────────────────────────

def _classify_violation(rule_id: str, violation: str) -> tuple[str, str]:
    """Classify a single violation string into (priority, category_key)."""
    vl = violation.lower()

    if rule_id == "L1":
        if "domain imports framework" in vl:
            return "P1", "layer_violations"
        if "routes imports from" in vl or "services imports from" in vl:
            return "P2", "layer_violations"
        return "P2", "layer_violations"

    if rule_id == "L2":
        return "P1", "circular_dependencies"

    if rule_id == "L3":
        if "redis" in vl and "forbidden" in vl:
            return "P1", "forbidden_imports"
        if "routes importing from" in vl:
            return "P2", "forbidden_imports"
        if "services importing from" in vl:
            return "P2", "forbidden_imports"
        if "domain importing" in vl:
            return "P1", "forbidden_imports"
        return "P2", "forbidden_imports"

    if rule_id == "L4":
        return "P2", "cross_domain_leakage"

    if rule_id == "L5":
        if "Files exceeding 2000" in violation or "exceeding 2000" in vl:
            return "P2", "large_files_functions"
        if "Functions exceeding 100" in violation or "exceeding 100" in vl:
            return "P2", "large_files_functions"
        if "Files exceeding 1000" in violation or "exceeding 1000" in vl:
            return "P3", "large_files_functions"
        return "P3", "large_files_functions"

    if rule_id == "L6":
        return "P3", "naming_violations"

    if rule_id == "L7":
        return "P3", "documentation_gaps"

    return "P2", "layer_violations"


# ── Debt item generators ───────────────────────────────────────────────────────

def _debt_from_compliance(
    compliance_results: list[dict[str, Any]],
    existing_map: dict[str, DebtItem],
    counter: list[int],
) -> list[DebtItem]:
    """Generate debt items from compliance engine rule results."""
    items: list[DebtItem] = []

    for rule in compliance_results:
        rule_id = rule.get("rule", "")
        details = rule.get("details", [])

        # Skip "no violations" messages
        skip_patterns = [
            "no layer violations", "no circular dependencies",
            "no forbidden imports", "no cross-domain violations",
            "within size limits", "naming conventions satisfied",
            "all files and routes have documentation",
        ]

        for detail in details:
            # Skip header/summary lines
            if any(detail.lower().startswith(p) for p in ["found", "no ", "all ", "files ", "functions ", "package ", "test ", "class/function/variable", "... and "]):
                continue
            if any(p in detail.lower() for p in skip_patterns):
                continue
            if not detail.strip() or not detail.startswith("  -"):
                continue

            # Clean up the violation text
            vtext = detail.strip()
            if vtext.startswith("- "):
                vtext = vtext[2:].strip()
            if vtext.startswith("-"):
                vtext = vtext[1:].strip()

            priority, cat_key = _classify_violation(rule_id, vtext)

            module_part, line_part = _extract_file_and_line(vtext)
            filepath = _module_to_filepath(module_part) if module_part else ""
            lines_str = line_part

            source = f"compliance:{rule_id}"

            est = EFFORT_ESTIMATES.get(cat_key, {}).get(priority, 2)
            if rule_id == "L5":
                if "Files exceeding" in detail:
                    est = 3 if priority == "P2" else 1
                else:
                    est = 2

            debt_id = f"TD-{counter[0]:04d}"

            # Check existing
            existing = existing_map.get(debt_id)
            status = "open"
            owner = "unassigned"
            if existing:
                status = existing.status
                owner = existing.owner

            # Auto-detect owner if unassigned and file exists
            if owner == "unassigned" and filepath:
                detected = _git_blame_for_file(filepath)
                if detected != "unassigned":
                    owner = detected

            item = DebtItem(
                debt_id=debt_id,
                priority=priority,
                category_key=cat_key,
                description=vtext[:200],
                file=filepath,
                lines=lines_str,
                est_hours=est,
                status=status,
                owner=owner,
                source=source,
            )

            items.append(item)
            existing_map[debt_id] = item
            counter[0] += 1

    return items


def _debt_from_constitution(
    contradictions: list[dict[str, Any]],
    existing_map: dict[str, DebtItem],
    counter: list[int],
) -> list[DebtItem]:
    """Generate debt items from constitution contradictions and gaps."""
    items: list[DebtItem] = []

    for entry in contradictions:
        cid = entry["id"]
        priority = entry["priority"]
        title = entry["title"]
        effort = entry["effort"]
        ctype = entry["type"]

        cat_key = "constitution_contradictions"
        if ctype == "gap":
            if "adr" in title.lower() or "ADR" in title:
                cat_key = "missing_adrs"

        source = f"constitution:{cid}"

        debt_id = f"TD-{counter[0]:04d}"
        existing = existing_map.get(debt_id)
        status = "open"
        owner = "unassigned"
        if existing:
            status = existing.status
            owner = existing.owner

        item = DebtItem(
            debt_id=debt_id,
            priority=priority,
            category_key=cat_key,
            description=f"{cid}: {title}",
            file="",
            lines="",
            est_hours=effort,
            status=status,
            owner=owner,
            source=source,
        )

        items.append(item)
        existing_map[debt_id] = item
        counter[0] += 1

    return items


def _debt_from_scorecard(
    scorecard_data: dict[str, Any],
    existing_map: dict[str, DebtItem],
    counter: list[int],
) -> list[DebtItem]:
    """Generate debt items from scorecard findings (coverage, etc.)."""
    items: list[DebtItem] = []

    axes = scorecard_data.get("axes", [])
    for axis in axes:
        name = axis.get("name", "")
        score = axis.get("score", 100)
        findings = axis.get("findings", [])

        if name == "Test Coverage" and score < 60:
            debt_id = f"TD-{counter[0]:04d}"
            existing = existing_map.get(debt_id)
            status = "open"
            owner = "unassigned"
            if existing:
                status = existing.status
                owner = existing.owner

            item = DebtItem(
                debt_id=debt_id,
                priority="P2",
                category_key="coverage_deficits",
                description=f"Test coverage at {score}% — below 60% threshold. "
                            f"Need comprehensive test suite across all modules.",
                file="",
                lines="",
                est_hours=40,
                status=status,
                owner=owner,
                source="scorecard:test_coverage",
                extra={"axis_score": score},
            )
            items.append(item)
            existing_map[debt_id] = item
            counter[0] += 1

        # Add findings that indicate technical debt
        for finding in findings:
            if "failing" in finding.lower() and "test" in finding.lower():
                debt_id = f"TD-{counter[0]:04d}"
                existing = existing_map.get(debt_id)
                status = "open"
                owner = "unassigned"
                if existing:
                    status = existing.status
                    owner = existing.owner

                item = DebtItem(
                    debt_id=debt_id,
                    priority="P1",
                    category_key="coverage_deficits",
                    description=finding[:200],
                    file="",
                    lines="",
                    est_hours=8,
                    status=status,
                    owner=owner,
                    source="scorecard:test_failures",
                )
                items.append(item)
                existing_map[debt_id] = item
                counter[0] += 1

    return items


# ── Registry I/O ───────────────────────────────────────────────────────────────

def _write_registry_json(items: list[DebtItem]) -> None:
    """Write structured JSON registry."""
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)

    counts = Counter(i.priority for i in items)
    status_counts = Counter(i.status for i in items)
    category_counts = Counter(i.category for i in items)
    total_effort = sum(i.est_hours for i in items)

    registry = {
        "meta": {
            "title": "GULA Technical Debt Registry",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "repo_root": str(REPO_ROOT),
            "total_items": len(items),
            "total_est_hours": round(total_effort, 1),
            "by_priority": dict(counts),
            "by_status": dict(status_counts),
            "by_category": dict(category_counts),
        },
        "items": [i.to_dict() for i in items],
    }

    REGISTRY_JSON.write_text(
        json.dumps(registry, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _write_registry_md(items: list[DebtItem]) -> None:
    """Write human-readable markdown registry table."""
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    counts = Counter(i.priority for i in items)
    status_counts = Counter(i.status for i in items)
    total_effort = sum(i.est_hours for i in items)

    lines: list[str] = []
    lines.append("# GULA Technical Debt Registry\n")
    lines.append(f"**Generated:** {now}  \n")
    lines.append(f"**Total Items:** {len(items)}  \n")
    lines.append(f"**Total Estimated Effort:** {total_effort:.1f} hours  \n")
    lines.append("")

    # Summary table
    lines.append("## Summary\n")
    lines.append("| Priority | Count | Definition | SLA |")
    lines.append("|----------|-------|------------|-----|")
    sla_map = {
        "P0": ("Blocking — deployment, data loss, security breach", "24 hours"),
        "P1": ("Critical — constitution, patient safety, regulatory", "7 days"),
        "P2": ("Major — best practices, tech debt accumulation", "30 days"),
        "P3": ("Minor — cosmetic, naming, documentation", "90 days"),
    }
    for p in ["P0", "P1", "P2", "P3"]:
        c = counts.get(p, 0)
        if c > 0:
            defn, sla = sla_map.get(p, ("", ""))
            lines.append(f"| **{p}** | {c} | {defn} | {sla} |")
    lines.append("")

    # Status breakdown
    lines.append("### Status Breakdown\n")
    lines.append("| Status | Count |")
    lines.append("|--------|-------|")
    for status in ["open", "fixing", "fixed", "waived"]:
        c = status_counts.get(status, 0)
        if c > 0:
            lines.append(f"| {_STATUS_EMOJI.get(status, '○')} {status.capitalize()} | {c} |")
    lines.append("")

    # Effort breakdown by priority
    effort_by_priority: dict[str, float] = defaultdict(float)
    for item in items:
        effort_by_priority[item.priority] += item.est_hours
    lines.append("### Effort by Priority\n")
    lines.append("| Priority | Est. Hours |")
    lines.append("|----------|------------|")
    for p in ["P0", "P1", "P2", "P3"]:
        eh = effort_by_priority.get(p, 0)
        if eh > 0:
            lines.append(f"| **{p}** | {eh:.1f} |")
    lines.append("")

    # Category breakdown
    cat_counts: dict[str, int] = defaultdict(int)
    cat_effort: dict[str, float] = defaultdict(float)
    for item in items:
        key = item.category
        cat_counts[key] += 1
        cat_effort[key] += item.est_hours

    lines.append("### Category Breakdown\n")
    lines.append("| Category | Count | Est. Hours |")
    lines.append("|----------|-------|------------|")
    for ck in CATEGORY_ORDER:
        label = CATEGORY_LABELS.get(ck, ck)
        cc = cat_counts.get(label, 0)
        if cc > 0:
            lines.append(f"| {label} | {cc} | {cat_effort.get(label, 0):.1f} |")
    lines.append("")

    # Detailed item table
    lines.append("## Detailed Items\n")
    lines.append("| ID | Priority | Category | Description | File | Lines | Est. Hrs | Status | Owner |")
    lines.append("|----|----------|----------|-------------|------|-------|----------|--------|-------|")

    # Sort by priority then category
    sorted_items = sorted(
        items,
        key=lambda x: (0 if x.priority == "P0" else 1 if x.priority == "P1" else 2 if x.priority == "P2" else 3,
                       x.category, x.id),
    )

    for item in sorted_items:
        desc = item.description[:80].replace("|", "\\|")
        fname = item.file[:50] if item.file else "—"
        lines_str = item.lines[:15] if item.lines else "—"
        status_sym = _STATUS_EMOJI.get(item.status, "○")

        lines.append(
            f"| {item.id} | {item.priority} | {item.category} "
            f"| {desc} | {fname} | {lines_str} "
            f"| {item.est_hours:.1f} | {status_sym} {item.status} | {item.owner} |"
        )

    lines.append("")
    lines.append("---")
    lines.append(f"*Registry auto-generated by `scripts/technical_debt_registry.py` at {now}*")

    REGISTRY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ── Reporting ──────────────────────────────────────────────────────────────────

def _print_full_report(items: list[DebtItem]) -> None:
    """Print colorized terminal report."""
    if not items:
        print(f"\n  {_c('green', 'No technical debt items found.')}\n")
        return

    counts = Counter(i.priority for i in items)
    status_counts = Counter(i.status for i in items)
    total_effort = sum(i.est_hours for i in items)

    print()
    print(f"  {_c('bold', '╔══════════════════════════════════════════════════════════════╗')}")
    print(f"  {_c('bold', '║          GULA Technical Debt Classification Registry          ║')}")
    print(f"  {_c('bold', '╚══════════════════════════════════════════════════════════════╝')}")
    print(f"  Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"  Items: {len(items)}  |  Total est. effort: {_c('yellow', f'{total_effort:.1f}h')}")
    print()

    # Priority breakdown bar
    print(f"  {_c('bold', 'Priority Breakdown:')}")
    max_count = max(counts.values()) if counts else 1
    for p in ["P0", "P1", "P2", "P3"]:
        c = counts.get(p, 0)
        bar_len = 30
        filled = int(c / max_count * bar_len) if max_count else 0
        bar = "█" * filled + "░" * (bar_len - filled)
        color = _PRIORITY_COLORS.get(p, _RESET)
        sla = {"P0": "24h", "P1": "7d", "P2": "30d", "P3": "90d"}.get(p, "")
        print(f"  {_c(color, p)}  {_c(color, bar)}  {c:>3}  (SLA: {sla})")
    print()

    # Status breakdown
    print(f"  {_c('bold', 'Status:')}")
    for status in ["open", "fixing", "fixed", "waived"]:
        c = status_counts.get(status, 0)
        sym = _STATUS_EMOJI.get(status, "○")
        print(f"    {sym} {status.capitalize()}: {c}")
    print()

    # Category counts
    cat_counts: dict[str, int] = Counter()
    for item in items:
        cat_counts[item.category] += 1

    print(f"  {_c('bold', 'Categories:')}")
    for ck in CATEGORY_ORDER:
        label = CATEGORY_LABELS.get(ck, ck)
        c = cat_counts.get(label, 0)
        if c > 0:
            print(f"    {label}: {c}")

    # Effort by priority
    effort_by_p: dict[str, float] = defaultdict(float)
    for item in items:
        effort_by_p[item.priority] += item.est_hours
    print()
    print(f"  {_c('bold', 'Effort by Priority:')}")
    for p in ["P0", "P1", "P2", "P3"]:
        if effort_by_p.get(p, 0) > 0:
            print(f"    {_c(_PRIORITY_COLORS.get(p, ''), p)}: {effort_by_p[p]:.1f}h")
    print()

    # Top items by priority
    print(f"  {_c('bold', 'Highest Priority Items (P0/P1):')}")
    print()
    high_priority = [i for i in items if i.priority in ("P0", "P1")]
    if high_priority:
        for item in high_priority:
            color = _PRIORITY_COLORS.get(item.priority, _RESET)
            print(f"  {_c(color, f'[{item.priority}]')} {_c('bold', item.id)}  {item.category}")
            print(f"      {item.description[:120]}")
            if item.file:
                print(f"      File: {item.file}")
            print(f"      Est: {item.est_hours:.1f}h  |  Status: {item.status}  |  Owner: {item.owner}")
            print()
    else:
        print(f"  {_c('green', '  No P0 or P1 items.')}")
        print()

    # All items short table
    sorted_display = sorted(
        items,
        key=lambda x: (0 if x.priority == "P0" else 1 if x.priority == "P1" else 2 if x.priority == "P2" else 3,
                       x.category, x.id),
    )
    print(f"  {_c('bold', 'All Items:')}")
    print(f"  {'ID':<10} {'Pri':<5} {'Category':<28} {'Est':>6} {'Status':<10} {'Owner':<20}")
    print(f"  {'-'*8:<10} {'-'*3:<5} {'-'*26:<28} {'-'*4:>6} {'-'*8:<10} {'-'*18:<20}")

    for item in sorted_display:
        color = _PRIORITY_COLORS.get(item.priority, _RESET)
        sym = _STATUS_EMOJI.get(item.status, "○")
        print(
            f"  {item.id:<10} "
            f"{_c(color, item.priority):<5} "
            f"{item.category:<28} "
            f"{item.est_hours:>5.1f}h "
            f"{sym} {item.status:<7} "
            f"{item.owner:<20}"
        )
    print()

    print(f"  {_c('bold', '┄' * 60)}")
    print(f"  Registry files:")
    print(f"    MD :  {REGISTRY_MD}")
    print(f"    JSON: {REGISTRY_JSON}")
    print()


def _print_summary(items: list[DebtItem]) -> None:
    """Print compact summary view."""
    if not items:
        print(f"\n  {_c('green', 'No technical debt items found.')}\n")
        return

    counts = Counter(i.priority for i in items)
    status_counts = Counter(i.status for i in items)
    open_count = status_counts.get("open", 0)
    total_effort = sum(i.est_hours for i in items)

    print()
    print(f"  {_c('bold', 'GULA Technical Debt Registry — Summary')}")
    print(f"  {'─' * 50}")
    tot = len(items)
    p0 = counts.get("P0", 0)
    p1 = counts.get("P1", 0)
    p2 = counts.get("P2", 0)
    p3 = counts.get("P3", 0)

    print(f"  Items:     {tot} total  ({_c('red', f'P0={p0}')}  "
          f"{_c('magenta', f'P1={p1}')}  "
          f"{_c('yellow', f'P2={p2}')}  "
          f"{_c('cyan', f'P3={p3}')})")
    print(f"  Open:      {open_count}")
    print(f"  Fixing:    {status_counts.get('fixing', 0)}")
    print(f"  Fixed:     {status_counts.get('fixed', 0)}")
    print(f"  Waived:    {status_counts.get('waived', 0)}")
    print(f"  Effort:    {total_effort:.1f} hours est.")
    print()

    # Compact table
    cat_counts: dict[str, int] = Counter()
    cat_effort: dict[str, float] = defaultdict(float)
    for item in items:
        key = item.category
        cat_counts[key] += 1
        cat_effort[key] += item.est_hours

    print(f"  {'Category':<30} {'Count':>6} {'Effort':>8}")
    print(f"  {'─' * 46}")
    for ck in CATEGORY_ORDER:
        label = CATEGORY_LABELS.get(ck, ck)
        c = cat_counts.get(label, 0)
        if c > 0:
            print(f"  {label:<30} {c:>6} {cat_effort.get(label, 0):>7.1f}h")

    print(f"  {'─' * 46}")
    print(f"  {'TOTAL':<30} {tot:>6} {total_effort:>7.1f}h")
    print()

    # Top 5 open items
    open_items = [i for i in items if i.status == "open"]
    if open_items:
        open_items.sort(key=lambda x: (0 if x.priority == "P0" else 1 if x.priority == "P1" else 2, x.est_hours), reverse=True)
        top5 = open_items[:5]
        print(f"  Top 5 open (by priority then effort):")
        for item in top5:
            color = _PRIORITY_COLORS.get(item.priority, _RESET)
            desc = item.description[:80]
            print(f"    {_c(color, f'[{item.priority}]')} {item.id}  {desc}")
        print()

    print(f"  Registry: {REGISTRY_MD}")
    print()


def _search_by_priority(items: list[DebtItem], priority: str) -> list[DebtItem]:
    """Filter items by priority level."""
    priority = priority.upper()
    valid = {"P0", "P1", "P2", "P3"}
    if priority not in valid:
        print(f"  {_c('red', f'Invalid priority: {priority}. Use P0, P1, P2, or P3.')}")
        return []
    return [i for i in items if i.priority == priority]


# ── Main ───────────────────────────────────────────────────────────────────────

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="GULA Technical Debt Classification Registry",
    )
    parser.add_argument(
        "--summary", action="store_true",
        help="Compact summary view",
    )
    parser.add_argument(
        "--refresh", action="store_true",
        help="Re-scan and re-classify all technical debt items",
    )
    parser.add_argument(
        "--search", type=str, default=None,
        help="Filter by priority (P0, P1, P2, P3)",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output JSON only (to stdout)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.json:
        global _USE_COLOR
        _USE_COLOR = False

    # Load existing registry to preserve status
    existing = _load_existing_registry()
    existing_map: dict[str, DebtItem] = {}
    for item in existing:
        existing_map[item.id] = item

    counter = [1]
    all_items: list[DebtItem] = list(existing)
    highest_existing = 0
    for item in existing:
        m = re.match(r"TD-(\d+)", item.id)
        if m:
            highest_existing = max(highest_existing, int(m.group(1)))
    counter[0] = highest_existing + 1

    remake_map = {item.id: item for item in existing}

    if args.refresh or not existing:
        all_items = []

        # 1. Run compliance engine
        compliance_results = _run_compliance_engine()
        items_from_compliance = _debt_from_compliance(
            compliance_results, remake_map, counter,
        )
        all_items.extend(items_from_compliance)

        # 2. Parse constitution contradictions
        contradictions = _parse_constitution_contradictions()
        items_from_constitution = _debt_from_constitution(
            contradictions, remake_map, counter,
        )
        all_items.extend(items_from_constitution)

        # 3. Run scorecard
        scorecard_data = _run_scorecard()
        items_from_scorecard = _debt_from_scorecard(
            scorecard_data, remake_map, counter,
        )
        all_items.extend(items_from_scorecard)

        # Deduplicate by source description
        seen: set[str] = set()
        deduped: list[DebtItem] = []
        for item in all_items:
            key = f"{item.source}:{item.description[:100]}"
            if key not in seen:
                seen.add(key)
                deduped.append(item)
            else:
                # Merge status if duplicate
                for existing_item in existing:
                    if existing_item.description == item.description:
                        item.status = existing_item.status
                        item.owner = existing_item.owner
                        break
                deduped.append(item)
        all_items = deduped

        # Write registry files
        _write_registry_json(all_items)
        _write_registry_md(all_items)

    else:
        # Load from existing files
        if not all_items:
            all_items = existing
        if not all_items and REGISTRY_JSON.exists():
            all_items = _load_existing_registry()

    # Apply search filter
    if args.search:
        all_items = _search_by_priority(all_items, args.search)

    # Output
    if args.json:
        registry_data = {
            "meta": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "total_items": len(all_items),
                "by_priority": dict(Counter(i.priority for i in all_items)),
                "by_status": dict(Counter(i.status for i in all_items)),
            },
            "items": [i.to_dict() for i in all_items],
        }
        print(json.dumps(registry_data, indent=2, ensure_ascii=False))
        return 0

    if args.summary:
        _print_summary(all_items)
    else:
        _print_full_report(all_items)

    return 0


if __name__ == "__main__":
    sys.exit(main())
