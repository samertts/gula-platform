#!/usr/bin/env python3
"""
GULA Architecture Compliance Engine
====================================
Enforces Engineering Constitution PART 5 dependency rules + PART 2 naming/quality rules.

Validates architecture compliance across the entire monorepo using AST-based analysis.

Rules implemented:
  L1 — Layer violation detection (routes→services→domain)
  L2 — Circular dependency detection
  L3 — Forbidden import detection
  L4 — Cross-domain bounded context leakage
  L5 — File size warnings (>1000 lines, >100 line functions)
  L6 — Naming convention checks (snake_case, PascalCase, UPPER_CASE)
  L7 — Documentation checks (module docstrings, route docstrings)

Output:
  - Colorized terminal output (auto-detected)
  - Machine-readable JSON (--json)
  - Summary compliance score 0-100
  - Rule-by-rule results (PASS / WARNING / FAIL)

Usage:
  python scripts/architecture_compliance_engine.py
  python scripts/architecture_compliance_engine.py --json
  python scripts/architecture_compliance_engine.py --verbose
  python scripts/architecture_compliance_engine.py --focus L3
  python scripts/architecture_compliance_engine.py --exclude-dirs tests,migrations

Exit codes:
  0 — all rules PASS (or WARNING only)
  1 — one or more rules FAIL
"""

from __future__ import annotations

import argparse
import ast
import json
import logging
import os
import pathlib
import re
import sys
from collections import defaultdict
from typing import Any

logger = logging.getLogger("architecture_compliance_engine")

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
BACKEND_APP = REPO_ROOT / "backend" / "app"
DEFAULT_EXCLUDE = {"__pycache__", "__init__.py", ".mypy_cache", ".pytest_cache"}

