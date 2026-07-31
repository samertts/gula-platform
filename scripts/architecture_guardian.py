#!/usr/bin/env python3
"""
Architecture Guardian — validates the GULA codebase against engineering
constitution rules using AST-level static analysis.

Checks:
  1. Circular dependency detection between modules
  2. Layer boundary violations (routes → database.py, direct ORM from routes)
  3. Naming conventions (snake_case files)
  4. Module docstring presence
  5. Unused import detection via AST

Usage:
    python scripts/architecture_guardian.py
    python scripts/architecture_guardian.py --verbose
    python scripts/architecture_guardian.py --json         # JSON output only
    python scripts/architecture_guardian.py --history      # show stored history

Exit codes:
    0  — no NEW violations (pre-existing ones unchanged are OK)
    1  — new violations found
"""

import argparse
import ast
import json
import logging
import pathlib
import re
import sys
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("architecture_guardian")

ANALYSIS_ROOT = pathlib.Path(__file__).resolve().parent.parent / "backend" / "app"
VIOLATIONS_HISTORY_FILE = pathlib.Path("/tmp/architecture_violations.json")

MODULE_CATEGORIES = {
    "routes": ANALYSIS_ROOT / "routes",
    "services": ANALYSIS_ROOT / "services",
    "models": ANALYSIS_ROOT / "models",
    "core": ANALYSIS_ROOT / "core",
    "security": ANALYSIS_ROOT / "security",
    "domain": ANALYSIS_ROOT / "domain",
}

# Sublayers within routes/ that are exempt from direct-DB-import rules
ROUTE_EXEMPT_FILES: set[str] = set()

# Directories to scan for naming / docstring checks
TOP_LEVEL_MODULES = [
    "routes", "services", "models", "core", "security", "domain",
    "ai", "audit", "notifications", "tasks", "financial", "legal",
    "gateways", "edge", "firewall", "interoperability", "approvals",
    "constraints", "dependencies", "forms", "integration", "kernel",
    "optimizer", "policies", "rules", "skills", "validation", "workflows",
]
# Skip these as top-level modules for docstring check
MODULES_SKIP_DOCSTRING = {"__pycache__"}

# ── Terminal colours ──────────────────────────────────────────────────────────

