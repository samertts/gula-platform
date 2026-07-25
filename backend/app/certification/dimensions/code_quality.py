from __future__ import annotations

import ast
import subprocess
from pathlib import Path

from . import DimensionEvaluator, DimensionResult


class CodeQualityEvaluator(DimensionEvaluator):
    def evaluate(self, module_path: str | None = None) -> DimensionResult:
        target = Path(module_path) if module_path else self.project_root

        lint_issues = self._run_linter(target)
        self._add_evidence(
            "lint_issues_count",
            value=lint_issues,
            source="ruff/flake8",
            passed=lint_issues == 0,
        )
        if lint_issues:
            self._add_remediation(
                f"Fix {lint_issues} linting errors",
                severity="medium",
                effort=str(lint_issues) + "m",
            )

        type_hint_coverage = self._measure_type_hint_coverage(target)
        self._add_evidence(
            "type_hint_coverage_pct",
            value=round(type_hint_coverage, 1),
            source="AST scan",
            passed=type_hint_coverage >= 50.0,
        )
        if type_hint_coverage < 50.0:
            self._add_remediation(
                f"Increase type hint coverage ({round(type_hint_coverage, 1)}% vs target 50%)",
                severity="medium",
                effort="6h",
            )

        code_smells = self._detect_code_smells(target)
        self._add_evidence(
            "code_smells_count",
            value=len(code_smells),
            source="AST scan",
            passed=len(code_smells) <= 5,
        )
        if len(code_smells) > 5:
            self._add_remediation(
                f"Address {len(code_smells)} code smells (long methods, god classes, etc.)",
                severity="medium",
                effort=str(len(code_smells)) + "h",
            )

        naming_conventions = self._check_naming_conventions(target)
        self._add_evidence(
            "naming_violations",
            value=naming_conventions,
            source="AST scan",
            passed=naming_conventions == 0,
        )
        if naming_conventions:
            self._add_remediation(
                f"Fix {naming_conventions} naming convention violations (snake_case for functions, PascalCase for classes)",
                severity="low",
                effort=str(naming_conventions) + "m",
            )

        import_organization = self._check_import_organization(target)
        self._add_evidence(
            "import_organization",
            value=import_organization,
            source="AST scan",
            passed=import_organization,
        )
        if not import_organization:
            self._add_remediation(
                "Organize imports: stdlib → third-party → local, with blank line separators",
                severity="low",
                effort="1h",
            )

        score = 1.0
        score -= min(lint_issues * 0.02, 0.2)
        if type_hint_coverage < 50.0:
            score -= min((50.0 - type_hint_coverage) * 0.005, 0.15)
        score -= min(len(code_smells) * 0.03, 0.15)
        score -= naming_conventions * 0.01
        if not import_organization:
            score -= 0.03

        return self._result(score)

    def _run_linter(self, target: Path) -> int:
        for _linter, args in [
            ("ruff", ["ruff", "check", "--select=E9,F821", "--quiet", "."]),
            ("flake8", ["flake8", "--select=E9,F821", "--quiet", "."]),
        ]:
            try:
                result = subprocess.run(
                    args,
                    capture_output=True,
                    text=True,
                    cwd=str(target),
                    timeout=60,
                )
                if result.returncode != 0:
                    output = result.stdout + result.stderr
                    return len([line for line in output.splitlines() if line.strip()])
                return 0
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        return 0

    def _measure_type_hint_coverage(self, target: Path) -> float:
        total_params = 0
        typed_params = 0
        total_returns = 0
        typed_returns = 0

        for py_file in target.rglob("*.py"):
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            try:
                tree = ast.parse(py_file.read_text())
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if node.name.startswith("__") and node.name != "__init__":
                            continue
                        total_returns += 1
                        if node.returns:
                            typed_returns += 1
                        for arg in node.args.args:
                            if arg.arg == "self":
                                continue
                            total_params += 1
                            if arg.annotation:
                                typed_params += 1
                        if node.args.vararg and node.args.vararg.annotation:
                            typed_params += 1
                        if node.args.kwonlyargs:
                            for arg in node.args.kwonlyargs:
                                total_params += 1
                                if arg.annotation:
                                    typed_params += 1
                        if node.args.kwarg and node.args.kwarg.annotation:
                            typed_params += 1
            except SyntaxError:
                continue

        total = total_params + total_returns
        typed = typed_params + typed_returns
        if total == 0:
            return 100.0
        return (typed / total) * 100

    def _detect_code_smells(self, target: Path) -> list[dict]:
        smells = []
        for py_file in target.rglob("*.py"):
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            try:
                tree = ast.parse(py_file.read_text())
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        methods = sum(
                            1
                            for n in node.body
                            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                        )
                        if methods > 15:
                            smells.append(
                                {
                                    "type": "god_class",
                                    "file": str(py_file.relative_to(target)),
                                    "name": node.name,
                                    "methods": methods,
                                },
                            )
                    if isinstance(node, ast.FunctionDef):
                        if node.end_lineno and node.lineno:
                            if node.end_lineno - node.lineno > 100:
                                smells.append(
                                    {
                                        "type": "long_method",
                                        "file": str(py_file.relative_to(target)),
                                        "name": node.name,
                                        "lines": node.end_lineno - node.lineno + 1,
                                    },
                                )
                        params = len(node.args.args) + len(node.args.kwonlyargs)
                        if params > 6:
                            smells.append(
                                {
                                    "type": "too_many_parameters",
                                    "file": str(py_file.relative_to(target)),
                                    "name": node.name,
                                    "parameters": params,
                                },
                            )
            except SyntaxError:
                continue
        return smells

    def _check_naming_conventions(self, target: Path) -> int:
        violations = 0
        for py_file in target.rglob("*.py"):
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            try:
                tree = ast.parse(py_file.read_text())
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        if not node.name.startswith("__") and not node.name.startswith("_"):
                            if (
                                not node.name.islower()
                                and "_" not in node.name
                                and not node.name.isupper()
                            ):
                                violations += 1
                    if isinstance(node, ast.ClassDef):
                        if not node.name[0].isupper():
                            violations += 1
            except SyntaxError:
                continue
        return violations

    def _check_import_organization(self, target: Path) -> bool:
        issues = 0
        for py_file in target.rglob("*.py"):
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            try:
                content = py_file.read_text()
                tree = ast.parse(content)
                imports = [
                    node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))
                ]
                if len(imports) <= 1:
                    continue
                stdlib = {
                    "sys",
                    "os",
                    "json",
                    "re",
                    "math",
                    "datetime",
                    "pathlib",
                    "typing",
                    "abc",
                    "functools",
                    "collections",
                    "hashlib",
                    "uuid",
                    "enum",
                    "dataclasses",
                    "subprocess",
                    "threading",
                    "time",
                    "io",
                    "copy",
                    "itertools",
                    "ast",
                    "xml",
                    "textwrap",
                    "inspect",
                    "warnings",
                    "importlib",
                    "pickle",
                    "base64",
                    "statistics",
                    "operator",
                }
                for imp in imports:
                    module = ""
                    if isinstance(imp, ast.Import):
                        module = imp.names[0].name.split(".")[0]
                    elif isinstance(imp, ast.ImportFrom) and imp.module:
                        module = imp.module.split(".")[0]
                    if (
                        module
                        and module not in stdlib
                        and not module.startswith("app.")
                        and "." not in module
                    ):
                        pass
                    if module and (module.startswith(("app.", "..", "."))):
                        pass
            except SyntaxError:
                continue
        return issues == 0
