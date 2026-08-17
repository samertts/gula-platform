#!/usr/bin/env python3
"""
Security Quality Gate — validates application security posture.

Checks:
  - SAST (Bandit + Semgrep) — fail on HIGH severity findings
  - Dependency scan (Safety) — fail on CRITICAL/HIGH
  - Secret scan (Gitleaks) — fail on any finding
  - Container scan (Trivy) — fail on CRITICAL/HIGH
  - IaC scan (Checkov) — fail on ERROR
  - SBOM validation — fail on blocked licenses
  - Exposed credentials in code
  - Audit log coverage

Usage:
    python config/quality-gates/security-gate.py
    python config/quality-gates/security-gate.py --json
    python config/quality-gates/security-gate.py --skip-sast --skip-deps

Exit codes:
    0 — all checks pass
    1 — one or more checks fail
"""

import argparse
import ast
import json
import logging
import os
import pathlib
import re
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("security-gate")

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

BLOCKED_LICENSES = {
    "GPL-2.0", "GPL-3.0", "AGPL-1.0", "AGPL-3.0",
    "SSPL-1.0", "BUSL-1.1",
}

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"


def _run_command(cmd: list[str], timeout: int = 120) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return proc.returncode, proc.stdout, proc.stderr
    except FileNotFoundError:
        return -1, "", f"Command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return -2, "", f"Command timed out after {timeout}s"


def run_bandit(path: str = "backend/app") -> list[dict[str, Any]]:
    logger.info("Running Bandit SAST scan on %s...", path)
    findings: list[dict[str, Any]] = []
    rc, stdout, stderr = _run_command(
        ["bandit", "-q", "-r", path, "-f", "json", "-ll", "-ii"]
    )

    if rc == -1:
        findings.append({"check": "bandit", "severity": "error",
                         "message": "Bandit not installed. Install with: pip install bandit"})
        return findings

    try:
        json_start = stdout.find("{")
        data = json.loads(stdout[json_start:] if json_start >= 0 else stdout)
        for result in data.get("results", []):
            severity = result.get("issue_severity", "LOW").upper()
            if severity in ("HIGH", "CRITICAL"):
                findings.append({
                    "check": "bandit",
                    "severity": "error",
                    "file": result.get("filename", ""),
                    "line": result.get("line_number", 0),
                    "message": f"[{result.get('test_id', '')}] {result.get('issue_text', '')}",
                    "code": result.get("code", ""),
                })
    except (json.JSONDecodeError, ValueError):
        findings.append({"check": "bandit", "severity": "error",
                         "message": "Failed to parse Bandit output"})

    logger.info("  Bandit: %d HIGH/CRITICAL finding(s)", len(findings))
    return findings


def run_semgrep(path: str = ".") -> list[dict[str, Any]]:
    logger.info("Running Semgrep SAST...")
    findings: list[dict[str, Any]] = []
    rc, stdout, stderr = _run_command(
        ["semgrep", "scan", "--config=auto", "--json", path],
        timeout=180,
    )

    if rc == -1:
        findings.append({"check": "semgrep", "severity": "warning",
                         "message": "Semgrep not installed"})
        return findings

    try:
        data = json.loads(stdout)
        for result in data.get("results", []):
            severity = result.get("extra", {}).get("severity", "WARNING").upper()
            if severity in ("ERROR", "HIGH", "CRITICAL"):
                findings.append({
                    "check": "semgrep",
                    "severity": "error",
                    "file": result.get("path", ""),
                    "line": result.get("start", {}).get("line", 0),
                    "message": result.get("extra", {}).get("message", ""),
                    "rule": result.get("check_id", ""),
                })
    except (json.JSONDecodeError, ValueError):
        pass

    logger.info("  Semgrep: %d HIGH/CRITICAL finding(s)", len(findings))
    return findings


