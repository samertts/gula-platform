from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .dimensions import DimensionResult
from .enums import CertificationDimension, CertificationLevel


@dataclass
class CertificationReport:
    module_path: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    overall_score: float = 0.0
    certification_level: CertificationLevel = CertificationLevel.BRONZE
    dimensions: dict[CertificationDimension, DimensionResult] = field(default_factory=dict)
    summary: str = ""

    def add_dimension(self, dimension: CertificationDimension, result: DimensionResult) -> None:
        self.dimensions[dimension] = result

    def calculate_overall(self) -> float:
        if not self.dimensions:
            return 0.0
        scores = [r.score for r in self.dimensions.values()]
        return round(sum(scores) / len(scores), 4)

    def to_dict(self) -> dict[str, Any]:
        return {
            "module_path": self.module_path,
            "timestamp": self.timestamp,
            "overall_score": self.overall_score,
            "certification_level": self.certification_level.value,
            "summary": self.summary,
            "dimensions": {
                dim.value: {
                    "score": result.score,
                    "percentage": result.percentage,
                    "passed": result.passed,
                    "evidence": [
                        {"name": e.name, "value": str(e.value) if e.value is not None else None, "source": e.source, "passed": e.passed}
                        for e in result.evidence
                    ],
                    "remediations": [
                        {"severity": r.severity, "message": r.message, "effort": r.effort}
                        for r in result.remediations
                    ],
                }
                for dim, result in self.dimensions.items()
            },
        }

    def to_markdown(self) -> str:
        lines = [
            f"# Certification Report: {self.module_path}",
            "",
            f"- **Timestamp:** {self.timestamp}",
            f"- **Overall Score:** {self.overall_score:.1%}",
            f"- **Certification Level:** {self.certification_level.value.upper()}",
            f"- **Summary:** {self.summary}",
            "",
            "## Dimension Scores",
            "",
            "| Dimension | Score | Passed |",
            "|-----------|-------|--------|",
        ]
        for dim, result in sorted(self.dimensions.items(), key=lambda x: x[1].score):
            passed_icon = "✅" if result.passed else "❌"
            lines.append(f"| {dim.value} | {result.score:.1%} | {passed_icon} |")

        lines.append("")
        for dim, result in sorted(self.dimensions.items(), key=lambda x: x[1].score):
            if not result.passed:
                lines.append(f"### {dim.value} — Remediations")
                for r in result.remediations:
                    lines.append(f"- [{r.severity.upper()}] {r.message}")
                lines.append("")

        return "\n".join(lines)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    def to_html(self) -> str:
        dims_rows = ""
        for dim, result in sorted(self.dimensions.items(), key=lambda x: x[1].score):
            color = "#22c55e" if result.passed else "#ef4444"
            dims_rows += f"""
            <tr>
                <td style="padding:8px;border-bottom:1px solid #e5e7eb;">{dim.value}</td>
                <td style="padding:8px;border-bottom:1px solid #e5e7eb;color:{color};font-weight:bold;">{result.score:.1%}</td>
                <td style="padding:8px;border-bottom:1px solid #e5e7eb;color:{color};">{'PASS' if result.passed else 'FAIL'}</td>
            </tr>"""

        remediations_html = ""
        for dim, result in sorted(self.dimensions.items(), key=lambda x: x[1].score):
            if not result.passed and result.remediations:
                remediations_html += f"""
                <h3 style="color:#374151;margin-top:20px;">{dim.value}</h3>
                <ul style="color:#6b7280;">"""
                for r in result.remediations:
                    remediations_html += f"<li><strong>[{r.severity.upper()}]</strong> {r.message}</li>"
                remediations_html += "</ul>"

        level_colors = {
            CertificationLevel.DIAMOND: "#1a5276",
            CertificationLevel.PLATINUM: "#6c757d",
            CertificationLevel.GOLD: "#f59e0b",
            CertificationLevel.SILVER: "#9ca3af",
            CertificationLevel.BRONZE: "#cd7f32",
        }
        level_color = level_colors.get(self.certification_level, "#374151")

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Certification Report</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; color: #1f2937; }}
h1 {{ color: #111827; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; }}
table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
th {{ text-align: left; padding: 10px 8px; background: #f9fafb; border-bottom: 2px solid #e5e7eb; }}
</style>
</head>
<body>
<h1>Certification Report</h1>
<p><strong>Module:</strong> {self.module_path}</p>
<p><strong>Timestamp:</strong> {self.timestamp}</p>
<p><strong>Overall Score:</strong> <span style="color:{level_color};font-size:1.2em;font-weight:bold;">{self.overall_score:.1%}</span></p>
<p><strong>Level:</strong> <span style="color:{level_color};font-size:1.5em;font-weight:bold;">{self.certification_level.value.upper()}</span></p>
<p><strong>Summary:</strong> {self.summary}</p>
<h2>Dimension Scores</h2>
<table>
<thead><tr><th>Dimension</th><th>Score</th><th>Status</th></tr></thead>
<tbody>{dims_rows}</tbody>
</table>
{remediations_html}
</body>
</html>"""


def generate_pdf_report(report: CertificationReport, output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    html = report.to_html()
    try:
        import pdfkit
        pdfkit.from_string(html, str(output))
        return output
    except ImportError:
        output.write_text(html)
        return output


def generate_json_report(report: CertificationReport, output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report.to_json(), encoding="utf-8")
    return output


def generate_markdown_report(report: CertificationReport, output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report.to_markdown(), encoding="utf-8")
    return output
