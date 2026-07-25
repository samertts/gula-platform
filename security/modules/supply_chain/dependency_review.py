from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from security.modules.supply_chain.models import DependencyVulnerability, SupplyChainPolicy

logger = logging.getLogger(__name__)

TYPO_SQUATTING_PACKAGES: Dict[str, List[str]] = {
    "pytorch": ["pytorche", "pytorch-cpu"],
    "tensorflow": ["tensorflo", "tensor-flow", "tensorlfow"],
    "requests": ["requestz", "reqests", "requests3"],
    "flask": ["flak", "flasky", "flask3", "flask-api"],
    "django": ["djangoo", "django-admin", "djanga"],
    "numpy": ["numpyy", "num-pi", "numpyty"],
    "pandas": ["pandaas", "pandasz", "panda"],
    "scikit-learn": ["sklearn", "scikit", "scikit-learn2"],
    "cryptography": ["cryptographi", "cryptographyy", "cyptography"],
    "boto3": ["boto4", "boto-three", "boto3aws"],
    "fastapi": ["fast-api", "fastapiii", "fastpai"],
    "pydantic": ["pydantic2", "pydantic-v2", "pydanti"],
    "sqlalchemy": ["sql-alchemy", "sqlalchemy2", "sqlalchemy3"],
}

TYPO_SQUATTING_PREFIXES: List[str] = ["python-", "py-", "python3-", "python2-"]
TYPO_SQUATTING_SUFFIXES: List[str] = ["-python", "-py", "-dev", "-library", "-helper"]


class DependencyDiff(BaseModel):
    package: str
    old_version: Optional[str] = None
    new_version: str
    action: str = "added"
    license: Optional[str] = None


class DependencyReviewResult(BaseModel):
    new_dependencies: List[DependencyDiff] = Field(default_factory=list)
    removed_dependencies: List[DependencyDiff] = Field(default_factory=list)
    updated_dependencies: List[DependencyDiff] = Field(default_factory=list)
    license_issues: List[DependencyDiff] = Field(default_factory=list)
    malicious_packages: List[Dict[str, Any]] = Field(default_factory=list)
    freshness_issues: List[str] = Field(default_factory=list)
    lockfile_valid: bool = True
    lockfile_errors: List[str] = Field(default_factory=list)
    scorecard_score: Optional[float] = None
    passed: bool = True


