"""Phase 15 — Technical Debt Engine.

Automatically detect architecture drift, knowledge drift, dependency drift,
configuration drift, dead code, duplicate code, duplicate knowledge, large
modules, outdated documentation, security debt, performance debt, and
maintainability debt. Every finding is versioned, auditable, and searchable.
"""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from .core import REPO_ROOT, Finding, Severity

LARGE_MODULE_LINES = 500
DUPLICATE_BLOCK_LINES = 4


@dataclass
class ModuleStats:
    """Per-module statistics used by the debt detectors."""

    path: str
    lines: int = 0
    has_docstring: bool = False
    todo_count: int = 0
    secret_pattern_count: int = 0
    nested_loop_count: int = 0


def _stats_for(path: Path) -> ModuleStats | None:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    lines = text.splitlines()
    return ModuleStats(
        path=str(path.relative_to(REPO_ROOT)),
        lines=len(lines),
        has_docstring=bool(re.search(r'^\s*("""|\'\'\')', text, re.MULTILINE)),
        todo_count=len(re.findall(r"\b(TODO|FIXME)\b", text)),
        secret_pattern_count=len(re.findall(
            r"(secret\s*=\s*['\"][^'\"]+|api[_-]?key\s*=\s*['\"][^'\"]+|BEGIN (RSA|PRIVATE) KEY)",
            text,
            re.IGNORECASE,
        )),
        nested_loop_count=len(re.findall(
            r"for .+:\n(\s+for .+:\n)", text,
        )),
    )


def collect_module_stats(patterns: Iterable[str]) -> list[ModuleStats]:
    """Collect statistics for every matching source module."""
    stats: list[ModuleStats] = []
    for pattern in patterns:
        for path in sorted(REPO_ROOT.glob(pattern)):
            if path.is_file():
                stats.append(_stats_for(path))
    return [s for s in stats if s is not None]


def large_modules(stats: list[ModuleStats], threshold: int = LARGE_MODULE_LINES) -> list[Finding]:
    """Detect modules exceeding the maintainability line budget."""
    findings: list[Finding] = []
    for module in sorted(stats, key=lambda s: -s.lines):
        if module.lines > threshold:
            findings.append(Finding(
                id=f"DEBT-LARGE-{len(findings) + 1:04d}",
                title=f"Large module: {module.path}",
                severity=Severity.LOW,
                category="large-modules",
                detail=f"{module.lines} lines > {threshold}",
                evidence=module.path,
                proposed_fix="Split the module along bounded-context boundaries",
            ))
    return findings


def missing_docstrings(stats: list[ModuleStats]) -> list[Finding]:
    """Detect modules without a module docstring (maintainability debt)."""
    findings: list[Finding] = []
    for module in sorted(stats, key=lambda s: s.path):
        if not module.has_docstring:
            findings.append(Finding(
                id=f"DEBT-DOC-{len(findings) + 1:04d}",
                title=f"Missing module docstring: {module.path}",
                severity=Severity.LOW,
                category="maintainability-debt",
                detail="Module has no docstring describing its purpose",
                evidence=module.path,
                proposed_fix="Add a module docstring",
            ))
    return findings


def todo_density(stats: list[ModuleStats]) -> list[Finding]:
    """Detect TODO/FIXME markers left in active code."""
    findings: list[Finding] = []
    for module in sorted(stats, key=lambda s: -s.todo_count):
        if module.todo_count:
            findings.append(Finding(
                id=f"DEBT-TODO-{len(findings) + 1:04d}",
                title=f"TODO/FIXME markers: {module.path}",
                severity=Severity.MEDIUM if module.todo_count > 3 else Severity.LOW,
                category="maintainability-debt",
                detail=f"{module.todo_count} markers",
                evidence=module.path,
                proposed_fix="Resolve markers or file tracked issues",
            ))
    return findings


def security_debt(stats: list[ModuleStats]) -> list[Finding]:
    """Detect hardcoded secret-like patterns (security debt)."""
    findings: list[Finding] = []
    for module in sorted(stats, key=lambda s: -s.secret_pattern_count):
        if module.secret_pattern_count:
            findings.append(Finding(
                id=f"DEBT-SEC-{len(findings) + 1:04d}",
                title=f"Possible hardcoded secret: {module.path}",
                severity=Severity.HIGH,
                category="security-debt",
                detail=f"{module.secret_pattern_count} secret-like patterns",
                evidence=module.path,
                proposed_fix="Move values into environment variables or a secret store",
            ))
    return findings


def performance_debt(stats: list[ModuleStats]) -> list[Finding]:
    """Detect nested loops (O(n^2)) inside modules (performance debt)."""
    findings: list[Finding] = []
    for module in sorted(stats, key=lambda s: -s.nested_loop_count):
        if module.nested_loop_count:
            findings.append(Finding(
                id=f"DEBT-PERF-{len(findings) + 1:04d}",
                title=f"Nested loops: {module.path}",
                severity=Severity.MEDIUM,
                category="performance-debt",
                detail=f"{module.nested_loop_count} nested loop(s)",
                evidence=module.path,
                proposed_fix="Benchmark before optimization; verify with tests",
            ))
    return findings