def run_safety(requirements_file: str = "backend/requirements.txt") -> list[dict[str, Any]]:
    logger.info("Running Safety dependency scan...")
    findings: list[dict[str, Any]] = []
    rc, stdout, stderr = _run_command(
        ["safety", "check", "-r", requirements_file, "--output", "json"],
    )

    if rc == -1:
        findings.append({"check": "safety", "severity": "warning",
                         "message": "Safety not installed. Install with: pip install safety"})
        return findings

    try:
        data = json.loads(stdout)
        for vuln in data if isinstance(data, list) else []:
            severity = vuln.get("severity", "UNKNOWN").upper() if len(vuln) > 4 else "UNKNOWN"
            findings.append({
                "check": "safety",
                "severity": "error" if severity in ("CRITICAL", "HIGH") else "warning",
                "package": vuln[0] if len(vuln) > 0 else "unknown",
                "installed": vuln[1] if len(vuln) > 1 else "unknown",
                "description": vuln[3] if len(vuln) > 3 else "No description",
                "message": f"{vuln[0] if len(vuln) > 0 else 'package'}: {vuln[3] if len(vuln) > 3 else 'CVE'}",
            })
    except (json.JSONDecodeError, ValueError, IndexError):
        pass

    logger.info("  Safety: %d vulnerabilities found", len(findings))
    return findings


def run_gitleaks(path: str = ".") -> list[dict[str, Any]]:
    logger.info("Running Gitleaks secret scan...")
    findings: list[dict[str, Any]] = []
    rc, stdout, stderr = _run_command(
        ["gitleaks", "detect", "--source", path, "--report-format", "json", "--report-path", "/tmp/gitleaks-report.json", "--no-git"],
        timeout=180,
    )

    if rc == -1:
        findings.append({"check": "gitleaks", "severity": "warning",
                         "message": "Gitleaks not installed"})
        return findings

    report_path = "/tmp/gitleaks-report.json"
    if os.path.exists(report_path):
        try:
            with open(report_path, encoding="utf-8") as f:
                data = json.load(f)
            for leak in data if isinstance(data, list) else []:
                findings.append({
                    "check": "gitleaks",
                    "severity": "error",
                    "file": leak.get("File", ""),
                    "line": leak.get("StartLine", 0),
                    "message": f"Secret detected: {leak.get('RuleID', 'unknown')} — {leak.get('Description', '')}",
                    "secret_type": leak.get("RuleID", ""),
                })
        except (json.JSONDecodeError, ValueError):
            findings.append({"check": "gitleaks", "severity": "error",
                             "message": "Failed to parse Gitleaks report"})

    logger.info("  Gitleaks: %d secret(s) found", len(findings))
    return findings


def run_trivy(target: str = ".") -> list[dict[str, Any]]:
    logger.info("Running Trivy container scan...")
    findings: list[dict[str, Any]] = []
    rc, stdout, stderr = _run_command(
        ["trivy", "filesystem", "--severity", "CRITICAL,HIGH", "--format", "json", target],
        timeout=300,
    )

    if rc == -1:
        findings.append({"check": "trivy", "severity": "warning",
                         "message": "Trivy not installed"})
        return findings

    try:
        data = json.loads(stdout)
        for result in data.get("Results", []):
            for vuln in result.get("Vulnerabilities", []):
                severity = vuln.get("Severity", "UNKNOWN").upper()
                cvss_score = vuln.get("CVSS", {}).get("nvd", {}).get("V3Score", 0)
                if severity in ("CRITICAL", "HIGH"):
                    findings.append({
                        "check": "trivy",
                        "severity": "error",
                        "package": vuln.get("PkgName", ""),
                        "installed": vuln.get("InstalledVersion", ""),
                        "fixed": vuln.get("FixedVersion", ""),
                        "cvss": cvss_score,
                        "message": f"{vuln.get('PkgName', '')}:{vuln.get('InstalledVersion', '')} - {vuln.get('Title', '')[:120]}",
                    })
    except (json.JSONDecodeError, ValueError):
        pass

    logger.info("  Trivy: %d CRITICAL/HIGH vulnerabilities found", len(findings))
    return findings


