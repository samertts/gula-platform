"""Phase 8 — Output.

Generate BUILDER_IMPLEMENTATION_REPORT.md containing: completed work, created
files, updated files, architecture, future improvements, remaining risks, and
a readiness score. Deterministic rendering from the execution record.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.builder.core import utcnow
from scripts.kernel.core import REPO_ROOT

BUILDER_IMPLEMENTATION_REPORT = REPO_ROOT / "BUILDER_IMPLEMENTATION_REPORT.md"


@dataclass
class ImplementationRecord:
    """The full record rendered into the implementation report."""

    mission_id: str
    objective: str
    mission_type: str = ""
    complexity: str = ""
    risk: str = ""
    completed_work: list[str] = field(default_factory=list)
    created_files: list[str] = field(default_factory=list)
    updated_files: list[str] = field(default_factory=list)
    architecture: list[str] = field(default_factory=list)
    future_improvements: list[str] = field(default_factory=list)
    remaining_risks: list[str] = field(default_factory=list)
    readiness_score: float = 0.0
    generated_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {k: (list(v) if isinstance(v, list) else v) for k, v in vars(self).items()}


def render_markdown(record: ImplementationRecord) -> str:
    """Render the implementation report markdown."""
    lines = [
        "# BUILDER_IMPLEMENTATION_REPORT.md",
        "",
        f"**Mission:** {record.mission_id}",
        "",
        f"**Objective:** {record.objective}",
        "",
        f"- Type: {record.mission_type}",
        f"- Complexity: {record.complexity}",
        f"- Risk: {record.risk}",
        f"- Readiness score: {record.readiness_score}/100",
        "",
        "## Completed Work",
        "",
    ]
    lines += [f"- {item}" for item in record.completed_work] or ["_none_"]
    lines.append("")
    lines.append("## Created Files")
    lines.append("")
    lines += [f"- {item}" for item in record.created_files] or ["_none_"]
    lines.append("")
    lines.append("## Updated Files")
    lines.append("")
    lines += [f"- {item}" for item in record.updated_files] or ["_none_"]
    lines.append("")
    lines.append("## Architecture")
    lines.append("")
    lines += [f"- {item}" for item in record.architecture] or ["_none_"]
    lines.append("")
    lines.append("## Future Improvements")
    lines.append("")
    lines += [f"- {item}" for item in record.future_improvements] or ["_none_"]
    lines.append("")
    lines.append("## Remaining Risks")
    lines.append("")
    lines += [f"- {item}" for item in record.remaining_risks] or ["_none_"]
    lines.append("")
    lines.append("---")
    lines.append(f"Generated at {record.generated_at}")
    lines.append("")
    return "\n".join(lines)


def write_report(record: ImplementationRecord, path: Path | None = None) -> Path:
    """Write the implementation report and return its path."""
    target = path or BUILDER_IMPLEMENTATION_REPORT
    target.write_text(render_markdown(record), encoding="utf-8")
    return target


def readiness(record: ImplementationRecord) -> float:
    """Compute readiness from remaining risks and completed work."""
    risk_penalty = min(50.0, len(record.remaining_risks) * 10.0)
    work_bonus = min(50.0, len(record.completed_work) * 5.0)
    return round(max(0.0, min(100.0, 50.0 - risk_penalty + work_bonus)), 1)
