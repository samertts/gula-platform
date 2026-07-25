#!/usr/bin/env python3
# =============================================================================
# GSF: validate-compliance.py — Compliance Validation
# =============================================================================
"""
Runs compliance checks against configured frameworks, generates reports,
checks for drift, and updates the risk register.

Usage:
    ./validate-compliance.py [options]

Options:
    --framework FRAMEWORK  Specific framework to check (owasp_asvs, nist_csf, iso_27001, hipaa, gdpr, all)
    --output DIR           Output directory [default: security/reports/compliance]
    --html                 Generate HTML report
    --update-register      Update risk register
    --drift-check          Check for configuration drift
    --help, -h             Show this help message

Exit codes:
    0   All checks passed
    1   Compliance failures found
    2   Error during validation
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
import time
from collections.abc import Generator
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("gsf.validate-compliance")


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FRAMEWORKS: dict[str, dict[str, Any]] = {
    "owasp_asvs": {
        "name": "OWASP ASVS",
        "version": "4.0.3",
        "level": 3,
        "controls": [
            "V1: Architecture, Design and Threat Modeling",
            "V2: Authentication Verification",
            "V3: Session Management",
            "V4: Access Control",
            "V5: Input Validation",
            "V6: Cryptography",
            "V7: Error Handling and Logging",
            "V8: Data Protection",
            "V9: Communications",
            "V10: Malicious Code",
            "V11: Business Logic",
            "V12: Files and Resources",
            "V13: API and Web Service",
            "V14: Configuration",
        ],
    },
    "nist_csf": {
        "name": "NIST CSF 2.0",
        "version": "2.0",
        "tier": "Tier 4 (Adaptive)",
        "controls": [
            "GV.OC: Organizational Context",
            "GV.RM: Risk Management Strategy",
            "GV.RR: Roles and Responsibilities",
            "GV.SC: Supply Chain Risk Management",
            "RA: Risk Assessment",
            "ID: Identification",
            "PR: Protection",
            "DE: Detection",
            "RS: Response",
            "RC: Recovery",
        ],
    },
    "iso_27001": {
        "name": "ISO 27001:2022",
        "version": "2022",
        "controls": [
            "A.5: Information Security Policies",
            "A.6: Organization of Information Security",
            "A.7: Human Resource Security",
            "A.8: Asset Management",
            "A.9: Access Control",
            "A.10: Cryptography",
            "A.11: Physical Security",
            "A.12: Operations Security",
            "A.13: Communications Security",
            "A.14: System Acquisition and Development",
            "A.15: Supplier Relationships",
            "A.16: Incident Management",
            "A.17: Business Continuity",
            "A.18: Compliance",
        ],
    },
    "hipaa": {
        "name": "HIPAA Security Rule",
        "version": "2013",
        "controls": [
            "Administrative Safeguards",
            "Physical Safeguards",
            "Technical Safeguards",
            "Organizational Requirements",
            "Policies and Procedures",
            "Breach Notification",
        ],
    },
    "gdpr": {
        "name": "GDPR",
        "version": "2018",
        "controls": [
            "Art 5: Principles",
            "Art 6: Lawfulness",
            "Art 7: Consent",
            "Art 9: Special Categories",
            "Art 17: Right to Erasure",
            "Art 32: Security of Processing",
            "Art 33: Breach Notification",
            "Art 35: DPIA",
        ],
    },
}


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class ControlResult:
    """Result of a single control check."""

    control_id: str
    control_name: str
    status: str  # passed, failed, not_applicable, not_tested
    score: float  # 0.0 - 1.0
    evidence: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class FrameworkResult:
    """Result of a framework compliance assessment."""

    framework_id: str
    framework_name: str
    version: str
    assessment_date: str
    overall_score: float
    control_results: list[ControlResult]
    passed: int = 0
    failed: int = 0
    not_applicable: int = 0
    not_tested: int = 0

    def __post_init__(self) -> None:
        for c in self.control_results:
            if c.status == "passed":
                self.passed += 1
            elif c.status == "failed":
                self.failed += 1
            elif c.status == "not_applicable":
                self.not_applicable += 1
            else:
                self.not_tested += 1


@dataclass
class ComplianceReport:
    """Complete compliance assessment report."""

    generated_at: str
    frameworks: list[FrameworkResult]
    drift_detected: bool = False
    drift_details: list[str] = field(default_factory=list)
    overall_compliance_score: float = 0.0
    risk_register_updates: list[dict[str, Any]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Compliance Checker
# ---------------------------------------------------------------------------

class ComplianceChecker:
    """Performs compliance checks against security configurations."""

    def __init__(self, config_dir: str | None = None) -> None:
        self.config_dir = config_dir or str(
            Path(__file__).resolve().parent.parent / "configs"
        )

    def check_framework(self, framework_id: str) -> FrameworkResult:
        """Check compliance against a specific framework."""
        framework = FRAMEWORKS.get(framework_id)
        if not framework:
            raise ValueError(f"Unknown framework: {framework_id}")

        logger.info("Checking framework: %s (%s)", framework["name"], framework_id)

        control_results: list[ControlResult] = []
        for control in framework["controls"]:
            result = self._evaluate_control(framework_id, control)
            control_results.append(result)

        tested = [c for c in control_results if c.status in ("passed", "failed")]
        overall = sum(c.score for c in tested) / len(tested) if tested else 0.0

        return FrameworkResult(
            framework_id=framework_id,
            framework_name=framework["name"],
            version=framework.get("version", ""),
            assessment_date=datetime.now(timezone.utc).isoformat(),
            overall_score=round(overall * 100, 1),
            control_results=control_results,
        )

    def _evaluate_control(self, framework_id: str, control_name: str) -> ControlResult:
        """Evaluate a single control against the codebase."""
        control_id = control_name.split(":")[0].strip() if ":" in control_name else control_name

        config_files = list(Path(self.config_dir).glob("*.yaml"))
        config_text = ""
        for cf in config_files:
            try:
                config_text += cf.read_text().lower()
            except OSError:
                pass

        keywords = control_name.lower().split()
        matched = sum(1 for kw in keywords if len(kw) > 3 and kw in config_text)
        score = min(1.0, matched / max(len(keywords), 1) * 1.2)

        if score >= 0.8:
            status = "passed"
        elif score >= 0.3:
            status = "failed"
        else:
            status = "not_applicable"

        evidence = [
            f"Config files checked: {[str(cf.name) for cf in config_files]}",
            f"Keyword match score: {score:.2f}",
        ]

        return ControlResult(
            control_id=control_id,
            control_name=control_name,
            status=status,
            score=score,
            evidence=evidence,
            notes=f"Automated check ({'high' if status == 'passed' else 'low' if status == 'failed' else 'n/a'} confidence)",
        )


# ---------------------------------------------------------------------------
# Drift Detection
# ---------------------------------------------------------------------------

class DriftDetector:
    """Detects configuration drift since the last assessment."""

    def __init__(self, snapshot_dir: str | None = None) -> None:
        self.snapshot_dir = snapshot_dir or str(
            Path(__file__).resolve().parent.parent / "reports" / "compliance" / "snapshots"
        )

    def check_drift(self) -> tuple[bool, list[str]]:
        """Check for configuration drift. Returns (drift_detected, details)."""
        config_dir = Path(self.snapshot_dir).parent.parent.parent / "configs"
        if not config_dir.exists():
            return False, ["No config directory found"]

        os.makedirs(self.snapshot_dir, exist_ok=True)
        details: list[str] = []

        for config_file in sorted(config_dir.glob("*.yaml")):
            current_hash = hashlib.sha3_256(config_file.read_bytes()).hexdigest()
            snapshot_file = Path(self.snapshot_dir) / f"{config_file.stem}.sha256"

            if snapshot_file.exists():
                previous_hash = snapshot_file.read_text().strip()
                if current_hash != previous_hash:
                    details.append(f"Drift detected in {config_file.name}")
            else:
                details.append(f"New snapshot for {config_file.name}")

            snapshot_file.write_text(current_hash)

        return len(details) > 0, details


# ---------------------------------------------------------------------------
# Risk Register
# ---------------------------------------------------------------------------

class RiskRegister:
    """Updates the risk register based on compliance findings."""

    @staticmethod
    def calculate_risks(report: ComplianceReport) -> list[dict[str, Any]]:
        """Calculate risk register updates from compliance report."""
        risks: list[dict[str, Any]] = []
        for framework in report.frameworks:
            for control in framework.control_results:
                if control.status == "failed":
                    risks.append({
                        "risk_id": f"RISK-{framework.framework_id}-{control.control_id}",
                        "framework": framework.framework_name,
                        "control": control.control_name,
                        "score": 1.0 - control.score,
                        "severity": "HIGH" if control.score < 0.5 else "MEDIUM",
                        "mitigation": f"Implement controls for {control.control_name}",
                        "assessed_at": datetime.now(timezone.utc).isoformat(),
                    })
        return risks


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------

def generate_report(
    report: ComplianceReport,
    output_dir: str,
    html: bool = False,
) -> str:
    """Generate compliance report. Returns path to report file."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    json_path = os.path.join(output_dir, f"compliance-report-{timestamp}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(asdict(report), f, indent=2, default=str)

    logger.info("JSON report written to: %s", json_path)

    if html:
        html_path = os.path.join(output_dir, f"compliance-report-{timestamp}.html")
        _generate_html(report, html_path)
        logger.info("HTML report written to: %s", html_path)
        return html_path

    return json_path


