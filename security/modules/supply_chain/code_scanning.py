from __future__ import annotations

import json
import logging
import os
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field

from security.modules.supply_chain.models import DependencyVulnerability

logger = logging.getLogger(__name__)


class CodeScanFinding(BaseModel):
    rule_id: str
    tool: str
    severity: str
    path: str
    line: int
    column: int = 0
    message: str
    description: str = ""
    cwe: Optional[str] = None
    remediation: str = ""


class CodeScanResult(BaseModel):
    tool: str
    findings: List[CodeScanFinding] = Field(default_factory=list)
    raw_output: str = ""
    success: bool = False
    error: Optional[str] = None
    quality_gate_passed: bool = True
    quality_gate_reasons: List[str] = Field(default_factory=list)


class CodeScanner:
    def __init__(self):
        self._finding_cache: Dict[str, List[CodeScanFinding]] = {}

    def _run_tool(self, cmd: List[str], timeout: int = 300) -> Dict[str, Any]:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0,
            }
        except FileNotFoundError:
            return {"stdout": "", "stderr": f"Tool not found: {cmd[0]}", "returncode": -1, "success": False}
        except subprocess.TimeoutExpired:
            return {"stdout": "", "stderr": f"Timed out after {timeout}s", "returncode": -1, "success": False}
        except Exception as e:
            return {"stdout": "", "stderr": str(e), "returncode": -1, "success": False}

    def run_codeql(self, source_path: str, query_path: Optional[str] = None) -> CodeScanResult:
        logger.info(f"Running CodeQL on {source_path}")
        db_path = f"/tmp/codeql-db-{uuid4().hex[:8]}"

        commands = [
            ["codeql", "database", "create", db_path, "--language=python", f"--source-root={source_path}"],
            ["codeql", "database", "analyze", db_path, "--format=sarif-latest", "--output=/tmp/codeql-results.sarif"],
        ]

        for cmd in commands:
            result = self._run_tool(cmd)
            if not result["success"] and "already exists" not in result["stderr"]:
                logger.warning(f"CodeQL command failed: {result['stderr']}")

        findings: List[CodeScanFinding] = []
        sarif_path = "/tmp/codeql-results.sarif"
        if os.path.exists(sarif_path):
            try:
                with open(sarif_path) as f:
                    sarif_data = json.load(f)
                for run in sarif_data.get("runs", []):
                    for result_entry in run.get("results", []):
                        rule_id = result_entry.get("ruleId", "")
                        loc = result_entry.get("locations", [{}])[0].get("physicalLocation", {})
                        region = loc.get("region", {})
                        message = result_entry.get("message", {}).get("text", "")
                        level = result_entry.get("level", "warning")

                        findings.append(CodeScanFinding(
                            rule_id=rule_id,
                            tool="codeql",
                            severity="CRITICAL" if level == "error" else "HIGH" if level == "warning" else "MEDIUM",
                            path=loc.get("artifactLocation", {}).get("uri", ""),
                            line=region.get("startLine", 0),
                            column=region.get("startColumn", 0),
                            message=message,
                            cwe=result_entry.get("properties", {}).get("cwe", None),
                            remediation="Review and fix the identified vulnerability",
                        ))
            except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
                logger.warning(f"Failed to parse CodeQL SARIF output: {e}")

        self._finding_cache["codeql"] = findings

        return CodeScanResult(
            tool="codeql",
            findings=findings,
            success=len(findings) > 0 or True,
            quality_gate_passed=len([f for f in findings if f.severity in ("CRITICAL", "HIGH")]) == 0,
        )

    def run_semgrep(self, target: str, rules: Optional[List[str]] = None) -> CodeScanResult:
        logger.info(f"Running Semgrep on {target}")

        cmd = ["semgrep", "--json", "--quiet", target]
        if rules:
            for rule in rules:
                cmd.extend(["--config", rule])
        else:
            cmd.extend(["--config", "auto"])

        result = self._run_tool(cmd)
        findings: List[CodeScanFinding] = []

        if result["success"]:
            try:
                data = json.loads(result["stdout"])
                for semgrep_result in data.get("results", []):
                    path = semgrep_result.get("path", "")
                    start = semgrep_result.get("start", {})
                    extra = semgrep_result.get("extra", {})
                    severity = extra.get("severity", "WARNING").upper()
                    metadata = extra.get("metadata", {})

                    findings.append(CodeScanFinding(
                        rule_id=extra.get("check_id", "unknown"),
                        tool="semgrep",
                        severity=severity if severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW") else "MEDIUM",
                        path=path,
                        line=start.get("line", 0),
                        column=start.get("col", 0),
                        message=extra.get("message", ""),
                        description=extra.get("description", ""),
                        cwe=metadata.get("cwe", None),
                        remediation=metadata.get("fix", extra.get("fix", "")),
                    ))
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse Semgrep output: {e}")

        self._finding_cache["semgrep"] = findings

        return CodeScanResult(
            tool="semgrep",
            findings=findings,
            raw_output=result["stdout"],
            success=result["success"],
            error=result["stderr"] if not result["success"] else None,
        )

    def run_bandit(self, target: str) -> CodeScanResult:
        logger.info(f"Running Bandit SAST on {target}")
        result = self._run_tool(["bandit", "-r", target, "-f", "json"])
        findings: List[CodeScanFinding] = []

        if result["success"]:
            try:
                data = json.loads(result["stdout"])
                for bandit_result in data.get("results", []):
                    findings.append(CodeScanFinding(
                        rule_id=bandit_result.get("test_id", ""),
                        tool="bandit",
                        severity=bandit_result.get("issue_severity", "MEDIUM").upper(),
                        path=bandit_result.get("filename", ""),
                        line=bandit_result.get("line_number", 0),
                        column=bandit_result.get("col_offset", 0),
                        message=bandit_result.get("issue_text", ""),
                        description=bandit_result.get("test_name", ""),
                        cwe=bandit_result.get("cwe", ["N/A"])[0] if bandit_result.get("cwe") else None,
                        remediation=bandit_result.get("recommendation", ""),
                    ))
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse Bandit output: {e}")

        self._finding_cache["bandit"] = findings

        return CodeScanResult(
            tool="bandit",
            findings=findings,
            raw_output=result["stdout"],
            success=result["success"],
            error=result["stderr"] if not result["success"] else None,
        )

    def run_checkov(self, target: str) -> CodeScanResult:
        logger.info(f"Running Checkov on {target}")
        result = self._run_tool(["checkov", "--directory", target, "--output", "json", "--quiet"])
        findings: List[CodeScanFinding] = []

        if result["success"]:
            try:
                data = json.loads(result["stdout"])
                for check_type, check_results in data.items():
                    if isinstance(check_results, dict):
                        for chk_id, failures in check_results.get("failed_checks", {}).items():
                            if isinstance(failures, dict):
                                failures = [failures]
                            for failure in (failures if isinstance(failures, list) else [failures]):
                                findings.append(CodeScanFinding(
                                    rule_id=failure.get("check_id", ""),
                                    tool="checkov",
                                    severity="HIGH" if failure.get("severity", "").upper() in ("CRITICAL", "HIGH") else "MEDIUM",
                                    path=failure.get("file_path", ""),
                                    line=failure.get("file_line_range", [0, 0])[0],
                                    message=failure.get("check_name", ""),
                                    description=failure.get("guideline", ""),
                                    cwe=None,
                                    remediation=failure.get("remediation", ""),
                                ))
            except (json.JSONDecodeError, KeyError, AttributeError) as e:
                logger.warning(f"Failed to parse Checkov output: {e}")

        self._finding_cache["checkov"] = findings

        return CodeScanResult(
            tool="checkov",
            findings=findings,
            raw_output=result["stdout"],
            success=result["success"],
            error=result["stderr"] if not result["success"] else None,
        )

    def aggregate_results(self, results: List[CodeScanResult]) -> Dict[str, Any]:
        all_findings: List[CodeScanFinding] = []
        seen: Set[str] = set()

        for result in results:
            for finding in result.findings:
                dedup_key = f"{finding.rule_id}:{finding.path}:{finding.line}"
                if dedup_key not in seen:
                    seen.add(dedup_key)
                    all_findings.append(finding)

        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for f in all_findings:
            if f.severity in severity_counts:
                severity_counts[f.severity] += 1

        return {
            "total_findings": len(all_findings),
            "unique_findings": all_findings,
            "severity_counts": severity_counts,
            "deduplication_ratio": len(all_findings) / max(len([r for r in results for f in r.findings]), 1),
        }

    def generate_sarif_output(self, findings: List[CodeScanFinding], tool_name: str = "GSF-007-CodeScan") -> str:
        sarif_results = []
        for f in findings:
            sarif_results.append({
                "ruleId": f.rule_id,
                "level": "error" if f.severity == "CRITICAL" else "warning",
                "message": {"text": f"{f.message}"},
                "locations": [{
                    "physicalLocation": {
                        "artifactLocation": {"uri": f.path},
                        "region": {"startLine": f.line, "startColumn": f.column or 1},
                    }
                }],
            })

        return json.dumps({
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [{
                "tool": {"driver": {"name": tool_name, "version": "1.0.0"}},
                "results": sarif_results,
            }],
        }, indent=2)

    def generate_pr_comments(self, findings: List[CodeScanFinding]) -> List[Dict[str, Any]]:
        comments: List[Dict[str, Any]] = []

        for f in findings[:50]:
            comment = {
                "path": f.path,
                "line": f.line,
                "body": (
                    f"**{f.tool}**: {f.severity} - {f.message}\n\n"
                    f"*Rule*: {f.rule_id}\n"
                    f"*CWE*: {f.cwe or 'N/A'}\n"
                ),
            }
            if f.remediation:
                comment["body"] += f"\n**Suggested fix**: {f.remediation}\n"
            comments.append(comment)

        return comments

    def evaluate_quality_gate(self, findings: List[CodeScanFinding],
                               thresholds: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        thresholds = thresholds or {"CRITICAL": 0, "HIGH": 5, "MEDIUM": 20}

        severity_counts: Dict[str, int] = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for f in findings:
            if f.severity in severity_counts:
                severity_counts[f.severity] += 1

        reasons: List[str] = []
        passed = True

        for severity, threshold in thresholds.items():
            count = severity_counts.get(severity, 0)
            if count > threshold:
                reasons.append(f"Found {count} {severity} findings (threshold: {threshold})")
                passed = False

        return {"passed": passed, "reasons": reasons, "counts": severity_counts, "thresholds": thresholds}

    def full_scan(self, target: str) -> List[CodeScanResult]:
        results: List[CodeScanResult] = []

        bandit_result = self.run_bandit(target)
        if bandit_result.success:
            results.append(bandit_result)

        semgrep_result = self.run_semgrep(target)
        if semgrep_result.success:
            results.append(semgrep_result)

        codeql_result = self.run_codeql(target)
        results.append(codeql_result)

        checkov_result = self.run_checkov(target)
        results.append(checkov_result)

        return results
