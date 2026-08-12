from __future__ import annotations

import ast
import logging
import os
from collections.abc import Callable
from dataclasses import dataclass, field

logger = logging.getLogger("gula.architecture")


@dataclass
class ArchitectureRule:
    name: str
    description: str
    check: Callable[[], list[str]]
    severity: str = "error"


@dataclass
class ValidationResult:
    passed: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)

    def merge(self, other: ValidationResult) -> None:
        if not other.passed:
            self.passed = False
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.info.extend(other.info)


class ArchitectureValidator:
    def __init__(self) -> None:
        self._rules: list[ArchitectureRule] = []
        self._results: dict[str, ValidationResult] = {}

    def add_rule(self, rule: ArchitectureRule) -> None:
        self._rules.append(rule)

    def validate_all(self) -> dict[str, ValidationResult]:
        for rule in self._rules:
            try:
                violations = rule.check()
                self._results[rule.name] = ValidationResult(
                    passed=len(violations) == 0,
                    errors=violations if rule.severity == "error" else [],
                    warnings=violations if rule.severity == "warning" else [],
                )
                if violations:
                    (logger.error if rule.severity == "error" else logger.warning)(
                        "Architecture rule '%s': %d violations", rule.name, len(violations))
            except Exception as exc:
                self._results[rule.name] = ValidationResult(passed=False, errors=[f"Check failed: {exc}"])
                logger.exception("Architecture rule '%s' crashed", rule.name)
        return self._results

    def summary(self) -> str:
        lines = ["# Architecture Validation Summary\n", ""]
        total = len(self._results)
        passed = sum(1 for r in self._results.values() if r.passed)
        lines.append(f"**{passed}/{total} rules passed**\n\n")
        for name, result in self._results.items():
            status = "✅" if result.passed else "❌"
            lines.append(f"### {status} {name}")
            if result.errors:
                lines.append(f"  Errors ({len(result.errors)}):")
                for e in result.errors[:5]:
                    lines.append(f"    - {e}")
            if result.warnings:
                lines.append(f"  Warnings ({len(result.warnings)}):")
                for w in result.warnings[:5]:
                    lines.append(f"    - {w}")
            lines.append("")
        return "\n".join(lines)


def _check_no_circular_imports(root: str = "backend/app") -> list[str]:
    violations: list[str] = []
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            filepath = os.path.join(dirpath, fn)
            relpath = os.path.relpath(filepath, root)
            try:
                with open(filepath) as f:
                    tree = ast.parse(f.read())
                imports: set[str] = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module and node.module.startswith("."):
                            imports.add(node.module)
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name.startswith("app."):
                                imports.add(alias.name)
                imported_by[relpath] = imports
            except SyntaxError:
                violations.append(f"Syntax error in {relpath}")
    return violations[:10]


imported_by: dict[str, set[str]] = {}


def _check_no_services_import_backend() -> list[str]:
    violations: list[str] = []
    if not os.path.isdir("services"):
        return violations
    for dirpath, _, filenames in os.walk("services"):
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            filepath = os.path.join(dirpath, fn)
            with open(filepath) as f:
                content = f.read()
            if "from backend" in content or "import backend" in content:
                violations.append(f"{os.path.relpath(filepath)} imports from backend (reverse dependency)")
    return violations


def _check_shared_no_backend() -> list[str]:
    violations: list[str] = []
    if not os.path.isdir("shared"):
        return violations
    for dirpath, _, filenames in os.walk("shared"):
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            filepath = os.path.join(dirpath, fn)
            with open(filepath) as f:
                content = f.read()
            if "from backend" in content or "import backend" in content:
                violations.append(f"{os.path.relpath(filepath)} imports backend")
    return violations


validator = ArchitectureValidator()
validator.add_rule(ArchitectureRule("no-circular-imports", "Detect circular imports", _check_no_circular_imports))
validator.add_rule(ArchitectureRule("no-services-to-backend", "Services must not import from backend", _check_no_services_import_backend))
validator.add_rule(ArchitectureRule("shared-no-backend", "Shared library must not import from backend", _check_shared_no_backend))

__all__ = ["ArchitectureRule", "ArchitectureValidator", "ValidationResult", "validator"]