class DependencyReviewer:
    def __init__(self, policy: Optional[SupplyChainPolicy] = None):
        self.policy = policy or SupplyChainPolicy()

    def validate_dependabot_config(self, config_yaml: str) -> Dict[str, Any]:
        findings: List[str] = []
        passed = True

        if "package-ecosystem" not in config_yaml.lower():
            findings.append("No package-ecosystem defined in Dependabot config")
            passed = False

        if "schedule" not in config_yaml.lower() or "interval" not in config_yaml.lower():
            findings.append("Dependabot schedule not configured")
            passed = False

        schedule_match = re.search(r"interval:\s*(\w+)", config_yaml, re.IGNORECASE)
        if schedule_match:
            interval = schedule_match.group(1).lower()
            if interval in ("monthly",):
                findings.append(f"Dependabot schedule is '{interval}' - consider 'weekly' or 'daily' for security updates")
                passed = False

        open_pr_limit = re.search(r"open-pull-requests-limit:\s*(\d+)", config_yaml)
        if not open_pr_limit:
            findings.append("open-pull-requests-limit not set")

        if "allow" not in config_yaml.lower():
            findings.append("No allowed dependency types specified in Dependabot config")
            passed = False

        reviewer_match = re.search(r"reviewers:\s*\[([^\]]*)\]", config_yaml) or re.search(r"reviewed-by:", config_yaml)
        if not reviewer_match:
            findings.append("No reviewers configured for Dependabot PRs")

        return {"findings": findings, "passed": passed}

    def parse_dependabot_alerts(self, alerts_json: str) -> List[DependencyVulnerability]:
        vulnerabilities: List[DependencyVulnerability] = []

        try:
            data = json.loads(alerts_json)
            alerts = data if isinstance(data, list) else data.get("alerts", data.get("data", []))
            for alert in alerts:
                security_advisory = alert.get("security_advisory", alert.get("advisory", {}))
                security_vulnerability = alert.get("security_vulnerability", alert.get("vulnerability", {}))
                vuln_pkg = alert.get("package", security_vulnerability.get("package", {}))

                vulnerabilities.append(DependencyVulnerability(
                    id=alert.get("id", security_advisory.get("ghsa_id", "")),
                    package=vuln_pkg.get("name", ""),
                    version=security_vulnerability.get("vulnerable_version_range", ""),
                    severity=security_advisory.get("severity", "UNKNOWN"),
                    cvss_score=security_advisory.get("cvss", {}).get("score", 0.0),
                    cve_id=security_advisory.get("cve_id", ""),
                    fix_version=security_vulnerability.get("first_patched_version", {}).get("identifier", ""),
                    advisory_url=security_advisory.get("permalink", security_advisory.get("url", "")),
                    published_date=security_advisory.get("published_at", None),
                ))
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse Dependabot alerts: {e}")

        return vulnerabilities

    def review_new_dependencies(self, new_deps: List[DependencyDiff],
                                 existing_deps: List[DependencyDiff]) -> Dict[str, Any]:
        findings: List[str] = []
        license_issues: List[str] = []
        passed = True

        allowed_licenses_upper = [l.upper() for l in self.policy.allowed_licenses]

        for dep in new_deps:
            if dep.package.lower() in [p.lower() for p in self.policy.blocked_packages]:
                findings.append(f"Dependency '{dep.package}' is in blocked packages list")
                passed = False

            if dep.license and dep.license.upper() not in allowed_licenses_upper:
                license_issues.append(f"'{dep.package}' has license '{dep.license}' - not approved")
                passed = False

            if dep.license is None:
                findings.append(f"'{dep.package}' has no license information")

            for allowed_registry in self.policy.allowed_registries:
                if dep.package.startswith("@"):
                    pass

            malicious = self.detect_malicious_package(dep.package, dep.new_version)
            if malicious:
                findings.append(f"Potential malicious package detected: '{dep.package}' - {malicious.get('reason', '')}")
                passed = False

        return {"findings": findings, "license_issues": license_issues, "passed": passed}

    def analyze_transitive_dependencies(self, lockfile: Dict[str, Any]) -> Dict[str, Any]:
        findings: List[str] = []
        passed = True

        if isinstance(lockfile, dict):
            for section in ("packages", "dependencies", "gems", "spec"):
                entries = lockfile.get(section, {})
                if isinstance(entries, dict):
                    for name, info in entries.items() if isinstance(entries, dict) else []:
                        if isinstance(info, dict):
                            version = info.get("version", "")
                            if "devDependencies" in section or "optionalDependencies" in section:
                                pass

        return {"findings": findings, "passed": passed}

    def detect_malicious_package(self, name: str, version: str) -> Optional[Dict[str, Any]]:
        name_lower = name.lower().replace("-", "").replace("_", "")

        for legit_pkg, typos in TYPO_SQUATTING_PACKAGES.items():
            if name_lower in [t.lower() for t in typos]:
                return {
                    "type": "typosquatting",
                    "package": name,
                    "reason": f"Package '{name}' resembles popular package '{legit_pkg}'",
                    "severity": "HIGH",
                }
            if name_lower == legit_pkg.replace("-", "").replace("_", ""):
                if name != legit_pkg:
                    return {
                        "type": "typosquatting",
                        "package": name,
                        "reason": f"Package '{name}' is a typosquat of '{legit_pkg}' (dash/underscore variant)",
                        "severity": "MEDIUM",
                    }

        for prefix in TYPO_SQUATTING_PREFIXES:
            if name_lower.startswith(prefix) and len(name) <= len(prefix) + 5:
                return {
                    "type": "typosquatting",
                    "package": name,
                    "reason": f"Package '{name}' resembles a prefix-squatted package",
                    "severity": "MEDIUM",
                }

        dependency_confusion_keywords = [
            "internal", "private", "corp", "company", "enterprise",
            "gula", "platform", "healthcare", "iraq", "hospital",
        ]
        for keyword in dependency_confusion_keywords:
            if keyword in name_lower and not version.startswith("1.0.0") and version:
                return {
                    "type": "dependency_confusion",
                    "package": name,
                    "reason": f"Package '{name}' contains organizational keyword '{keyword}' - verify it's from internal registry",
                    "severity": "HIGH",
                }

        return None

    def check_version_range_safety(self, specifier: str) -> Dict[str, Any]:
        findings: List[str] = []
        passed = True

        if not specifier or specifier.strip() == "*":
            findings.append("Wildcard version specifier '*' - allows any version")
            passed = False

        if specifier.startswith(">=") and "<" not in specifier and "!=" not in specifier:
            findings.append(f"Unbounded version '{specifier}' - will accept any version above minimum")
            passed = False

        if re.match(r"^[\d.]+$", specifier.strip()):
            pass

        if "||" in specifier:
            parts = [p.strip() for p in specifier.split("||")]
            if any(p == "*" for p in parts):
                findings.append("Compound version specifier includes wildcard")
                passed = False

        return {"findings": findings, "passed": passed, "specifier": specifier}

    def validate_lockfile(self, lockfile_path: str, expected_format: Optional[str] = None) -> Dict[str, Any]:
        errors: List[str] = []
        passed = True

        path = Path(lockfile_path)
        if not path.exists():
            return {"errors": [f"Lockfile not found: {lockfile_path}"], "passed": False}

        content = path.read_text()
        lines = content.split("\n")

        if lockfile_path.endswith("package-lock.json") or lockfile_path.endswith("npm-shrinkwrap.json"):
            try:
                data = json.loads(content)
                for pkg_name, pkg_info in data.get("packages", data.get("dependencies", {})).items():
                    resolved = pkg_info.get("resolved", "")
                    if resolved and not resolved.startswith("https://"):
                        errors.append(f"'{pkg_name}' has non-HTTPS resolved URL: {resolved}")
                        passed = False
                    integrity = pkg_info.get("integrity", "")
                    if integrity and not integrity.startswith("sha"):
                        errors.append(f"'{pkg_name}' has invalid integrity hash format")
                        passed = False
            except json.JSONDecodeError:
                errors.append("Invalid JSON in lockfile")
                passed = False

        elif lockfile_path.endswith("yarn.lock"):
            integrity_pattern = re.compile(r'^\s+integrity\s+(sha\d+-)')
            has_integrity = bool(integrity_pattern.search(content))
            if not has_integrity:
                errors.append("yarn.lock missing integrity hashes")
                passed = False

        elif lockfile_path.endswith("poetry.lock"):
            try:
                for line in lines:
                    if line.strip().startswith("python-versions"):
                        pass
                if "[[package]]" not in content:
                    errors.append("poetry.lock has no package entries")
                    passed = False
            except Exception:
                pass

        elif lockfile_path.endswith("Pipfile.lock"):
            try:
                data = json.loads(content)
                has_hashes = False
                for section in ("default", "develop"):
                    for pkg in data.get(section, {}).values():
                        if isinstance(pkg, dict) and pkg.get("hashes"):
                            has_hashes = True
                            break
                if not has_hashes:
                    errors.append("Pipfile.lock missing hash verification for packages")
                    passed = False
            except json.JSONDecodeError:
                errors.append("Invalid JSON in Pipfile.lock")
                passed = False

        return {"errors": errors, "passed": passed}

    def run_openssf_scorecard(self, repo_url: str) -> Dict[str, Any]:
        logger.info(f"Running OpenSSF Scorecard for {repo_url}")

        result = subprocess.run(
            ["scorecard", "--repo", repo_url, "--format", "json"],
            capture_output=True, text=True, timeout=120
        )

        scorecard_data: Dict[str, Any] = {
            "score": 0.0,
            "category_scores": {},
            "findings": [],
            "error": None,
        }

        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                for check in data.get("checks", []):
                    name = check.get("name", "")
                    score = check.get("score", 0)
                    reason = check.get("reason", "")
                    scorecard_data["category_scores"][name] = score
                    if score < 5:
                        scorecard_data["findings"].append(f"{name}: {score}/10 - {reason}")

                overall = data.get("score", 0)
                scorecard_data["score"] = overall
            except (json.JSONDecodeError, KeyError) as e:
                scorecard_data["error"] = f"Failed to parse Scorecard output: {e}"
        elif "not found" in result.stderr.lower():
            scorecard_data["error"] = "scorecard CLI not installed"
        else:
            scorecard_data["error"] = result.stderr[:500]

        if scorecard_data["error"]:
            scorecard_data["score"] = self._estimate_scorecard_score(repo_url)

        return scorecard_data

    def _estimate_scorecard_score(self, repo_url: str) -> float:
        score = 5.0
        if "github.com" in repo_url:
            score += 1.0
            if re.search(r"security|\.md$", repo_url, re.IGNORECASE):
                score += 0.5
            if "main" in repo_url or "master" in repo_url:
                score += 0.5
        return min(score, 10.0)

    def generate_badge(self, score: float) -> str:
        if score >= 8.0:
            color = "brightgreen"
            label = "A+"
        elif score >= 6.0:
            color = "green"
            label = "A"
        elif score >= 4.0:
            color = "yellowgreen"
            label = "B"
        elif score >= 2.0:
            color = "yellow"
            label = "C"
        else:
            color = "red"
            label = "D"

        return f"![OpenSSF Scorecard](https://img.shields.io/badge/OpenSSF%20Scorecard-{label}-{color})"

    def full_dependency_review(self, new_deps: List[DependencyDiff],
                                existing_deps: List[DependencyDiff],
                                lockfile_path: Optional[str] = None) -> DependencyReviewResult:
        result = DependencyReviewResult()
        result.new_dependencies = new_deps

        review = self.review_new_dependencies(new_deps, existing_deps)
        result.license_issues = [
            d for d in new_deps if d.license and d.license.upper() not in [l.upper() for l in self.policy.allowed_licenses]
        ]
        if not result.license_issues:
            result.license_issues = [
                DependencyDiff(package=f, new_version="", action="license_issue")
                for f in review["license_issues"]
            ]

        for dep in new_deps:
            malicious = self.detect_malicious_package(dep.package, dep.new_version)
            if malicious:
                result.malicious_packages.append(malicious)

        if lockfile_path:
            lockfile_result = self.validate_lockfile(lockfile_path)
            result.lockfile_valid = lockfile_result["passed"]
            result.lockfile_errors = lockfile_result["errors"]

        result.passed = (
            result.lockfile_valid
            and len(result.malicious_packages) == 0
            and len(result.license_issues) == 0
        )

        return result