def duplicate_code(blocks: dict[str, list[str]]) -> list[Finding]:
    """Detect near-duplicate code blocks shared by multiple modules."""
    findings: list[Finding] = []
    seen: set[str] = set()
    for block, locations in blocks.items():
        if len(locations) > 1 and block not in seen:
            seen.add(block)
            findings.append(Finding(
                id=f"DEBT-DUPCODE-{len(findings) + 1:04d}",
                title="Duplicated code block",
                severity=Severity.MEDIUM,
                category="duplicate-code",
                detail=f"Block present in {len(locations)} locations",
                evidence=", ".join(sorted(locations)),
                proposed_fix="Extract the shared block into a Kernel/shared utility",
            ))
    return findings


def extract_duplicate_blocks(
    module_contents: dict[str, str],
    min_lines: int = DUPLICATE_BLOCK_LINES,
) -> dict[str, list[str]]:
    """Map normalized line-blocks to the modules that contain them."""
    buckets: dict[str, list[str]] = defaultdict(list)
    for module, content in module_contents.items():
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        for i in range(len(lines) - min_lines + 1):
            block = tuple(lines[i : i + min_lines])
            buckets[str(block)].append(module)
    return {block: locations for block, locations in buckets.items() if len(locations) > 1}


def dead_code(import_graph: dict[str, list[str]], entrypoints: Iterable[str]) -> list[Finding]:
    """Detect modules never reached from any entrypoint (dead code)."""
    reached: set[str] = set(entrypoints)
    changed = True
    while changed:
        changed = False
        for module in list(reached):
            for imported in import_graph.get(module, []):
                if imported not in reached:
                    reached.add(imported)
                    changed = True
    findings: list[Finding] = []
    for module in sorted(import_graph):
        if module not in reached:
            findings.append(Finding(
                id=f"DEBT-DEAD-{len(findings) + 1:04d}",
                title=f"Dead module: {module}",
                severity=Severity.MEDIUM,
                category="dead-code",
                detail="Module is never reached from an entrypoint",
                evidence=module,
                proposed_fix="Remove the module or document why it is dormant",
            ))
    return findings


def outdated_docs(module_paths: list[str], doc_keywords: list[str]) -> list[Finding]:
    """Detect modules without a matching documentation artifact."""
    findings: list[Finding] = []
    for module in sorted(module_paths):
        stem = Path(module).stem
        matched = any(stem.lower() in keyword.lower() for keyword in doc_keywords)
        if not matched:
            findings.append(Finding(
                id=f"DEBT-ODOC-{len(findings) + 1:04d}",
                title=f"Outdated documentation: {module}",
                severity=Severity.LOW,
                category="outdated-docs",
                detail="No documentation artifact references this module",
                evidence=module,
                proposed_fix="Document the public surface of the module",
            ))
    return findings


def knowledge_drift(registry_ids: list[str], index_ids: list[str]) -> list[Finding]:
    """Detect knowledge artifacts registered but missing from the index."""
    indexed = set(index_ids)
    findings: list[Finding] = []
    for artifact_id in sorted(registry_ids):
        if artifact_id not in indexed:
            findings.append(Finding(
                id=f"DEBT-KDRIFT-{len(findings) + 1:04d}",
                title=f"Knowledge drift: {artifact_id}",
                severity=Severity.MEDIUM,
                category="knowledge-drift",
                detail="Artifact is registered but not present in the knowledge index",
                evidence=artifact_id,
                proposed_fix="Regenerate the index (make brain) after registering the artifact",
            ))
    return findings


def dependency_drift(declared: list[str], used: list[str]) -> list[Finding]:
    """Detect declared dependencies that are never used (dependency drift)."""
    findings: list[Finding] = []
    for dependency in sorted(set(declared)):
        if dependency not in set(used):
            findings.append(Finding(
                id=f"DEBT-DDEP-{len(findings) + 1:04d}",
                title=f"Unused dependency: {dependency}",
                severity=Severity.MEDIUM,
                category="dependency-drift",
                detail="Declared dependency is never used",
                evidence=dependency,
                proposed_fix="Remove the dependency or document its purpose",
            ))
    return findings


def configuration_drift(declared: list[str], present: list[str]) -> list[Finding]:
    """Detect configuration keys declared but missing from the environment."""
    present_set = set(present)
    findings: list[Finding] = []
    for key in sorted(set(declared)):
        if key not in present_set:
            findings.append(Finding(
                id=f"DEBT-CFG-{len(findings) + 1:04d}",
                title=f"Missing configuration: {key}",
                severity=Severity.MEDIUM,
                category="configuration-drift",
                detail="Declared configuration key is not present",
                evidence=key,
                proposed_fix="Provide the configuration value or a documented default",
            ))
    return findings


def architecture_drift(import_cycles: list[list[str]]) -> list[Finding]:
    """Detect import cycles between modules (architecture drift)."""
    findings: list[Finding] = []
    for cycle in sorted(import_cycles, key=lambda c: " -> ".join(c)):
        findings.append(Finding(
            id=f"DEBT-ARCH-{len(findings) + 1:04d}",
            title="Import cycle (architecture drift)",
            severity=Severity.HIGH,
            category="architecture-drift",
            detail=" -> ".join(cycle),
            evidence=" -> ".join(cycle),
            proposed_fix="Move the shared dependency into the Kernel/shared core",
        ))
    return findings
