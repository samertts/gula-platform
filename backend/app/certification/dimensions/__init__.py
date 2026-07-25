from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Evidence:
    name: str
    value: str | float | bool | None = None
    source: str = ""
    passed: bool = True


@dataclass
class Remediation:
    severity: str = "medium"
    message: str = ""
    effort: str = "medium"


@dataclass
class DimensionResult:
    score: float = 0.0
    passed: bool = False
    evidence: list[Evidence] = field(default_factory=list)
    remediations: list[Remediation] = field(default_factory=list)
    max_score: float = 1.0

    @property
    def percentage(self) -> float:
        return round(self.score / max(self.max_score, 1e-9) * 100, 1)


class DimensionEvaluator(ABC):
    def __init__(self, project_root: Path | str | None = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.evidence: list[Evidence] = []
        self.remediations: list[Remediation] = []

    @abstractmethod
    def evaluate(self, module_path: str | None = None) -> DimensionResult: ...

    def _add_evidence(
        self,
        name: str,
        value: str | float | bool | None = None,
        source: str = "",
        passed: bool = True,
    ) -> None:
        self.evidence.append(Evidence(name=name, value=value, source=source, passed=passed))

    def _add_remediation(
        self, message: str, severity: str = "medium", effort: str = "medium",
    ) -> None:
        self.remediations.append(Remediation(severity=severity, message=message, effort=effort))

    def _result(self, score: float) -> DimensionResult:
        return DimensionResult(
            score=round(min(max(score, 0.0), 1.0), 4),
            passed=score >= 0.7,
            evidence=self.evidence,
            remediations=self.remediations,
        )