_RESET = "\033[0m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_RED = "\033[91m"
_CYAN = "\033[96m"
_BOLD = "\033[1m"
_WHITE = "\033[97m"
_MAGENTA = "\033[95m"

_USE_COLOR = sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    if not _USE_COLOR:
        return text
    palette = {
        "green": _GREEN, "yellow": _YELLOW, "red": _RED,
        "cyan": _CYAN, "bold": _BOLD, "white": _WHITE, "reset": _RESET,
        "magenta": _MAGENTA,
    }
    return f"{palette.get(code, _RESET)}{text}{_RESET}"


PASS = "PASS"
WARNING = "WARNING"
FAIL = "FAIL"
STATUS_ORDER = {PASS: 0, WARNING: 1, FAIL: 2}

RuleResult = dict[str, Any]


def make_rule(
    rule_id: str,
    title: str,
    status: str,
    details: list[str] | None = None,
    passed: int = 0,
    total: int = 0,
) -> RuleResult:
    return {
        "rule": rule_id,
        "title": title,
        "status": status,
        "details": details or [],
        "passed": passed,
        "total": total,
    }


# ── File discovery ────────────────────────────────────────────────────────

def discover_python_files(
    root: pathlib.Path,
    exclude_dirs: set[str] | None = None,
) -> list[pathlib.Path]:
    exclude = DEFAULT_EXCLUDE | (exclude_dirs or set())
    files: list[pathlib.Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        rel = pathlib.Path(dirpath).relative_to(root)
        parts = set(rel.parts)
        if parts & exclude:
            continue
        if any(p.startswith(".") for p in rel.parts):
            continue
        for fn in filenames:
            if fn.endswith(".py") and fn not in exclude:
                files.append(pathlib.Path(dirpath) / fn)
    return sorted(files)


def module_path(filepath: pathlib.Path, root: pathlib.Path) -> str:
    """Convert a file path to a dotted Python module path relative to root."""
    rel = filepath.relative_to(root)
    parts = list(rel.parts)
    if parts[-1] == "__init__.py":
        parts.pop()
    else:
        parts[-1] = parts[-1].removesuffix(".py")
    return ".".join(parts)


def get_file_package(filepath: pathlib.Path, root: pathlib.Path) -> str | None:
    """Determine the top-level package name (e.g. 'routes', 'services')."""
    rel = filepath.relative_to(root)
    parts = rel.parts
    if len(parts) >= 1:
        first = parts[0]
        if first.endswith(".py"):
            return None
        return first
    return None


# ── AST-based import extraction ──────────────────────────────────────────

class ImportVisitor(ast.NodeVisitor):
    """Collects all import statements from an AST."""

    def __init__(self) -> None:
        self.imports: list[dict[str, Any]] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append({
                "type": "import",
                "module": alias.name,
                "alias": alias.asname,
                "lineno": node.lineno,
            })

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        for alias in node.names:
            self.imports.append({
                "type": "import_from",
                "module": module,
                "name": alias.name,
                "alias": alias.asname,
                "lineno": node.lineno,
            })


def parse_imports(filepath: pathlib.Path) -> list[dict[str, Any]]:
    """Parse imports from a Python file using AST."""
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8"), filename=str(filepath))
    except SyntaxError:
        return []
    visitor = ImportVisitor()
    visitor.visit(tree)
    return visitor.imports


def get_module_layer(module: str, root: pathlib.Path) -> str | None:
    """Determine which layer a dotted module belongs to.

    Maps module paths to canonical layer names.
    """
    if module.startswith("app.routes") or module.startswith("..routes"):
        return "routes"
    if module.startswith("app.services") or module.startswith("..services"):
        return "services"
    if module.startswith("app.domain") or module.startswith("..domain"):
        return "domain"
    if module.startswith("app.models") or module.startswith("..models"):
        return "models"
    if module.startswith("app.core") or module.startswith("..core"):
        return "core"
    if module.startswith("app.security") or module.startswith("..security"):
        return "security"
    if module.startswith("app.database") or module == "..database":
        return "database"
    if module.startswith("app.config") or module == "..config":
        return "config"
    if module.startswith("app.audit") or module.startswith("..audit"):
        return "audit"
    if module.startswith("app.notifications") or module.startswith("..notifications"):
        return "notifications"
    if module.startswith("app.tasks") or module.startswith("..tasks"):
        return "tasks"
    if module.startswith("app.gateways") or module.startswith("..gateways"):
        return "gateways"
    if module.startswith("app.edge") or module.startswith("..edge"):
        return "edge"
    if module.startswith("app.firewall") or module.startswith("..firewall"):
        return "firewall"
    if module.startswith("app.integration") or module.startswith("..integration"):
        return "integration"
    if module.startswith("app.kernel") or module.startswith("..kernel"):
        return "kernel"
    if module.startswith("app.ehr") or module.startswith("..ehr"):
        return "ehr"
    if module.startswith("app.lims") or module.startswith("..lims"):
        return "lims"
    if module.startswith("app.health_data") or module.startswith("..health_data"):
        return "health_data"
    if module.startswith("app.ai") or module.startswith("..ai"):
        return "ai"
    for ctx_pkg in ("ehr", "lims", "health_data", "clinical", "national_data",
                    "biomedical", "blood_bank", "care_continuum", "citizen_platform",
                    "command_center", "command_intelligence", "critical_care",
                    "governance", "hospital", "interoperability", "knowledge_graph",
                    "lifecycle_platform", "nursing", "pharmacy", "public_health",
                    "radiology", "research_platform", "simulation", "trust",
                    "approvals", "certification", "contracts", "engineering",
                    "forms", "legal", "national", "nhdw", "optimizer", "pilot_platform",
                    "platform", "policies", "roadmap", "rules", "skills", "validation",
                    "workflows", "financial", "ai_fabric", "capabilities",
                    "constraints", "control_plane", "dependencies", "ems",
                    "kernel", "lifecycle_platform", "national_data", "nhdw"):
        if module.startswith(f"app.{ctx_pkg}") or module.startswith(f"..{ctx_pkg}"):
            return "bounded_context"
    return None


def is_framework_import(module: str) -> bool:
    """Check if a module is a framework/library import."""
    frameworks = {
        "fastapi", "pydantic", "sqlalchemy", "alembic", "redis",
        "starlette", "flask", "django", "tortoise", "beanie",
        "motor", "aioredis", "aiohttp", "httpx", "requests",
        "numpy", "pandas", "scipy", "sklearn", "tensorflow",
        "torch", "celery", "rq", "huey", "dramatiq",
    }
    top = module.split(".")[0]
    return top in frameworks


# ── Rule L1: Layer violation detection ───────────────────────────────────

LAYER_RULES: dict[str, set[str]] = {
    "routes": {"services", "security", "gateways", "config"},
    "services": {"domain", "models", "services", "security", "gateways", "core",
                 "config", "database", "notifications", "tasks", "audit",
                 "integration", "edge", "firewall", "kernel", "ai", "bounded_context"},
    "domain": set(),
    "models": {"core", "config", "database", "security"},
    "core": {"config", "database", "security", "core"},
    "security": {"config", "core", "database"},
}

ALLOWED_LAYER_IMPORTS: dict[str, set[str]] = {
    "routes": {"services", "security", "gateways"},
    "services": {"domain", "models", "audit", "notifications", "core", "security",
                 "config", "database", "gateways", "integration", "edge", "kernel",
                 "ai", "bounded_context", "tasks"},
    "domain": set(),
    "models": {"core", "config", "database", "security"},
    "core": {"config", "database", "security", "core"},
    "security": {"config", "core", "database"},
}

# Routes should NOT import from these layers directly
ROUTE_FORBIDDEN_LAYERS = {"models", "domain", "core", "database"}

# Services should NOT import from routes
SERVICE_FORBIDDEN_LAYERS = {"routes"}

# Domain should NOT import from anything except standard lib
DOMAIN_FORBIDDEN_LAYERS = {"routes", "services", "models", "core", "security",
                           "database", "gateways", "integration", "audit",
                           "notifications", "tasks", "edge", "firewall",
                           "kernel", "ai", "bounded_context", "config"}

# Models should NOT import from routes or services
MODEL_FORBIDDEN_LAYERS = {"routes", "services"}


def check_layer_violations(
    root: pathlib.Path,
    exclude_dirs: set[str],
) -> RuleResult:
    files = discover_python_files(root, exclude_dirs)
    violations: list[str] = []
    checked = 0

    for fp in files:
        pkg = get_file_package(fp, root)
        if pkg is None:
            continue
        if pkg not in LAYER_RULES:
            continue

        imports = parse_imports(fp)
        module_str = module_path(fp, root)
        checked += 1

        for imp in imports:
            mod = imp["module"]
            target_layer = get_module_layer(mod, root)
            if target_layer is None:
                continue

            if pkg == "routes" and target_layer in ROUTE_FORBIDDEN_LAYERS:
                violations.append(
                    f"{module_str}:{imp['lineno']} routes imports from {target_layer} "
                    f"({imp['module']}.{imp.get('name', '')})"
                )
            elif pkg == "services" and target_layer in SERVICE_FORBIDDEN_LAYERS:
                violations.append(
                    f"{module_str}:{imp['lineno']} services imports from routes "
                    f"({imp['module']}.{imp.get('name', '')})"
                )
            elif pkg == "domain" and target_layer in DOMAIN_FORBIDDEN_LAYERS:
                violations.append(
                    f"{module_str}:{imp['lineno']} domain imports from {target_layer} "
                    f"({imp['module']}.{imp.get('name', '')})"
                )
            elif pkg == "domain" and is_framework_import(mod):
                violations.append(
                    f"{module_str}:{imp['lineno']} domain imports framework "
                    f"({imp['module']}.{imp.get('name', '')})"
                )
            elif pkg == "models" and target_layer in MODEL_FORBIDDEN_LAYERS:
                violations.append(
                    f"{module_str}:{imp['lineno']} models imports from {target_layer} "
                    f"({imp['module']}.{imp.get('name', '')})"
                )

    status = PASS
    if violations:
        status = FAIL

    detail_lines = []
    if violations:
        detail_lines.append(f"Found {len(violations)} layer violation(s):")
        detail_lines.extend(f"  - {v}" for v in violations)
    else:
        detail_lines.append("No layer violations detected.")

    return make_rule(
        "L1", "Layer Violation Detection",
        status, detail_lines,
        passed=checked - len(violations), total=checked,
    )


# ── Rule L2: Circular dependency detection ───────────────────────────────

def build_import_graph(
    root: pathlib.Path,
    exclude_dirs: set[str],
) -> dict[str, set[str]]:
    graph: dict[str, set[str]] = defaultdict(set)
    files = discover_python_files(root, exclude_dirs)
    for fp in files:
        src_module = module_path(fp, root)
        imports = parse_imports(fp)
        for imp in imports:
            mod = imp["module"]
            target_module = mod.lstrip(".")
            if target_module.startswith("app."):
                target_module = target_module[4:]
            elif target_module.startswith(".."):
                continue
            elif "." in target_module:
                parts = target_module.split(".")
                resolved = resolve_relative_import(src_module, imp["module"], imp.get("name"))
                if resolved:
                    target_module = resolved
                    if target_module.startswith("app."):
                        target_module = target_module[4:]
                    graph[src_module].add(target_module)
                    continue
            if target_module.startswith("app."):
                target_module = target_module[4:]
            if target_module and not target_module.startswith("_"):
                graph[src_module].add(target_module)
    return graph


def resolve_relative_import(
    source_module: str,
    import_module: str,
    import_name: str | None,
) -> str | None:
    """Resolve a relative import to an absolute module path."""
    if not import_module.startswith("."):
        return None
    level = 0
    while import_module[level] == ".":
        level += 1
    base_parts = source_module.split(".")
    if level > len(base_parts):
        return None
    base = ".".join(base_parts[:-level])
    suffix = import_module[level:]
    if suffix:
        return f"app.{base}.{suffix}" if base else f"app.{suffix}"
    if import_name:
        return f"app.{base}.{import_name}" if base else f"app.{import_name}"
    return None


def find_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    """Find all cycles in a directed graph using DFS."""
    cycles: list[list[str]] = []
    visited: set[str] = set()
    rec_stack: list[str] = []
    rec_set: set[str] = set()

    def dfs(node: str) -> None:
        visited.add(node)
        rec_stack.append(node)
        rec_set.add(node)

        for neighbor in graph.get(node, set()):
            if neighbor not in visited:
                dfs(neighbor)
            elif neighbor in rec_set:
                # Found a cycle — extract it
                idx = rec_stack.index(neighbor)
                cycle = rec_stack[idx:] + [neighbor]
                cycles.append(cycle)

        rec_stack.pop()
        rec_set.discard(node)

    for node in graph:
        if node not in visited:
            dfs(node)

    return cycles


def check_circular_dependencies(
    root: pathlib.Path,
    exclude_dirs: set[str],
) -> RuleResult:
    graph = build_import_graph(root, exclude_dirs)
    cycles = find_cycles(graph)

    status = PASS
    details: list[str] = []

    if cycles:
        status = FAIL
        details.append(f"Found {len(cycles)} circular dependenc(ies):")
        for cycle in cycles:
            cycle_str = " → ".join(cycle)
            details.append(f"  - {cycle_str}")
    else:
        details.append("No circular dependencies detected.")

    return make_rule(
        "L2", "Circular Dependency Detection",
        status, details,
        passed=len(cycles), total=len(cycles),
    )


# ── Rule L3: Forbidden import detection ──────────────────────────────────

FORBIDDEN_PATTERNS: dict[str, list[dict[str, Any]]] = {
    "routes": [
        {"pattern": re.compile(r"(from\s+.*\.database\s+import|import\s+.*\.database)"),
         "desc": "routes importing from database directly"},
        {"pattern": re.compile(r"(from\s+.*\.models\s+import|import\s+.*\.models)"),
         "desc": "routes importing from models directly"},
        {"pattern": re.compile(r"(from\s+.*\.core\s+import|import\s+.*\.core)"),
         "desc": "routes importing from core directly"},
    ],
    "services": [
        {"pattern": re.compile(r"(from\s+.*\.routes\s+import|import\s+.*\.routes)"),
         "desc": "services importing from routes"},
    ],
    "domain": [
        {"pattern": re.compile(r"(from\s+fastapi|import\s+fastapi)"),
         "desc": "domain importing from fastapi framework"},
        {"pattern": re.compile(r"(from\s+sqlalchemy|import\s+sqlalchemy)"),
         "desc": "domain importing from sqlalchemy"},
        {"pattern": re.compile(r"(from\s+.*\.(routes|services|models|core|security|database)\s+import|import\s+.*\.(routes|services|models|core|security|database))"),
         "desc": "domain importing from application layer"},
    ],
    "domain_default": [
        {"pattern": re.compile(r"(from\s+fastapi|import\s+fastapi)"),
         "desc": "domain importing from fastapi framework"},
        {"pattern": re.compile(r"(from\s+sqlalchemy|import\s+sqlalchemy)"),
         "desc": "domain importing from sqlalchemy"},
        {"pattern": re.compile(r"(from\s+redis|import\s+redis)"),
         "desc": "domain importing from redis"},
        {"pattern": re.compile(r"(from\s+.*\.(routes|services|models|core|security|database|gateways|integration|notifications|tasks|edge|firewall|kernel|audit)\s+import|import\s+.*\.(routes|services|models|core|security|database|gateways|integration|notifications|tasks|edge|firewall|kernel|audit))"),
         "desc": "domain importing from application layers"},
    ],
    "all": [
        {"pattern": re.compile(r"Session\s*=\s*"),
         "desc": "direct Session assignment outside database.py",
         "exclude_files": {"database.py"}},
    ],
}

# Define bounded contexts (subdomains/bounded contexts that should be isolated)
BOUNDED_CONTEXTS: dict[str, set[str]] = {
    "ehr": {"ehr"},
    "lims": {"lims"},
    "health_data": {"health_data"},
    "clinical": {"clinical"},
    "national_data": {"national_data"},
    "biomedical": {"biomedical"},
    "blood_bank": {"blood_bank"},
    "care_continuum": {"care_continuum"},
    "citizen_platform": {"citizen_platform"},
    "command_center": {"command_center"},
    "critical_care": {"critical_care"},
    "governance": {"governance"},
    "hospital": {"hospital"},
    "interoperability": {"interoperability"},
    "knowledge_graph": {"knowledge_graph"},
    "nursing": {"nursing"},
    "pharmacy": {"pharmacy"},
    "public_health": {"public_health"},
    "radiology": {"radiology"},
    "research_platform": {"research_platform"},
    "simulation": {"simulation"},
    "trust": {"trust"},
    "approvals": {"approvals"},
    "certification": {"certification"},
    "contracts": {"contracts"},
    "engineering": {"engineering"},
    "forms": {"forms"},
    "legal": {"legal"},
    "national": {"national"},
    "nhdw": {"nhdw"},
    "optimizer": {"optimizer"},
    "pilot_platform": {"pilot_platform"},
    "platform": {"platform"},
    "policies": {"policies"},
    "roadmap": {"roadmap"},
    "rules": {"rules"},
    "skills": {"skills"},
    "validation": {"validation"},
    "workflows": {"workflows"},
    "financial": {"financial"},
    "ai_fabric": {"ai_fabric"},
    "capabilities": {"capabilities"},
    "constraints": {"constraints"},
    "control_plane": {"control_plane"},
    "dependencies": {"dependencies"},
    "ems": {"ems"},
    "kernel": {"kernel"},
    "lifecycle_platform": {"lifecycle_platform"},
    "ai": {"ai"},
    "command_intelligence": {"command_intelligence"},
}

# These top-level directories are NOT bounded contexts — they are cross-cutting layers
_CORE_LAYER_NAMES = {
    "routes", "services", "models", "domain", "core", "security",
    "database", "config", "audit", "notifications", "tasks",
    "gateways", "integration", "edge", "firewall", "kernel", "ai",
}

_ALL_SOURCE_PACKAGES = set(BOUNDED_CONTEXTS.keys()) | _CORE_LAYER_NAMES

DANGEROUS_RAW_IMPORTS = {
    "redis": {"core", "security", "config"} | _ALL_SOURCE_PACKAGES,
    "sqlalchemy.orm": {"models", "database", "core", "security", "services",
                       "routes", "gateways", "integration", "edge", "firewall",
                       "kernel", "audit", "notifications", "tasks", "ai",
                       "domain"} | _ALL_SOURCE_PACKAGES,
}


def check_forbidden_imports(
    root: pathlib.Path,
    exclude_dirs: set[str],
) -> RuleResult:
    files = discover_python_files(root, exclude_dirs)
    violations: list[str] = []
    checked = 0

    for fp in files:
        pkg = get_file_package(fp, root)
        if pkg is None:
            continue
        fname = fp.name
        content = fp.read_text(encoding="utf-8", errors="replace")
        checked += 1

        module_str = module_path(fp, root)

        # Package-specific forbidden patterns
        patterns = FORBIDDEN_PATTERNS.get(pkg, [])
        if pkg == "domain":
            patterns = FORBIDDEN_PATTERNS["domain_default"]

        for rule in patterns:
            exclude_files = rule.get("exclude_files", set())
            if fname in exclude_files:
                continue
            matches = rule["pattern"].findall(content)
            if matches:
                # Find line number of first match
                for lineno, line in enumerate(content.splitlines(), 1):
                    if rule["pattern"].search(line):
                        violations.append(
                            f"{module_str}:{lineno} {rule['desc']} ({line.strip()[:80]})"
                        )
                        break
                else:
                    violations.append(
                        f"{module_str} {rule['desc']} (pattern matched)"
                    )

        # Check raw dangerous imports
        imports = parse_imports(fp)
        for imp in imports:
            mod = imp["module"]
            for dangerous_mod, allowed_pkgs in DANGEROUS_RAW_IMPORTS.items():
                if mod == dangerous_mod or mod.startswith(dangerous_mod + "."):
                    if pkg not in allowed_pkgs:
                        violations.append(
                            f"{module_str}:{imp['lineno']} forbidden import '{mod}' "
                            f"in {pkg} layer (only allowed in: {', '.join(allowed_pkgs)})"
                        )
                        break

    status = PASS
    if violations:
        status = FAIL

    detail_lines = []
    if violations:
        detail_lines.append(f"Found {len(violations)} forbidden import(s):")
        detail_lines.extend(f"  - {v}" for v in violations)
    else:
        detail_lines.append("No forbidden imports detected.")

    return make_rule(
        "L3", "Forbidden Import Detection",
        status, detail_lines,
        passed=checked - len(violations), total=checked,
    )


# ── Rule L4: Cross-domain bounded context leakage ────────────────────────

CROSS_CONTEXT_ALLOWLIST: dict[str, set[str]] = {
    "lims": {"ehr", "health_data", "clinical", "knowledge_graph", "interoperability"},
    "ehr": {"lims", "health_data", "clinical", "knowledge_graph", "interoperability"},
    "health_data": {"ehr", "lims"},
    "clinical": {"ehr", "lims", "knowledge_graph"},
    "knowledge_graph": set(),
}


def check_cross_domain_violations(
    root: pathlib.Path,
    exclude_dirs: set[str],
) -> RuleResult:
    files = discover_python_files(root, exclude_dirs)
    violations: list[str] = []
    checked = 0

    for fp in files:
        pkg = get_file_package(fp, root)
        if pkg is None:
            continue
        if pkg not in BOUNDED_CONTEXTS:
            continue

        checked += 1
        module_str = module_path(fp, root)
        imports = parse_imports(fp)
        own_contexts = BOUNDED_CONTEXTS[pkg]
        allowlist = CROSS_CONTEXT_ALLOWLIST.get(pkg, set())

        for imp in imports:
            mod = imp["module"]
            for ctx_name, ctx_pkgs in BOUNDED_CONTEXTS.items():
                if ctx_name == pkg:
                    continue
                for ctx_pkg in ctx_pkgs:
                    if mod.startswith(ctx_pkg) or mod.startswith(f"app.{ctx_pkg}"):
                        if ctx_name not in allowlist:
                            violations.append(
                                f"{module_str}:{imp['lineno']} bounded context leakage: "
                                f"'{pkg}' imports from '{ctx_name}' "
                                f"({imp['module']}.{imp.get('name', '')})"
                            )
                        break

    status = PASS
    if violations:
        status = FAIL

    detail_lines = []
    if violations:
        detail_lines.append(f"Found {len(violations)} cross-domain violation(s):")
        detail_lines.extend(f"  - {v}" for v in violations)
    else:
        detail_lines.append("No cross-domain violations detected.")

    return make_rule(
        "L4", "Cross-Domain Bounded Context Leakage",
        status, detail_lines,
        passed=checked - len(violations), total=checked,
    )


# ── Rule L5: File size / function size warnings ──────────────────────────

class FunctionSizeVisitor(ast.NodeVisitor):
    """Counts lines in each function definition."""

    def __init__(self) -> None:
        self.functions: list[tuple[str, int, int]] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node.body:
            first = node.body[0].lineno
            last = node.body[-1].end_lineno or node.body[-1].lineno
            size = last - first + 1
            self.functions.append((node.name, node.lineno, size))
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        if node.body:
            first = node.body[0].lineno
            last = node.body[-1].end_lineno or node.body[-1].lineno
            size = last - first + 1
            self.functions.append((node.name, node.lineno, size))
        self.generic_visit(node)


def check_file_sizes(
    root: pathlib.Path,
    exclude_dirs: set[str],
) -> RuleResult:
    files = discover_python_files(root, exclude_dirs)
    large_files: list[tuple[str, int]] = []
    large_functions: list[tuple[str, str, int, int]] = []
    checked_files = 0
    checked_functions = 0

    for fp in files:
        content = fp.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()
        checked_files += 1
        module_str = module_path(fp, root)

        if len(lines) > 1000:
            large_files.append((module_str, len(lines)))

        try:
            tree = ast.parse(content, filename=str(fp))
        except SyntaxError:
            continue

        fv = FunctionSizeVisitor()
        fv.visit(tree)
        for func_name, lineno, size in fv.functions:
            checked_functions += 1
            if size > 100:
                large_functions.append((module_str, func_name, lineno, size))

    details: list[str] = []
    warnings = 0

    if large_files:
        warnings += len(large_files)
        details.append(f"Files exceeding 1000 lines ({len(large_files)}):")
        for mod, sz in large_files:
            details.append(f"  - {mod}: {sz} lines")
        if not large_functions:
            details.append("")

    if large_functions:
        warnings += len(large_functions)
        details.append(f"Functions exceeding 100 lines ({len(large_functions)}):")
        for mod, fn, lineno, sz in large_functions:
            details.append(f"  - {mod}:{lineno} {fn}() = {sz} lines")

    if not large_files and not large_functions:
        details.append("All files and functions within size limits.")

    status = PASS
    if warnings > 0:
        status = WARNING
    if any(sz > 2000 for _, sz in large_files):
        status = FAIL

    return make_rule(
        "L5", "File & Function Size Warnings",
        status, details,
        passed=checked_files + checked_functions - warnings,
        total=checked_files + checked_functions,
    )


# ── Rule L6: Naming convention checks ────────────────────────────────────

class NamingVisitor(ast.NodeVisitor):
    """Checks naming conventions in a file."""

    def __init__(self, module_path_str: str) -> None:
        self.module_path = module_path_str
        self.violations: list[str] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
            self.violations.append(
                f"{self.module_path}:{node.lineno} Class '{node.name}' "
                f"should be PascalCase"
            )
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node.name.startswith("__") and node.name.endswith("__"):
            pass
        elif node.name.startswith("_"):
            if not re.match(r'^_[a-z_][a-z0-9_]*$', node.name):
                self.violations.append(
                    f"{self.module_path}:{node.lineno} Function '{node.name}' "
                    f"should be _snake_case for private"
                )
        else:
            if not re.match(r'^[a-z_][a-z0-9_]*$', node.name):
                self.violations.append(
                    f"{self.module_path}:{node.lineno} Function '{node.name}' "
                    f"should be snake_case"
                )
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            if isinstance(target, ast.Name):
                name = target.id
                if name.isupper() and len(name) > 1:
                    if not re.match(r'^[A-Z][A-Z0-9_]*$', name):
                        self.violations.append(
                            f"{self.module_path}:{node.lineno} Constant '{name}' "
                            f"should be UPPER_CASE"
                        )
                elif name.islower() and len(name) > 1:
                    if not re.match(r'^[a-z_][a-z0-9_]*$', name):
                        self.violations.append(
                            f"{self.module_path}:{node.lineno} Variable '{name}' "
                            f"should be snake_case"
                        )


def check_naming_conventions(
    root: pathlib.Path,
    exclude_dirs: set[str],
) -> RuleResult:
    files = discover_python_files(root, exclude_dirs)
    all_violations: list[str] = []
    pkg_violations: list[str] = []
    file_violations: list[str] = []
    test_violations: list[str] = []
    checked = 0

    for fp in files:
        module_str = module_path(fp, root)
        checked += 1

        # Check package names (directory names) are snake_case
        rel = fp.relative_to(root)
        for part in rel.parts[:-1]:
            if part != part.lower() and not part.startswith("."):
                is_snake = bool(re.match(r'^[a-z][a-z0-9_]*$', part))
                if not is_snake:
                    pkg_violations.append(
                        f"Package directory '{part}' is not snake_case (in {module_str})"
                    )
                break

        # Check test file naming
        if "tests" in rel.parts or rel.parts[0] == "tests":
            if not fp.name.startswith("test_"):
                test_violations.append(
                    f"Test file '{module_str}' should start with 'test_'"
                )

        # Check class/function/variable naming via AST
        try:
            content = fp.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(content, filename=str(fp))
            nv = NamingVisitor(module_str)
            nv.visit(tree)
            all_violations.extend(nv.violations)
        except SyntaxError:
            file_violations.append(f"Could not parse {module_str} (syntax error)")

    details: list[str] = []
    total_violations = len(all_violations) + len(pkg_violations) + len(test_violations)

    if pkg_violations:
        details.append("Package naming violations:")
        details.extend(f"  - {v}" for v in pkg_violations)

    if test_violations:
        details.append("Test file naming violations:")
        details.extend(f"  - {v}" for v in test_violations)

    if all_violations:
        details.append("Class/function/variable naming violations:")
        details.extend(f"  - {v}" for v in all_violations[:50])
        if len(all_violations) > 50:
            details.append(f"  ... and {len(all_violations) - 50} more")

    if not details:
        details.append("All naming conventions satisfied.")

    status = PASS
    if total_violations > 0:
        status = FAIL

    return make_rule(
        "L6", "Naming Convention Checks",
        status, details,
        passed=checked - total_violations, total=checked,
    )


# ── Rule L7: Documentation checks ────────────────────────────────────────

def check_documentation(
    root: pathlib.Path,
    exclude_dirs: set[str],
) -> RuleResult:
    files = discover_python_files(root, exclude_dirs)
    no_module_doc: list[str] = []
    no_route_doc: list[str] = []
    checked_module = 0
    checked_routes = 0

    for fp in files:
        module_str = module_path(fp, root)
        try:
            content = fp.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(content, filename=str(fp))
        except SyntaxError:
            continue

        checked_module += 1

        # Module docstring check (non-empty __init__.py or .py with docstring)
        if fp.name != "__init__.py":
            docstring = ast.get_docstring(tree)
            if not docstring:
                no_module_doc.append(module_str)
        elif fp.name == "__init__.py":
            docstring = ast.get_docstring(tree)
            if not docstring and len(tree.body) > 0:
                no_module_doc.append(module_str)

        # Route handler docstring check
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                decorator_names = set()
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Attribute) and hasattr(dec, 'attr'):
                        decorator_names.add(dec.attr)
                    elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                        decorator_names.add(dec.func.attr)
                is_route_handler = bool(decorator_names & {
                    "get", "post", "put", "patch", "delete", "head", "options",
                    "route", "api_route",
                })
                if is_route_handler or "router" in module_str:
                    checked_routes += 1
                    if not ast.get_docstring(node):
                        no_route_doc.append(f"{module_str}:{node.lineno} {node.name}")

    details: list[str] = []
    warnings = 0

    if no_module_doc:
        warnings += len(no_module_doc)
        details.append(f"Files without module docstrings ({len(no_module_doc)}):")
        details.extend(f"  - {m}" for m in no_module_doc[:30])
        if len(no_module_doc) > 30:
            details.append(f"  ... and {len(no_module_doc) - 30} more")

    if no_route_doc:
        warnings += len(no_route_doc)
        if details:
            details.append("")
        details.append(f"Route handlers without docstrings ({len(no_route_doc)}):")
        details.extend(f"  - {r}" for r in no_route_doc[:30])
        if len(no_route_doc) > 30:
            details.append(f"  ... and {len(no_route_doc) - 30} more")

    if not details:
        details.append("All files and routes have documentation.")

    status = PASS
    if warnings > 0:
        status = WARNING

    return make_rule(
        "L7", "Documentation Checks",
        status, details,
        passed=checked_module + checked_routes - warnings,
        total=checked_module + checked_routes,
    )


# ── Scoring ──────────────────────────────────────────────────────────────

def compute_score(results: list[RuleResult]) -> float:
    if not results:
        return 100.0
    total = 0.0
    max_score = len(results) * 100.0
    for r in results:
        if r["status"] == PASS:
            total += 100.0
        elif r["status"] == WARNING:
            total += 50.0
        elif r["status"] == FAIL:
            total += 0.0
    return round(total / max_score * 100, 1) if max_score > 0 else 100.0


def has_failure(results: list[RuleResult]) -> bool:
    return any(r["status"] == FAIL for r in results)


# ── CLI / Main ────────────────────────────────────────────────────────────

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="GULA Architecture Compliance Engine",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Machine-readable JSON output (suppresses colour)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--focus", type=str, default=None,
        help="Run a single rule (e.g. L3, L5)",
    )
    parser.add_argument(
        "--exclude-dirs", type=str, default="tests,migrations,__pycache__",
        help="Comma-separated list of directories to exclude (default: tests,migrations,__pycache__)",
    )
    parser.add_argument(
        "--root", type=str, default=None,
        help="Root directory to scan (default: backend/app)",
    )
    return parser.parse_args(argv)