_RESET = "\033[0m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_RED = "\033[91m"
_CYAN = "\033[96m"
_BOLD = "\033[1m"


def _green(msg: str) -> str:
    return f"{_GREEN}{msg}{_RESET}"


def _red(msg: str) -> str:
    return f"{_RED}{msg}{_RESET}"


def _yellow(msg: str) -> str:
    return f"{_YELLOW}{msg}{_RESET}"


def _cyan(msg: str) -> str:
    return f"{_CYAN}{msg}{_RESET}"


def _bold(msg: str) -> str:
    return f"{_BOLD}{msg}{_RESET}"


# ── File scanning helpers ─────────────────────────────────────────────────────


def _iter_py_files(directory: pathlib.Path) -> list[pathlib.Path]:
    """Return all .py files under *directory* (non-recursive for top-level)."""
    if not directory.is_dir():
        return []
    return sorted(
        p for p in directory.iterdir()
        if p.suffix == ".py" and p.name != "__init__.py"
    )


def _all_py_files(root: pathlib.Path) -> list[pathlib.Path]:
    """Recursively gather all .py files under *root*."""
    if not root.is_dir():
        return []
    return sorted(p for p in root.rglob("*.py") if p.name != "__init__.py")


def _module_name_from_path(file_path: pathlib.Path, root: pathlib.Path) -> str:
    """Convert a file path relative to *root* into a dotted module name."""
    rel = file_path.resolve().relative_to(root.resolve())
    parts = list(rel.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1].replace(".py", "")
    return ".".join(parts)


# ── 1. Circular dependency detection ──────────────────────────────────────────


class ImportVisitor(ast.NodeVisitor):
    """Collect all import statements from a module."""

    def __init__(self) -> None:
        self.imports: list[tuple[str, int]] = []  # (module_name, lineno)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append((alias.name, node.lineno))

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module is None:
            return
        # Normalize relative imports
        level = node.level if node.level else 0
        module = node.module
        self.imports.append((module, node.lineno, level))


def _resolve_relative_import(
    current_module: str, import_module: str, level: int
) -> str | None:
    """Resolve a relative import to an absolute dotted module name."""
    if level == 0:
        return import_module
    parts = current_module.split(".")
    if level > len(parts):
        return None
    base = ".".join(parts[:-level])
    if import_module:
        return f"{base}.{import_module}" if base else import_module
    return base


def _build_dependency_graph(
    root: pathlib.Path,
) -> tuple[dict[str, set[str]], dict[str, list[tuple[str, int, int]]]]:
    """Build a directed graph of module → dependencies.

    Returns (graph: {module: {dependency, ...}}, line_map: {module: [(dep, lineno, level)]})
    """
    graph: dict[str, set[str]] = {}
    line_map: dict[str, list[tuple[str, int, int]]] = {}

    for py_file in _all_py_files(root):
        module_name = _module_name_from_path(py_file, root)
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        except SyntaxError as exc:
            logger.warning("Syntax error in %s: %s", py_file, exc)
            continue

        visitor = ImportVisitor()
        visitor.visit(tree)
        deps: set[str] = set()
        line_map[module_name] = []

        for imp in visitor.imports:
            if len(imp) == 3:  # ImportFrom: (module, lineno, level)
                import_module, lineno, level = imp
                resolved = _resolve_relative_import(module_name, import_module, level)
                if resolved:
                    deps.add(resolved)
                    line_map[module_name].append((resolved, lineno, level))
            else:  # Import: (module, lineno)
                import_module, lineno = imp
                deps.add(import_module)
                line_map[module_name].append((import_module, lineno, 0))

        graph[module_name] = {d for d in deps if root.name in d}

    return graph, line_map


def _filter_relevant_deps(dep: str) -> bool:
    """Filter to only keep deps that are within the app module tree."""
    # De-dup: keep deps that start with the same root
    return True


def _find_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    """Find all simple cycles in the dependency graph using DFS."""

    cycles: list[list[str]] = []
    visited: set[str] = set()
    path: list[str] = []
    path_set: set[str] = set()

    def dfs(node: str) -> None:
        if node in path_set:
            # Found a cycle; extract it
            cycle_start = path.index(node)
            cycle = path[cycle_start:] + [node]
            cycles.append(cycle)
            return
        if node in visited:
            return
        visited.add(node)
        path.append(node)
        path_set.add(node)

        for neighbour in graph.get(node, set()):
            if neighbour in graph:  # only traverse nodes in our graph
                dfs(neighbour)

        path.pop()
        path_set.discard(node)

    for node in list(graph.keys()):
        dfs(node)

    # Deduplicate cycles (same set of nodes, different starting points)
    seen: set[str] = set()
    unique_cycles: list[list[str]] = []
    for cycle in cycles:
        canonical = "->".join(sorted(set(cycle)))
        if canonical not in seen:
            seen.add(canonical)
            unique_cycles.append(cycle)

    return unique_cycles


def check_circular_dependencies(
    root: pathlib.Path,
) -> list[dict[str, Any]]:
    """Check for circular dependencies between modules."""
    violations: list[dict[str, Any]] = []
    graph, _ = _build_dependency_graph(root)
    cycles = _find_cycles(graph)

    for cycle in cycles:
        violations.append({
            "check": "circular_dependency",
            "severity": "error",
            "message": f"Circular dependency detected: {' → '.join(cycle)}",
            "modules": list(dict.fromkeys(cycle)),  # ordered dedup
        })

    return violations


# ── 2. Layer boundary check ──────────────────────────────────────────────────


def _parse_imports(file_path: pathlib.Path) -> list[dict[str, Any]]:
    """Parse all import statements from a file."""
    imports: list[dict[str, Any]] = []
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    except SyntaxError:
        return imports

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            level = node.level if node.level else 0
            module = node.module or ""
            names = [alias.name for alias in node.names]
            imports.append({
                "module": module,
                "level": level,
                "names": names,
                "lineno": node.lineno,
            })
        elif isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
            imports.append({
                "module": "",
                "level": 0,
                "names": names,
                "lineno": node.lineno,
            })
    return imports


def _has_model_import(imp: dict) -> bool:
    """Check if an import is from a models module."""
    module = imp["module"]
    parts = module.split(".")
    return "models" in parts or (imp["level"] > 0 and "models" in imp.get("names", []))


def _has_sqlalchemy_import(imp: dict) -> bool:
    """Check if an import references SQLAlchemy ORM types."""
    for name in imp["names"]:
        if name.startswith("Session") or name in (
            "declarative_base", "relationship", "backref", "column",
        ):
            return True
    return "sqlalchemy" in imp["module"].lower()


def _resolve_import_module(current_file: pathlib.Path, imp: dict, root: pathlib.Path) -> str | None:
    """Resolve a relative import to an absolute dotted module name."""
    rel_path = current_file.resolve().relative_to(root.resolve())
    parts = list(rel_path.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1].replace(".py", "")

    level = imp["level"]
    if level == 0:
        return imp["module"]

    if level > len(parts):
        return None
    base_parts = parts[:-level]
    if imp["module"]:
        base_parts += imp["module"].split(".")
    return ".".join(base_parts) if base_parts else imp["module"]


def check_layer_boundaries(root: pathlib.Path) -> list[dict[str, Any]]:
    """Verify route files don't directly import database.py or ORM objects."""
    violations: list[dict[str, Any]] = []
    routes_dir = root / "routes"

    if not routes_dir.is_dir():
        return violations

    for py_file in _iter_py_files(routes_dir):
        if py_file.name in ROUTE_EXEMPT_FILES:
            continue

        imports = _parse_imports(py_file)
        for imp in imports:
            resolved = _resolve_import_module(py_file, imp, root)

            # Check 1: Direct import from database module
            if resolved and resolved.endswith("database") and "get_db" in imp.get("names", []):
                violations.append({
                    "check": "layer_boundary",
                    "severity": "error",
                    "message": (
                        f"{py_file.relative_to(root.parent.parent)}:{imp['lineno']} "
                        f"directly imports 'get_db' from database. "
                        f"Routes should use services layer, not direct DB access."
                    ),
                    "file": str(py_file.relative_to(root.parent.parent)),
                    "line": imp["lineno"],
                })

            # Check 2: Direct import of Session / ORM types from sqlalchemy
            for name in imp["names"]:
                if name in ("Session", "declarative_base") and "sqlalchemy" in imp.get("module", ""):
                    violations.append({
                        "check": "layer_boundary",
                        "severity": "warning",
                        "message": (
                            f"{py_file.relative_to(root.parent.parent)}:{imp['lineno']} "
                            f"imports '{name}' from sqlalchemy directly. "
                            f"ORM access should go through services layer."
                        ),
                        "file": str(py_file.relative_to(root.parent.parent)),
                        "line": imp["lineno"],
                    })

            # Check 3: Import from models (direct model access from routes)
            if resolved and "models" in resolved.split("."):
                # If it's a model import used for type hints, it's acceptable;
                # but importing for querying is not. We flag it as a warning.
                is_model_type_usage = any(
                    name
                    for name in imp["names"]
                    if name
                )
                if imp["names"]:
                    violations.append({
                        "check": "layer_boundary",
                        "severity": "warning",
                        "message": (
                            f"{py_file.relative_to(root.parent.parent)}:{imp['lineno']} "
                            f"imports from models ({', '.join(imp['names'])}). "
                            f"Prefer importing models via services layer."
                        ),
                        "file": str(py_file.relative_to(root.parent.parent)),
                        "line": imp["lineno"],
                    })

    return violations


# ── 3. Naming conventions ────────────────────────────────────────────────────


def check_naming_conventions(root: pathlib.Path) -> list[dict[str, Any]]:
    """Check that Python files use snake_case naming."""
    violations: list[dict[str, Any]] = []

    for py_file in _all_py_files(root):
        name = py_file.name
        if name == "__init__.py":
            continue

        # Check: not snake_case
        if not re.match(r"^[a-z][a-z0-9_]*\.py$", name):
            violations.append({
                "check": "naming_convention",
                "severity": "warning",
                "message": (
                    f"{py_file.relative_to(root.parent.parent)} "
                    f"uses '{name}' which is not snake_case."
                ),
                "file": str(py_file.relative_to(root.parent.parent)),
            })

    return violations


# ── 4. Module documentation ──────────────────────────────────────────────────


def check_module_docstrings(root: pathlib.Path) -> list[dict[str, Any]]:
    """Check that each top-level module has a docstring."""
    violations: list[dict[str, Any]] = []

    for module_name in TOP_LEVEL_MODULES:
        module_dir = root / module_name
        if not module_dir.is_dir():
            continue

        init_file = module_dir / "__init__.py"
        if not init_file.exists():
            violations.append({
                "check": "module_docstring",
                "severity": "warning",
                "message": (
                    f"Module '{module_name}' is missing __init__.py"
                ),
                "file": str(init_file.relative_to(root.parent.parent)) if init_file.exists() else module_name,
            })
            continue

        try:
            tree = ast.parse(init_file.read_text(encoding="utf-8"), filename=str(init_file))
            docstring = ast.get_docstring(tree)
            if not docstring:
                violations.append({
                    "check": "module_docstring",
                    "severity": "warning",
                    "message": (
                        f"Module '{module_name}' (__init__.py) is missing a module-level docstring"
                    ),
                    "file": str(init_file.relative_to(root.parent.parent)),
                })
        except SyntaxError:
            violations.append({
                "check": "module_docstring",
                "severity": "warning",
                "message": (
                    f"Module '{module_name}' (__init__.py) has a syntax error"
                ),
                "file": str(init_file.relative_to(root.parent.parent)),
            })

    # Also check top-level files in app/ (main.py, worker.py, config.py, database.py)
    for py_file in root.iterdir():
        if py_file.suffix != ".py" or py_file.name == "__init__.py":
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            docstring = ast.get_docstring(tree)
            if not docstring:
                violations.append({
                    "check": "module_docstring",
                    "severity": "warning",
                    "message": (
                        f"Top-level file '{py_file.name}' is missing a module-level docstring"
                    ),
                    "file": str(py_file.relative_to(root.parent.parent)),
                })
        except SyntaxError:
            pass

    return violations


# ── 5. Unused import detection ────────────────────────────────────────────────


class NameUsageVisitor(ast.NodeVisitor):
    """Collect all name references to detect which imports are actually used."""

    def __init__(self) -> None:
        self.used_names: set[str] = set()
        self.defined_names: set[str] = set()
        self.imported_names: dict[str, int] = {}  # name → line number
        self.imported_modules: dict[str, int] = {}  # alias → line number
        # names exposed via __all__
        self.exported_names: set[str] = set()

    def visit_Name(self, node: ast.Name) -> None:
        if not isinstance(node.ctx, (ast.Store, ast.Del)):
            self.used_names.add(node.id)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        # Track uses like module.ClassName
        if isinstance(node.value, ast.Name):
            self.used_names.add(node.value.id)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imported_modules[name] = node.lineno
            # "import foo" also defines "foo" as a name
            self.defined_names.add(name)
            # Imported names are used implicitly if the module is accessed via attribute
            self.used_names.add(name)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imported_names[name] = node.lineno
            self.defined_names.add(name)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.defined_names.add(node.name)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.defined_names.add(node.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.defined_names.add(node.name)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.defined_names.add(target.id)
            elif isinstance(target, ast.Tuple):
                for elt in target.elts:
                    if isinstance(elt, ast.Name):
                        self.defined_names.add(elt.id)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if isinstance(node.target, ast.Name):
            self.defined_names.add(node.target.id)
        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        for item in node.items:
            if item.optional_vars:
                if isinstance(item.optional_vars, ast.Name):
                    self.defined_names.add(item.optional_vars.id)
                elif isinstance(item.optional_vars, ast.Tuple):
                    for elt in item.optional_vars.elts:
                        if isinstance(elt, ast.Name):
                            self.defined_names.add(elt.id)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.name:
            self.defined_names.add(node.name)
        self.generic_visit(node)

    def visit_ImportFrom_Star(self, node: ast.ImportFrom) -> None:
        # Wildcard imports — cannot check
        pass

    def visit_Global(self, node: ast.Global) -> None:
        for name in node.names:
            self.used_names.add(name)

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        for name in node.names:
            self.used_names.add(name)

    def _check_exported(self, node: ast.Module) -> None:
        """Scan for __all__ definitions."""
        for child in node.body:
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name) and target.id == "__all__":
                        if isinstance(child.value, (ast.List, ast.Tuple)):
                            for elt in child.value.elts:
                                if isinstance(elt, ast.Constant):
                                    self.exported_names.add(elt.value)


# Names that are always considered intentionally imported (used for side effects)
_SIDE_EFFECT_MODULES: set[str] = {"logging", "warnings", "importlib"}
# Names that are re-exports for convenience
_NAMES_ALWAYS_USED: set[str] = {"__all__"}


def check_unused_imports(root: pathlib.Path) -> list[dict[str, Any]]:
    """Detect unused imports via static AST analysis."""
    violations: list[dict[str, Any]] = []

    for py_file in _all_py_files(root):
        if py_file.name == "__init__.py":
            continue

        try:
            text = py_file.read_text(encoding="utf-8")
            tree = ast.parse(text, filename=str(py_file))
        except SyntaxError:
            continue

        visitor = NameUsageVisitor()
        visitor.visit(tree)
        visitor._check_exported(tree)

        # Names used via __all__ export
        exported = visitor.exported_names

        # For each imported name, check if it's referenced elsewhere
        for name, lineno in visitor.imported_names.items():
            # Skip side-effect imports
            if name in _SIDE_EFFECT_MODULES:
                continue
            # Skip if exported via __all__
            if name in exported:
                continue
            # Check if used — "used" means it appears anywhere besides its import statement
            usage_count = 0
            # Count usage occurrences in the AST
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and node.id == name and not isinstance(node.ctx, (ast.Store, ast.Del)):
                    # Make sure this isn't the import statement itself
                    if hasattr(node, "col_offset") and hasattr(node, "lineno"):
                        usage_count += 1
                elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == name:
                    usage_count += 1

            # Subtract the import itself (counted once in walk)
            if usage_count <= 1:
                violations.append({
                    "check": "unused_import",
                    "severity": "warning",
                    "message": (
                        f"{py_file.relative_to(root.parent.parent)}:{lineno} "
                        f"unused import '{name}'"
                    ),
                    "file": str(py_file.relative_to(root.parent.parent)),
                    "line": lineno,
                    "import_name": name,
                })

        # Check unused module imports (import foo rather than from foo import bar)
        for module_name, lineno in visitor.imported_modules.items():
            # Skip side-effect modules
            top = module_name.split(".")[0]
            if top in _SIDE_EFFECT_MODULES:
                continue
            if module_name in exported:
                continue
            # Check: is the module name used as an attribute access target?
            usage_count = 0
            for node in ast.walk(tree):
                if (isinstance(node, ast.Name) and node.id == module_name.split(".")[0]) or (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == module_name.split(".")[0]):
                    usage_count += 1

            if usage_count <= 1:
                violations.append({
                    "check": "unused_import",
                    "severity": "warning",
                    "message": (
                        f"{py_file.relative_to(root.parent.parent)}:{lineno} "
                        f"unused import '{module_name}'"
                    ),
                    "file": str(py_file.relative_to(root.parent.parent)),
                    "line": lineno,
                    "import_name": module_name,
                })

    return violations


# ── Violation history management ─────────────────────────────────────────────


def _load_violation_history() -> dict[str, Any]:
    """Load previous violation history from disk."""
    if VIOLATIONS_HISTORY_FILE.exists():
        try:
            with open(VIOLATIONS_HISTORY_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            logger.warning("Could not read violation history, starting fresh.")
    return {"timestamp": None, "violations": []}


def _save_violation_history(violations: list[dict[str, Any]]) -> None:
    """Save current violations as the new baseline."""
    history = {
        "timestamp": datetime.now(UTC).isoformat(),
        "violations": violations,
    }
    try:
        with open(VIOLATIONS_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except OSError as exc:
        logger.warning("Could not write violation history: %s", exc)


def _violation_key(v: dict[str, Any]) -> str:
    """Create a stable unique key for a violation."""
    check = v.get("check", "")
    message = v.get("message", "")
    fname = v.get("file", "")
    line = v.get("line", 0)
    return f"{check}::{fname}::{line}::{message}"


def _categorize_violations(
    current: list[dict[str, Any]],
    history: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Split current violations into new / pre-existing / resolved.

    Returns (new_violations, existing_violations, resolved_violations).
    """
    current_keys = {_violation_key(v): v for v in current}
    history_keys = {_violation_key(v): v for v in history}

    new = [current_keys[k] for k in current_keys if k not in history_keys]
    existing = [current_keys[k] for k in current_keys if k in history_keys]
    resolved = [history_keys[k] for k in history_keys if k not in current_keys]

    return new, existing, resolved


# ── Output formatting ─────────────────────────────────────────────────────────


def _status_summary(
    all_violations: list[dict[str, Any]],
    new_violations: list[dict[str, Any]],
    existing_violations: list[dict[str, Any]],
    resolved_violations: list[dict[str, Any]],
) -> str:
    """Generate a human-readable summary."""
    total = len(all_violations)
    new_count = len(new_violations)
    existing_count = len(existing_violations)
    resolved_count = len(resolved_violations)

    lines = [
        _bold("\n═══ Architecture Guardian Report ═══\n"),
    ]

    if resolved_count > 0:
        lines.append(f"  {_green('✓')} Resolved: {_green(str(resolved_count))}")
    if existing_count > 0:
        lines.append(f"  {_yellow('◷')} Pre-existing: {_yellow(str(existing_count))}")
    if new_count > 0:
        lines.append(f"  {_red('✗')} New violations: {_red(str(new_count))}")
    lines.append(f"  Total: {total}")

    if new_count == 0 and total == 0:
        lines.append(f"\n  {_green('All clear! No violations found.')}")

    return "\n".join(lines)


def _format_violation(v: dict[str, Any], status: str = "new") -> str:
    """Format a single violation with colour."""
    sev = v.get("severity", "warning")
    if sev == "error":
        colour = _RED
        tag = "ERR"
    elif sev == "warning":
        colour = _YELLOW
        tag = "WRN"
    else:
        colour = _CYAN
        tag = "INF"

    status_tag = _red("NEW") if status == "new" else _yellow("PRE")

    msg = v.get("message", "")
    return f"  [{status_tag}] [{colour}{tag}{_RESET}] {msg}"


def _print_report(
    all_violations: list[dict[str, Any]],
    new_violations: list[dict[str, Any]],
    existing_violations: list[dict[str, Any]],
    resolved_violations: list[dict[str, Any]],
    json_output: bool = False,
) -> None:
    """Print the report to stdout."""
    if json_output:
        report = {
            "timestamp": datetime.now(UTC).isoformat(),
            "summary": {
                "total": len(all_violations),
                "new": len(new_violations),
                "pre_existing": len(existing_violations),
                "resolved": len(resolved_violations),
            },
            "new_violations": new_violations,
            "pre_existing_violations": existing_violations,
            "resolved_violations": resolved_violations,
        }
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return

    print(_status_summary(all_violations, new_violations, existing_violations, resolved_violations))

    if new_violations:
        print(f"\n  {_bold(_red('── New Violations ──'))}")
        for v in new_violations:
            print(_format_violation(v, "new"))

    if existing_violations:
        print(f"\n  {_bold(_yellow('── Pre-existing Violations ──'))}")
        for v in existing_violations:
            print(_format_violation(v, "existing"))

    if resolved_violations:
        print(f"\n  {_bold(_green('── Resolved Violations ──'))}")
        for v in resolved_violations:
            print(f"  {_green('✓')} {v.get('message', '')}")

    print()


# ── Main entry point ──────────────────────────────────────────────────────────


def run_all_checks(root: pathlib.Path) -> list[dict[str, Any]]:
    """Run all architecture checks and return aggregated violations."""
    all_violations: list[dict[str, Any]] = []

    logger.info("Running circular dependency check...")
    try:
        violations = check_circular_dependencies(root)
        all_violations.extend(violations)
        logger.info("  Circular dependency check: %d violation(s)", len(violations))
    except Exception as exc:
        logger.error("Circular dependency check failed: %s", exc)

    logger.info("Running layer boundary check...")
    try:
        violations = check_layer_boundaries(root)
        all_violations.extend(violations)
        logger.info("  Layer boundary check: %d violation(s)", len(violations))
    except Exception as exc:
        logger.error("Layer boundary check failed: %s", exc)

    logger.info("Running naming convention check...")
    try:
        violations = check_naming_conventions(root)
        all_violations.extend(violations)
        logger.info("  Naming convention check: %d violation(s)", len(violations))
    except Exception as exc:
        logger.error("Naming convention check failed: %s", exc)

    logger.info("Running module docstring check...")
    try:
        violations = check_module_docstrings(root)
        all_violations.extend(violations)
        logger.info("  Module docstring check: %d violation(s)", len(violations))
    except Exception as exc:
        logger.error("Module docstring check failed: %s", exc)

    logger.info("Running unused import check...")
    try:
        violations = check_unused_imports(root)
        all_violations.extend(violations)
        logger.info("  Unused import check: %d violation(s)", len(violations))
    except Exception as exc:
        logger.error("Unused import check failed: %s", exc)

    return all_violations


def _setup_logging(verbose: bool) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Architecture Guardian — validate GULA codebase rules",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose (DEBUG) logging",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON only",
    )
    parser.add_argument(
        "--history",
        action="store_true",
        help="Display stored violation history and exit",
    )
    parser.add_argument(
        "--root",
        type=str,
        default=None,
        help="Override analysis root path (default: backend/app)",
    )
    args = parser.parse_args()

    _setup_logging(args.verbose)

    # Determine analysis root
    if args.root:
        root = pathlib.Path(args.root).resolve()
    else:
        root = ANALYSIS_ROOT.resolve()

    if not root.is_dir():
        logger.error("Analysis root %s does not exist", root)
        return 1

    # Show history mode
    if args.history:
        history = _load_violation_history()
        if history.get("violations"):
            print(json.dumps(history, indent=2, ensure_ascii=False))
        else:
            print(json.dumps({"timestamp": None, "violations": [], "message": "No history recorded"}, indent=2))
        return 0

    # Run checks
    logger.info("Architecture Guardian scanning %s", root)
    all_violations = run_all_checks(root)

    # Load history and categorize
    history = _load_violation_history()
    previous_violations = history.get("violations", [])

    new_violations, existing_violations, resolved_violations = _categorize_violations(
        all_violations, previous_violations,
    )

    # Save current state as new baseline
    _save_violation_history(all_violations)

    # Print report
    _print_report(
        all_violations,
        new_violations,
        existing_violations,
        resolved_violations,
        json_output=args.json,
    )

    # Exit code: 1 if any NEW violations found
    if new_violations:
        logger.info("Exit: 1 — %d new violation(s) found", len(new_violations))
        return 1

    logger.info("Exit: 0 — no new violations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