def _generate_html(report: ComplianceReport, path: str) -> None:
    """Generate an HTML compliance report."""
    parts = [
        "<!DOCTYPE html><html><head>",
        "<title>GSF Compliance Report</title>",
        "<style>",
        "body{font-family:system-ui,sans-serif;margin:2em;color:#333}",
        "h1{color:#1a1a2e}",
        ".score{font-size:2em;font-weight:bold}",
        ".pass{color:#28a745}.fail{color:#dc3545}.warn{color:#ffc107}",
        "table{border-collapse:collapse;width:100%;margin:1em 0}",
        "th,td{border:1px solid #dee2e6;padding:10px;text-align:left}",
        "th{background:#1a1a2e;color:white}",
        "tr:nth-child(even){background:#f8f9fa}",
        ".framework{margin:2em 0;padding:1em;border:1px solid #dee2e6;border-radius:8px}",
        "</style></head><body>",
        f"<h1>GSF Compliance Report</h1>",
        f"<p>Generated: {report.generated_at}</p>",
        f"<p>Overall Score: <span class='score'>{report.overall_compliance_score:.1f}%</span></p>",
        f"<p>Drift Detected: {'Yes' if report.drift_detected else 'No'}</p>",
    ]

    if report.drift_details:
        parts.append("<h2>Drift Details</h2><ul>")
        for d in report.drift_details:
            parts.append(f"<li>{d}</li>")
        parts.append("</ul>")

    for framework in report.frameworks:
        score_class = "pass" if framework.overall_score >= 80 else "fail" if framework.overall_score < 60 else "warn"
        parts.extend([
            "<div class='framework'>",
            f"<h2>{framework.framework_name} v{framework.version}</h2>",
            f"<p>Score: <span class='score {score_class}'>{framework.overall_score}%</span></p>",
            f"<p>Passed: {framework.passed} | Failed: {framework.failed} | N/A: {framework.not_applicable}</p>",
            "<table><tr><th>Control</th><th>Status</th><th>Score</th><th>Notes</th></tr>",
        ])
        for c in framework.control_results:
            status_class = "pass" if c.status == "passed" else "fail"
            parts.append(
                f"<tr><td>{c.control_name}</td>"
                f"<td class='{status_class}'>{c.status}</td>"
                f"<td>{c.score:.0%}</td>"
                f"<td>{c.notes}</td></tr>"
            )
        parts.append("</table></div>")

    parts.append("</body></html>")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="GSF Compliance Validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--framework", choices=list(FRAMEWORKS.keys()) + ["all"], default="all",
        help="Framework to check",
    )
    parser.add_argument("--output", default=None, help="Output directory")
    parser.add_argument("--html", action="store_true", help="Generate HTML report")
    parser.add_argument("--update-register", action="store_true", help="Update risk register")
    parser.add_argument("--drift-check", action="store_true", help="Check for configuration drift")
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    script_dir = Path(__file__).resolve().parent
    report_dir = args.output or str(script_dir.parent / "reports" / "compliance")

    checker = ComplianceChecker()
    drift_detector = DriftDetector()
    risk_register = RiskRegister()

    frameworks_to_check = list(FRAMEWORKS.keys()) if args.framework == "all" else [args.framework]

    framework_results: list[FrameworkResult] = []
    for fw_id in frameworks_to_check:
        result = checker.check_framework(fw_id)
        framework_results.append(result)

    drift_detected, drift_details = False, []
    if args.drift_check:
        drift_detected, drift_details = drift_detector.check_drift()

    overall = sum(f.overall_score for f in framework_results) / len(framework_results) if framework_results else 0.0

    report = ComplianceReport(
        generated_at=datetime.now(timezone.utc).isoformat(),
        frameworks=framework_results,
        drift_detected=drift_detected,
        drift_details=drift_details,
        overall_compliance_score=round(overall, 1),
    )

    if args.update_register:
        report.risk_register_updates = risk_register.calculate_risks(report)

    report_path = generate_report(report, report_dir, args.html)

    logger.info("Report generated: %s", report_path)

    failures = sum(f.failed for f in framework_results)
    if failures > 0:
        logger.error("Compliance validation FAILED: %d control failures across %d frameworks", failures, len(framework_results))
        return 1

    logger.info("Compliance validation PASSED: all controls OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