def run_rule(
    rule_id: str,
    checker,
    root: pathlib.Path,
    exclude_dirs: set[str],
    focus: str | None,
) -> RuleResult | None:
    if focus and rule_id != focus:
        return None
    return checker(root, exclude_dirs)


def format_results(
    results: list[RuleResult],
    score: float,
    json_output: bool,
) -> str:
    if json_output:
        return json.dumps({
            "score": score,
            "passed": not has_failure(results),
            "results": results,
        }, indent=2, ensure_ascii=False)

    lines: list[str] = []
    lines.append("")
    lines.append(f"{_c('bold', '═' * 72)}")
    lines.append(f"{_c('bold', ' GULA Architecture Compliance Engine')}")
    lines.append(f"{_c('bold', '═' * 72)}")
    lines.append("")

    max_rule_len = max(len(r["rule"]) for r in results) if results else 2

    for r in results:
        status_str = r["status"]
        if status_str == PASS:
            colored_status = _c("green", f"  {status_str}  ")
        elif status_str == WARNING:
            colored_status = _c("yellow", f" {status_str} ")
        else:
            colored_status = _c("red", f"  {status_str}  ")

        rule_part = f"{r['rule']:{max_rule_len}}"
        title_part = r["title"]
        lines.append(f"  {colored_status}  {rule_part}  {title_part}")

        if r["details"] and r["details"] != ["All naming conventions satisfied."] and \
           r["details"] != ["All files and routes have documentation."] and \
           r["details"] != ["All files and functions within size limits."] and \
           r["details"] != ["No layer violations detected."] and \
           r["details"] != ["No circular dependencies detected."] and \
           r["details"] != ["No forbidden imports detected."] and \
           r["details"] != ["No cross-domain violations detected."]:
            for det in r["details"]:
                lines.append(f"    {det}")

        lines.append("")

    lines.append(f"{_c('bold', '─' * 72)}")
    if score >= 90:
        score_color = _c("green", f"  {score} / 100")
    elif score >= 70:
        score_color = _c("yellow", f"  {score} / 100")
    else:
        score_color = _c("red", f"  {score} / 100")
    lines.append(f"  Compliance Score: {score_color}")
    lines.append("")

    if has_failure(results):
        lines.append(f"  {_c('red', '✖ FAIL')} — One or more rules failed")
    else:
        lines.append(f"  {_c('green', '✔ PASS')} — All checks passed")
    lines.append("")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.json:
        global _USE_COLOR
        _USE_COLOR = False

    log_level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    scan_root = pathlib.Path(args.root) if args.root else BACKEND_APP
    exclude_dirs = set(DEFAULT_EXCLUDE) | set(
        d.strip() for d in args.exclude_dirs.split(",") if d.strip()
    )

    if not scan_root.exists():
        logger.error("Scan root does not exist: %s", scan_root)
        return 1

    logger.info("Scanning: %s", scan_root)
    logger.info("Excluding: %s", ", ".join(sorted(exclude_dirs - DEFAULT_EXCLUDE)))

    rules: list[tuple[str, Any]] = [
        ("L1", check_layer_violations),
        ("L2", check_circular_dependencies),
        ("L3", check_forbidden_imports),
        ("L4", check_cross_domain_violations),
        ("L5", check_file_sizes),
        ("L6", check_naming_conventions),
        ("L7", check_documentation),
    ]

    results: list[RuleResult] = []
    for rule_id, checker in rules:
        result = run_rule(rule_id, checker, scan_root, exclude_dirs, args.focus)
        if result is not None:
            results.append(result)

    score = compute_score(results)
    output = format_results(results, score, bool(args.json))
    print(output)

    return 1 if has_failure(results) else 0


if __name__ == "__main__":
    sys.exit(main())
