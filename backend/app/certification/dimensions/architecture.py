from __future__ import annotations

from pathlib import Path

from app.engineering.intelligence.dependency_graph import DependencyGraphGenerator
from app.engineering.validation.clean_arch import CleanArchitectureValidator
from app.engineering.validation.ddd import DDDValidator

from . import DimensionEvaluator, DimensionResult


class ArchitectureEvaluator(DimensionEvaluator):
    def evaluate(self, module_path: str | None = None) -> DimensionResult:
        target = Path(module_path) if module_path else self.project_root

        clean_arch = CleanArchitectureValidator(target)
        arch_issues = clean_arch.validate()
        self._add_evidence(
            "clean_arch_violations",
            value=len(arch_issues),
            source="CleanArchitectureValidator",
            passed=len(arch_issues) == 0,
        )
        if arch_issues:
            self._add_remediation(
                f"Fix {len(arch_issues)} architecture layer violations",
                severity="high",
                effort=str(len(arch_issues) * 2) + "h",
            )

        ddd = DDDValidator(target)
        ddd_issues = ddd.validate()
        self._add_evidence(
            "ddd_violations",
            value=len(ddd_issues),
            source="DDDValidator",
            passed=len(ddd_issues) == 0,
        )
        if ddd_issues:
            self._add_remediation(
                f"Resolve {len(ddd_issues)} DDD principle violations",
                severity="medium",
            )
        for issue in ddd_issues:
            self._add_evidence(
                name=f"ddd_{issue.principle}",
                value=issue.message,
                source=str(issue.file),
                passed=False,
            )

        dep_graph = DependencyGraphGenerator(target)
        cycles = dep_graph.find_cyclic_dependencies()
        self._add_evidence(
            "circular_dependencies",
            value=len(cycles),
            source="DependencyGraphGenerator",
            passed=len(cycles) == 0,
        )
        if cycles:
            self._add_remediation(
                f"Break {len(cycles)} circular dependencies",
                severity="high",
                effort="4h",
            )

        audit = dep_graph.audit()
        self._add_evidence(
            "total_modules",
            value=audit["total_modules"],
            source="DependencyGraphGenerator",
        )
        self._add_evidence(
            "orphaned_modules",
            value=audit["orphaned_modules"],
            source="DependencyGraphGenerator",
            passed=audit["orphaned_modules"] == 0,
        )
        if audit["orphaned_modules"]:
            self._add_remediation(
                f"Review {audit['orphaned_modules']} orphaned modules",
                severity="low",
            )

        score = 1.0
        score -= len(arch_issues) * 0.08
        score -= len(ddd_issues) * 0.04
        score -= len(cycles) * 0.15
        score -= audit["orphaned_modules"] * 0.02

        return self._result(score)