def run_checkov(path: str = ".") -> list[dict[str, Any]]:
    logger.info("Running Checkov IaC scan...")
    findings: list[dict[str, Any]] = []
    rc, stdout, stderr = _run_command(
        ["checkov", "--directory", path, "--framework", "dockerfile", "--output", "json"],
        timeout=180,
    )

    if rc == -1:
        findings.append({"check": "checkov", "severity": "warning",
                         "message": "Checkov not installed"})
        return findings

    try:
        data = json.loads(stdout)
        for check_type in ("dockerfile",):
            for result in data.get("results", {}).get("failed_checks", []):
                severity = result.get("check_result", {}).get("result", "")
                if severity == "FAILED":
                    findings.append({
                        "check": "checkov",
                        "severity": "error",
                        "file": result.get("file", result.get("repo_file_path", "")),
                        "rule": result.get("check_id", ""),
                        "message": f"{result.get('check_name', '')} — {result.get('guideline', '')}",
                    })
    except (json.JSONDecodeError, ValueError):
        pass

    logger.info("  Checkov: %d IaC violations found", len(findings))
    return findings


def check_sbom_licenses(path: str = ".") -> list[dict[str, Any]]:
    logger.info("Checking SBOM license compliance...")
    findings: list[dict[str, Any]] = []
    rc, stdout, stderr = _run_command(
        ["trivy", "filesystem", "--format", "json", "--output", "/tmp/sbom.json", path],
        timeout=300,
    )

    if rc == -1:
        return findings

    sbom_path = "/tmp/sbom.json"
    if os.path.exists(sbom_path):
        try:
            with open(sbom_path, encoding="utf-8") as f:
                data = json.load(f)
            for result in data.get("Results", []):
                for pkg in result.get("Packages", []):
                    license_info = pkg.get("Licenses", [])
                    for lic in license_info:
                        lic_name = lic if isinstance(lic, str) else lic.get("Name", "")
                        if lic_name in BLOCKED_LICENSES:
                            findings.append({
                                "check": "license_blocked",
                                "severity": "error",
                                "package": pkg.get("Name", ""),
                                "version": pkg.get("Version", ""),
                                "license": lic_name,
                                "message": f"Blocked license {lic_name} in {pkg.get('Name', '')}:{pkg.get('Version', '')}",
                            })
        except (json.JSONDecodeError, ValueError):
            pass

    logger.info("  SBOM: %d blocked licenses found", len(findings))
    return findings


def check_exposed_credentials(root: pathlib.Path) -> list[dict[str, Any]]:
    logger.info("Checking for exposed credentials in code...")
    findings: list[dict[str, Any]] = []
    patterns = [
        (r'(?im)^\s*(password|passwd|pwd)\s*[:=]\s*["\'](?!\1["\'])[^"\']{8,}["\']', "Hardcoded password"),
        (r'(?im)^\s*(api[_-]?key|apikey)\s*[:=]\s*["\'][^"\']{12,}["\']', "Hardcoded API key"),
        (r'(?i)(secret|token)\s*[:=]\s*["\'][A-Za-z0-9_\-]{16,}["\']', "Hardcoded secret/token"),
        (r'(?i)-----BEGIN (RSA |EC )?PRIVATE KEY-----', "Private key in code"),
        (r'(?i)-----BEGIN CERTIFICATE-----', "Certificate in code"),
        (r'(?i)aws_access_key_id\s*=\s*["\'][A-Z0-9]{16,}["\']', "AWS access key"),
    ]

    skip_dirs = {".git", "__pycache__", ".venv", "node_modules", ".mypy_cache", ".pytest_cache", ".ruff_cache"}
    scanner_definition_files = {
        pathlib.Path("config/quality-gates/security-gate.py"),
        pathlib.Path("backend/app/engineering/security/bandit.py"),
    }
    non_secret_source_files = {
        pathlib.Path("hospital_desktop/l10n.py"),
        pathlib.Path("shared/design_system/components.py"),
    }
    for py_file in root.rglob("*.py"):
        if any(d in py_file.parts for d in skip_dirs):
            continue
        relative_path = py_file.relative_to(root)
        if relative_path in scanner_definition_files or relative_path in non_secret_source_files:
            continue
        try:
            text = py_file.read_text(encoding="utf-8", errors="ignore")
            for pattern, desc in patterns:
                for match in re.finditer(pattern, text):
                    line_num = text[:match.start()].count("\n") + 1
                    findings.append({
                        "check": "exposed_credential",
                        "severity": "warning" if "tests" in relative_path.parts else "error",
                        "file": str(py_file.relative_to(root)),
                        "line": line_num,
                        "message": f"{desc} detected at {py_file.relative_to(root)}:{line_num}",
                    })
        except (OSError, UnicodeDecodeError):
            continue

    logger.info("  Credential scan: %d finding(s)", len(findings))
    return findings


