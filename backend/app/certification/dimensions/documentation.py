from __future__ import annotations

import ast
from pathlib import Path

from . import DimensionEvaluator, DimensionResult


class DocumentationEvaluator(DimensionEvaluator):
    def evaluate(self, module_path: str | None = None) -> DimensionResult:
        target = Path(module_path) if module_path else self.project_root

        adr_count = self._count_adrs(target)
        self._add_evidence(
            "adr_count",
            value=adr_count,
            source="docs/adr directory",
            passed=adr_count >= 3,
        )
        if adr_count < 3:
            self._add_remediation(
                f"Document architectural decisions with ADRs (found {adr_count}, target >= 3)",
                severity="medium",
                effort=str((3 - adr_count) * 2) + "h",
            )

        readme_found = self._check_readme(target)
        self._add_evidence(
            "readme_exists",
            value=readme_found,
            source="Repository root",
            passed=readme_found,
        )
        if not readme_found:
            self._add_remediation(
                "Create a README.md with project overview, setup, and architecture",
                severity="high",
                effort="3h",
            )

        api_docs = self._check_api_documentation(target)
        self._add_evidence(
            "api_documentation",
            value=api_docs,
            source="OpenAPI / routes",
            passed=api_docs,
        )
        if not api_docs:
            self._add_remediation(
                "Add OpenAPI/Swagger documentation or route docstrings",
                severity="high",
                effort="6h",
            )

        changelog = self._check_changelog(target)
        self._add_evidence(
            "changelog_exists",
            value=changelog,
            source="Repository root",
            passed=changelog,
        )
        if not changelog:
            self._add_remediation(
                "Create CHANGELOG.md following Keep a Changelog format",
                severity="low",
                effort="1h",
            )

        docstring_coverage = self._measure_docstring_coverage(target)
        self._add_evidence(
            "docstring_coverage_pct",
            value=round(docstring_coverage, 1),
            source="AST scan",
            passed=docstring_coverage >= 30.0,
        )
        if docstring_coverage < 30.0:
            self._add_remediation(
                f"Improve docstring coverage ({round(docstring_coverage, 1)}% vs target 30%)",
                severity="medium",
                effort="6h",
            )

        contributing = self._check_contributing(target)
        self._add_evidence(
            "contributing_guide",
            value=contributing,
            source="Repository root",
            passed=contributing,
        )
        if not contributing:
            self._add_remediation(
                "Create CONTRIBUTING.md with development setup and guidelines",
                severity="low",
                effort="2h",
            )

        license_file = self._check_license(target)
        self._add_evidence(
            "license_file",
            value=license_file,
            source="Repository root",
            passed=license_file,
        )
        if not license_file:
            self._add_remediation(
                "Add a LICENSE file to the repository",
                severity="medium",
                effort="1h",
            )

        code_of_conduct = self._check_code_of_conduct(target)
        self._add_evidence(
            "code_of_conduct",
            value=code_of_conduct,
            source="Repository root",
            passed=code_of_conduct,
        )
        if not code_of_conduct:
            self._add_remediation(
                "Add CODE_OF_CONDUCT.md",
                severity="low",
                effort="1h",
            )

        score = 1.0
        if adr_count < 3:
            score -= min((3 - adr_count) * 0.05, 0.2)
        if not readme_found:
            score -= 0.15
        if not api_docs:
            score -= 0.15
        if not changelog:
            score -= 0.05
        if docstring_coverage < 30.0:
            score -= min((30.0 - docstring_coverage) * 0.005, 0.1)
        if not contributing:
            score -= 0.03
        if not license_file:
            score -= 0.05
        if not code_of_conduct:
            score -= 0.02

        return self._result(score)

    def _count_adrs(self, target: Path) -> int:
        adr_dirs = [
            target / "docs" / "adr",
            target / "docs" / "adrs",
            target / "adr",
            target / "decisions",
        ]
        for d in adr_dirs:
            if d.exists():
                return len(list(d.glob("*.md")))
        return 0

    def _check_readme(self, target: Path) -> bool:
        files = ["README.md", "README.rst", "README.txt", "README"]
        return any((target / f).exists() for f in files)

    def _check_api_documentation(self, target: Path) -> bool:
        for py_file in target.rglob("*.py"):
            try:
                content = py_file.read_text()
                if "openapi" in content.lower() or "swagger" in content.lower() or "FastAPI" in content:
                    return True
            except Exception:
                continue
        for _f in target.rglob("openapi.*"):
            return True
        for _f in target.rglob("openapi/**"):
            return True
        return False

    def _check_changelog(self, target: Path) -> bool:
        files = ["CHANGELOG.md", "CHANGELOG.rst", "CHANGELOG.txt", "HISTORY.md"]
        return any((target / f).exists() for f in files)

    def _measure_docstring_coverage(self, target: Path) -> float:
        total_functions = 0
        documented_functions = 0
        for py_file in target.rglob("*.py"):
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            try:
                tree = ast.parse(py_file.read_text())
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        total_functions += 1
                        if node.body and isinstance(node.body[0], ast.Expr):
                            if isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                                documented_functions += 1
            except SyntaxError:
                continue
        total_functions = max(total_functions, 1)
        return (documented_functions / total_functions) * 100

    def _check_contributing(self, target: Path) -> bool:
        files = ["CONTRIBUTING.md", "CONTRIBUTING.rst", "CONTRIBUTING.txt"]
        return any((target / f).exists() for f in files)

    def _check_license(self, target: Path) -> bool:
        for _f in target.rglob("LICENSE*"):
            return True
        return False

    def _check_code_of_conduct(self, target: Path) -> bool:
        files = ["CODE_OF_CONDUCT.md", "CODE_OF_CONDUCT.rst"]
        return any((target / f).exists() for f in files)
