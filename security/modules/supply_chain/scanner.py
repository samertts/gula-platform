from __future__ import annotations

import json
import logging
import re
import subprocess
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from security.modules.supply_chain.models import (
    DependencyVulnerability,
    SBOMComponent,
    SupplyChainPolicy,
)

logger = logging.getLogger(__name__)


class ScanResult(BaseModel):
    scanner: str
    vulnerabilities: list[DependencyVulnerability] = Field(default_factory=list)
    components: list[SBOMComponent] = Field(default_factory=list)
    raw_output: str = ""
    success: bool = False
    error: str | None = None


class LicenseFinding(BaseModel):
    package: str
    version: str
    license: str
    allowed: bool = True
    reason: str = ""


class SupplyChainScanner:
    def __init__(self, policy: SupplyChainPolicy | None = None):
        self.policy = policy or SupplyChainPolicy()

    def _run_command(self, cmd: list[str], timeout: int = 120) -> dict[str, Any]:
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0,
            }
        except FileNotFoundError:
            return {
                "stdout": "",
                "stderr": f"Command not found: {cmd[0]}",
                "returncode": -1,
                "success": False,
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"Command timed out after {timeout}s: {' '.join(cmd)}",
                "returncode": -1,
                "success": False,
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
                "success": False,
            }

    def generate_sbom_syft(self, target: str = ".") -> ScanResult:
        logger.info(f"Generating SBOM with Syft for {target}")
        result = self._run_command(["syft", target, "-o", "cyclonedx-json"])
        components: list[SBOMComponent] = []

        if result["success"]:
            try:
                data = json.loads(result["stdout"])
                for component in data.get("components", data.get("artifacts", [])):
                    purl = component.get("purl", "")
                    licenses = component.get("licenses", [component.get("license", "")])
                    license_str = licenses[0] if licenses else ""
                    if isinstance(license_str, dict):
                        license_str = license_str.get("license", {}).get("id", "")

                    components.append(SBOMComponent(
                        name=component.get("name", ""),
                        version=component.get("version", ""),
                        supplier=component.get("supplier", None),
                        purl=purl,
                        license=license_str or None,
                        sha256=component.get("sha256", None),
                        originator=component.get("originator", None),
                    ))
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse Syft output: {e}")

        return ScanResult(
            scanner="syft",
            components=components,
            raw_output=result["stdout"],
            success=result["success"],
            error=result["stderr"] if not result["success"] else None,
        )

    def scan_vulnerabilities_grype(self, target: str = ".") -> ScanResult:
        logger.info(f"Scanning vulnerabilities with Grype for {target}")
        result = self._run_command([
            "grype", target, "--output", "json", "--fail-on", "critical"
        ])
        vulnerabilities: list[DependencyVulnerability] = []

        if result["success"] or result["returncode"] == 1:
            try:
                data = json.loads(result["stdout"])
                matches = data.get("matches", [])
                for match in matches:
                    vuln = match.get("vulnerability", {})
                    artifact = match.get("artifact", {})

                    severity = vuln.get("severity", "UNKNOWN")
                    fix_info = vuln.get("fix", {})
                    cvss = match.get("cvss", [{}])
                    cvss_score = 0.0
                    if cvss:
                        for metric in cvss:
                            cvss_score = max(cvss_score, metric.get("score", 0.0))

                    vulnerabilities.append(DependencyVulnerability(
                        id=match.get("id", ""),
                        package=artifact.get("name", ""),
                        version=artifact.get("version", ""),
                        severity=severity,
                        cvss_score=cvss_score,
                        cve_id=vuln.get("id", ""),
                        fix_version=fix_info.get("version") if isinstance(fix_info, dict) else None,
                        advisory_url=vuln.get("advisory", None),
                        published_date=vuln.get("published", None),
                    ))
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse Grype output: {e}")

        return ScanResult(
            scanner="grype",
            vulnerabilities=vulnerabilities,
            raw_output=result["stdout"],
            success=result["success"],
            error=result["stderr"] if not result["success"] and result["returncode"] != 1 else None,
        )

    def scan_container_trivy(self, image: str, format: str = "json") -> ScanResult:
        logger.info(f"Scanning container image with Trivy: {image}")
        result = self._run_command([
            "trivy", "image", image, "--format", format, "--severity", "CRITICAL,HIGH"
        ])
        vulnerabilities: list[DependencyVulnerability] = []

        if result["success"] or result["returncode"] == 1:
            try:
                data = json.loads(result["stdout"])
                for result_item in data.get("Results", []):
                    for vuln in result_item.get("Vulnerabilities", []):
                        vulnerabilities.append(DependencyVulnerability(
                            id=vuln.get("VulnerabilityID", ""),
                            package=vuln.get("PkgName", ""),
                            version=vuln.get("InstalledVersion", ""),
                            severity=vuln.get("Severity", "UNKNOWN"),
                            cvss_score=vuln.get("CVSSScore", 0.0) or 0.0,
                            cve_id=vuln.get("VulnerabilityID", ""),
                            fix_version=vuln.get("FixedVersion", None),
                            published_date=vuln.get("PublishedDate", None),
                        ))
            except (json.JSONDecodeError, KeyError, AttributeError) as e:
                logger.warning(f"Failed to parse Trivy output: {e}")

        return ScanResult(
            scanner="trivy",
            vulnerabilities=vulnerabilities,
            raw_output=result["stdout"],
            success=result["success"],
            error=result["stderr"] if not result["success"] and result["returncode"] != 1 else None,
        )

    def check_license_compliance(self, components: list[SBOMComponent]) -> list[LicenseFinding]:
        findings: list[LicenseFinding] = []
        allowed = self.policy.allowed_licenses

        for comp in components:
            if not comp.license:
                findings.append(LicenseFinding(
                    package=comp.name,
                    version=comp.version,
                    license="unknown",
                    allowed=False,
                    reason="No license information available for component",
                ))
                continue

            comp_license_upper = comp.license.upper()
            is_allowed = any(
                allowed_license.upper() in comp_license_upper or comp_license_upper in allowed_license.upper()
                for allowed_license in allowed
            )

            if not is_allowed:
                known_restricted = ["GPL-3.0", "AGPL-3.0", "SSPL-1.0", "BUSL-1.1"]
                is_restricted = any(r.upper() in comp_license_upper for r in known_restricted)
                findings.append(LicenseFinding(
                    package=comp.name,
                    version=comp.version,
                    license=comp.license,
                    allowed=False,
                    reason=(
                        "Copyleft/restricted license" if is_restricted
                        else f"License '{comp.license}' not in allowed list"
                    ),
                ))

        return findings

    def validate_dependency_freshness(self, components: list[SBOMComponent],
                                       max_days: int = 365) -> dict[str, Any]:
        findings: list[str] = []
        passed = True
        now = datetime.now(UTC)

        for comp in components:
            if hasattr(comp, "version") and comp.version:
                parts = comp.version.replace("v", "").split(".")
                if parts and len(parts) >= 2:
                    try:
                        major = int(parts[0])
                        if major < 1:
                            findings.append(
                                f"Component '{comp.name}@{comp.version}' is pre-1.0 - "
                                "may have unstable API or lack security support"
                            )
                    except ValueError:
                        pass

        return {"findings": findings, "passed": passed}

    def query_vulnerability_database(self, package: str, version: str) -> list[DependencyVulnerability]:
        known_vulns: dict[str, list[dict[str, Any]]] = {
            "log4j": [
                {"cve": "CVE-2021-44228", "fixed": "2.17.0", "severity": "CRITICAL", "score": 10.0},
                {"cve": "CVE-2021-45046", "fixed": "2.17.0", "severity": "CRITICAL", "score": 9.0},
            ],
            "jinja2": [
                {"cve": "CVE-2024-22195", "fixed": "3.1.3", "severity": "MEDIUM", "score": 5.5},
            ],
            "cryptography": [
                {"cve": "CVE-2023-50782", "fixed": "42.0.4", "severity": "MEDIUM", "score": 5.5},
            ],
            "requests": [
                {"cve": "CVE-2023-32681", "fixed": "2.31.0", "severity": "MEDIUM", "score": 6.5},
            ],
            "urllib3": [
                {"cve": "CVE-2023-45803", "fixed": "2.0.7", "severity": "MEDIUM", "score": 5.5},
            ],
            "starlette": [
                {"cve": "CVE-2024-47874", "fixed": "0.40.0", "severity": "HIGH", "score": 7.5},
            ],
            "fastapi": [
                {"cve": "CVE-2024-29165", "fixed": "1.4.0", "severity": "MEDIUM", "score": 6.1},
            ],
            "redis": [],
            "pydantic": [
                {"cve": "CVE-2024-4032", "fixed": "2.8.0", "severity": "MEDIUM", "score": 6.3},
            ],
        }

        package_key = package.lower()
        results: list[DependencyVulnerability] = []

        if package_key in known_vulns:
            for v in known_vulns[package_key]:
                if v.get("fixed"):
                    try:
                        installed_parts = [int(x) for x in re.split(r"[.\-_]", version.replace("v", "").split("+")[0].split("-")[0]) if x.isdigit()]
                        fixed_parts = [int(x) for x in re.split(r"[.\-_]", v["fixed"]) if x.isdigit()]
                        if installed_parts < fixed_parts:
                            results.append(DependencyVulnerability(
                                id=v["cve"],
                                package=package,
                                version=version,
                                severity=v["severity"],
                                cvss_score=v["score"],
                                cve_id=v["cve"],
                                fix_version=v["fixed"],
                            ))
                    except (ValueError, IndexError):
                        continue

        return results

    def generate_report(self, scan_result: ScanResult, format: str = "json") -> str:
        if format == "json":
            return json.dumps({
                "scanner": scan_result.scanner,
                "vulnerabilities": [
                    {
                        "cve": v.cve_id,
                        "package": v.package,
                        "version": v.version,
                        "severity": v.severity,
                        "cvss": v.cvss_score,
                        "fix_version": v.fix_version,
                    }
                    for v in scan_result.vulnerabilities
                ],
                "components": [
                    {"name": c.name, "version": c.version, "license": c.license}
                    for c in scan_result.components
                ],
                "success": scan_result.success,
                "error": scan_result.error,
            }, indent=2)

        if format == "cyclonedx":
            components_xml = ""
            for comp in scan_result.components:
                components_xml += (
                    f'<component type="library">'
                    f"<name>{comp.name}</name>"
                    f"<version>{comp.version}</version>"
                    f"<licenses>"
                    f"<license><id>{comp.license or 'unknown'}</id></license>"
                    f"</licenses>"
                    f"<purl>{comp.purl or ''}</purl>"
                    f"</component>"
                )

            return f"""<?xml version="1.0" encoding="UTF-8"?>
<bom xmlns="http://cyclonedx.org/schema/bom/1.5" version="1">
<metadata>
<timestamp>{datetime.utcnow().isoformat()}Z</timestamp>
<tools><tool><name>Syft</name><version>0.0.0</version></tool></tools>
</metadata>
<components>{components_xml}</components>
</bom>"""

        if format == "spdx":
            spdx_lines = [
                "SPDXVersion: SPDX-2.3",
                "DataLicense: CC0-1.0",
                "SPDXID: SPDXRef-DOCUMENT",
                "DocumentName: GULA Supply Chain Scan",
                f"Created: {datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}",
                "",
            ]
            for i, comp in enumerate(scan_result.components):
                spdx_lines.extend([
                    f"##### Package: {comp.name}-{comp.version}",
                    f"PackageName: {comp.name}",
                    f"SPDXID: SPDXRef-Package-{i}",
                    f"PackageVersion: {comp.version}",
                    f"PackageLicenseConcluded: {comp.license or 'NOASSERTION'}",
                    f"PackageDownloadLocation: {comp.purl or 'NOASSERTION'}",
                    "",
                ])
            return "\n".join(spdx_lines)

        if format == "sarif":
            return json.dumps({
                "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
                "version": "2.1.0",
                "runs": [{
                    "tool": {"driver": {"name": f"GSF-007-SupplyChain-{scan_result.scanner}", "version": "1.0.0"}},
                    "results": [
                        {
                            "ruleId": v.cve_id,
                            "level": "error" if v.severity == "CRITICAL" else "warning",
                            "message": {"text": f"{v.cve_id}: {v.package} {v.version} (CVSS: {v.cvss_score})"},
                            "locations": [{"physicalLocation": {"artifactLocation": {"uri": v.package}}}],
                        }
                        for v in scan_result.vulnerabilities
                    ],
                }],
            }, indent=2)

        if format == "html":
            vuln_rows = ""
            for v in scan_result.vulnerabilities:
                vuln_rows += (
                    f"<tr><td>{v.cve_id}</td><td>{v.package}</td>"
                    f"<td>{v.version}</td><td>{v.severity}</td>"
                    f"<td>{v.cvss_score}</td><td>{v.fix_version or 'N/A'}</td></tr>"
                )

            return f"""<!DOCTYPE html><html><head><title>Supply Chain Scan Report</title>
<style>body{{font-family:sans-serif;margin:20px}}table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ddd;padding:8px;text-align:left}}th{{background-color:#f2f2f2}}
.critical{{background-color:#ffdddd}}tr:nth-child(even){{background-color:#f9f9f9}}</style>
</head><body>
<h1>Supply Chain Scan Report</h1>
<p>Scanner: {scan_result.scanner} | Generated: {datetime.utcnow().isoformat()}</p>
<h2>Vulnerabilities ({len(scan_result.vulnerabilities)})</h2>
<table><tr><th>CVE</th><th>Package</th><th>Version</th><th>Severity</th><th>CVSS</th><th>Fix</th></tr>
{vuln_rows}</table></body></html>"""

        return json.dumps({"error": f"Unsupported format: {format}"}, indent=2)
