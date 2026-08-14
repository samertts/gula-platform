from __future__ import annotations

from pathlib import Path

from .enums import CertificationDimension, CertificationLevel
from .report import CertificationReport


class CertificationEngine:
    LEVEL_THRESHOLDS: list[tuple[float, CertificationLevel]] = [
        (0.95, CertificationLevel.DIAMOND),
        (0.85, CertificationLevel.PLATINUM),
        (0.75, CertificationLevel.GOLD),
        (0.60, CertificationLevel.SILVER),
        (0.40, CertificationLevel.BRONZE),
    ]

    def __init__(self, project_root: Path | str | None = None):
        self.project_root = Path(project_root).resolve() if project_root else Path.cwd().resolve()
        self._evaluators: dict[CertificationDimension, type] | None = None

    def _safe_path(self, module_path: str | None) -> Path:
        if not module_path:
            return self.project_root
        target = Path(module_path).resolve()
        if not target.is_relative_to(self.project_root):
            raise ValueError("Certification module path must remain inside the project root")
        return target

    @property
    def evaluators(self) -> dict[CertificationDimension, type]:
        if self._evaluators is None:
            from . import _EVALUATOR_MAP
            self._evaluators = dict(_EVALUATOR_MAP)
        return self._evaluators

    def evaluate_module(self, module_path: str | None = None) -> CertificationReport:
        target = self._safe_path(module_path)
        report = CertificationReport(module_path=str(target))

        for dimension, evaluator_cls in self.evaluators.items():
            evaluator = evaluator_cls(self.project_root)
            result = evaluator.evaluate(str(target))
            report.add_dimension(dimension, result)

        report.certification_level = self.get_certification_level(module_path, report)
        report.overall_score = report.calculate_overall()
        report.summary = self._generate_summary(report)
        return report

    def evaluate_dimension(
        self,
        dimension: CertificationDimension,
        module_path: str | None = None,
    ) -> CertificationReport:
        target = self._safe_path(module_path)
        report = CertificationReport(module_path=str(target))

        evaluator_cls = self.evaluators.get(dimension)
        if evaluator_cls is None:
            raise ValueError(f"Unknown dimension: {dimension}")
        evaluator = evaluator_cls(self.project_root)
        result = evaluator.evaluate(str(target))
        report.add_dimension(dimension, result)
        report.overall_score = report.calculate_overall()
        report.certification_level = self._determine_level(report.overall_score)
        return report

    def get_certification_level(
        self,
        module_path: str | None = None,
        report: CertificationReport | None = None,
    ) -> CertificationLevel:
        if report is None:
            report = self.evaluate_module(module_path)
        return self._determine_level(report.overall_score)

    def _determine_level(self, score: float) -> CertificationLevel:
        for threshold, level in self.LEVEL_THRESHOLDS:
            if score >= threshold:
                return level
        return CertificationLevel.BRONZE

    def _generate_summary(self, report: CertificationReport) -> str:
        dims = report.dimensions
        passed = sum(1 for d in dims.values() if d.passed)
        total = len(dims)
        weaknesses = [
            f"{dim.value}: {result.score:.2f}"
            for dim, result in dims.items()
            if result.score < 0.7
        ]

        summary = (
            f"{passed}/{total} dimensions passed. "
            f"Overall score: {report.overall_score:.1%}. "
            f"Level: {report.certification_level.value.upper()}. "
        )
        if weaknesses:
            summary += f"Areas needing improvement: {', '.join(weaknesses)}."
        else:
            summary += "All dimensions meet or exceed the 70% threshold."

        return summary