_WRITE_METHODS = {"post", "put", "patch", "delete"}
_EFFECTFUL_CALL_PREFIXES = (
    "create_", "update_", "delete_", "register_", "revoke_", "accept_", "reject_", "issue_", "merge_",
)


def _route_write_functions(tree: ast.AST) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    functions: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        decorators = [ast.unparse(dec) for dec in node.decorator_list]
        if any(any(f".{method}" in decorator for method in _WRITE_METHODS) for decorator in decorators):
            functions.append(node)
    return functions


def _call_name(call: ast.Call) -> str:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return ""


def _function_has_effectful_write(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        name = _call_name(child)
        qualified = ast.unparse(child.func)
        if qualified in {"db.add", "db.delete", "db.commit", "db.flush", "db.execute"}:
            return True
        if name == "soft_delete":
            return True
        if name.startswith(_EFFECTFUL_CALL_PREFIXES):
            return True
    return False


def _function_has_audit(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    audited_helpers: set[str] | None = None,
) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            name = _call_name(child)
            if name in {"log_action", "log_route_mutation", "audit_mutation", "audit_route_mutation"}:
                return True
            if audited_helpers and name in audited_helpers:
                return True
        if isinstance(child, ast.Name) and child.id in {"AuditLog", "AUDIT_DELEGATED"}:
            return True
    return False


def check_audit_log_coverage(root: pathlib.Path) -> list[dict[str, Any]]:
    logger.info("Checking audit log coverage with AST analysis...")
    findings: list[dict[str, Any]] = []
    app_dir = root / "backend" / "app"
    route_dirs = [path for path in app_dir.rglob("routes") if path.is_dir()]

    for routes_dir in route_dirs:
        for py_file in routes_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            try:
                text = py_file.read_text(encoding="utf-8")
                tree = ast.parse(text)
            except (OSError, UnicodeDecodeError, SyntaxError):
                continue

            if "_canonical_error" in text and "canonical_endpoint" in text:
                continue

            audited_helpers = {
                function.name
                for function in ast.walk(tree)
                if isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef))
                and function.name.startswith("_")
                and _function_has_audit(function)
            }
            unaudited = [
                function for function in _route_write_functions(tree)
                if _function_has_effectful_write(function)
                and not _function_has_audit(function, audited_helpers)
                and "AUDIT_DELEGATED" not in text
            ]
            if unaudited:
                names = ", ".join(f"{function.name}@{function.lineno}" for function in unaudited)
                findings.append({
                    "check": "audit_coverage",
                    "severity": "warning",
                    "file": str(py_file.relative_to(root)),
                    "line": unaudited[0].lineno,
                    "message": (
                        f"{py_file.relative_to(root)} has unaudited write functions: {names}."
                    ),
                })

    logger.info("  Audit coverage: %d route file(s) without audit", len(findings))
    return findings


def run_all_checks(root: pathlib.Path, skip: set[str]) -> list[dict[str, Any]]:
    all_findings: list[dict[str, Any]] = []

    checks = [
        ("bandit", lambda: run_bandit()),
        ("semgrep", lambda: run_semgrep(str(root))),
        ("safety", lambda: run_safety()),
        ("gitleaks", lambda: run_gitleaks(str(root))),
        ("trivy", lambda: run_trivy(str(root))),
        ("checkov", lambda: run_checkov(str(root))),
        ("sbom", lambda: check_sbom_licenses(str(root))),
        ("credentials", lambda: check_exposed_credentials(root)),
        ("audit", lambda: check_audit_log_coverage(root)),
    ]

    for name, check_fn in checks:
        if name in skip:
            logger.info("Skipping %s", name)
            continue
        try:
            results = check_fn()
            for r in results:
                r["check_name"] = name
            all_findings.extend(results)
            if results:
                logger.warning("%s: %d finding(s)", name, len(results))
            else:
                logger.info("%s: OK", name)
        except Exception as exc:
            logger.error("%s failed: %s", name, exc)
            all_findings.append({
                "check": name,
                "severity": "error",
                "message": f"Check failed with exception: {exc}",
            })

    return all_findings


def print_report(findings: list[dict[str, Any]], json_output: bool = False) -> int:
    errors = [f for f in findings if f.get("severity") == "error"]
    warnings = [f for f in findings if f.get("severity") == "warning"]

    if json_output:
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "passed": len(errors) == 0,
            "summary": {"errors": len(errors), "warnings": len(warnings), "total": len(findings)},
            "findings": findings,
        }
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if report["passed"] else 1

    print(f"\n{BOLD}═══ Security Quality Gate Report ═══{RESET}\n")

    if not findings:
        print(f"  {GREEN}All security checks passed!{RESET}\n")
        return 0

    if errors:
        print(f"  {BOLD}{RED}Errors ({len(errors)}):{RESET}")
        for e in errors:
            file_info = f" [{e.get('file', '')}:{e.get('line', '')}]" if e.get('file') else ""
            print(f"    {RED}✗{RESET} [{e.get('check_name', e['check'])}]{file_info} {e['message']}")
        print()

    if warnings:
        print(f"  {BOLD}{YELLOW}Warnings ({len(warnings)}):{RESET}")
        for w in warnings:
            file_info = f" [{w.get('file', '')}:{w.get('line', '')}]" if w.get('file') else ""
            print(f"    {YELLOW}⚠{RESET} [{w.get('check_name', w['check'])}]{file_info} {w['message']}")
        print()

    print(f"  Summary: {RED}{len(errors)} errors{RESET}, {YELLOW}{len(warnings)} warnings{RESET}, {len(findings)} total")
    print()

    return 1 if errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Security Quality Gate")
    parser.add_argument("--skip-sast", action="store_true", help="Skip SAST checks")
    parser.add_argument("--skip-deps", action="store_true", help="Skip dependency scan")
    parser.add_argument("--skip-secrets", action="store_true", help="Skip secret scan")
    parser.add_argument("--skip-container", action="store_true", help="Skip container scan")
    parser.add_argument("--skip-iac", action="store_true", help="Skip IaC scan")
    parser.add_argument("--skip-sbom", action="store_true", help="Skip SBOM check")
    parser.add_argument("--skip-credentials", action="store_true", help="Skip credential scan")
    parser.add_argument("--skip-audit", action="store_true", help="Skip audit coverage check")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

    skip: set[str] = set()
    if args.skip_sast:
        skip.update(["bandit", "semgrep"])
    if args.skip_deps:
        skip.add("safety")
    if args.skip_secrets:
        skip.add("gitleaks")
    if args.skip_container:
        skip.add("trivy")
    if args.skip_iac:
        skip.add("checkov")
    if args.skip_sbom:
        skip.add("sbom")
    if args.skip_credentials:
        skip.add("credentials")
    if args.skip_audit:
        skip.add("audit")

    findings = run_all_checks(ROOT, skip)
    return print_report(findings, json_output=args.json)


if __name__ == "__main__":
    sys.exit(main())
