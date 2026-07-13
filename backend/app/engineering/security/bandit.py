from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SecurityIssue:
    file: str
    line: int
    severity: str
    confidence: str
    cwe: str
    message: str


class BanditScanner:
    def __init__(self, project_root: Path | str):
        self.project_root = Path(project_root)

    def scan(self, path: str = ".") -> list[SecurityIssue]:
        try:
            result = subprocess.run(
                ["python", "-m", "bandit", "-r", "-ll", "-ii", "-f", "json", path],
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
                timeout=120,
            )
            return self._parse_result(result.stdout)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return []

    def _parse_result(self, json_output: str) -> list[SecurityIssue]:
        import json
        try:
            data = json.loads(json_output)
            issues = []
            for result in data.get("results", []):
                issues.append(
                    SecurityIssue(
                        file=result.get("filename", ""),
                        line=result.get("line_number", 0),
                        severity=result.get("issue_severity", ""),
                        confidence=result.get("issue_confidence", ""),
                        cwe=result.get("cwe", ""),
                        message=result.get("issue_text", ""),
                    )
                )
            return issues
        except (json.JSONDecodeError, KeyError):
            return []


class SemgrepScanner:
    def __init__(self, project_root: Path | str):
        self.project_root = Path(project_root)

    def scan(self, path: str = ".") -> list[SecurityIssue]:
        try:
            result = subprocess.run(
                ["semgrep", "--json", "--quiet", path],
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
                timeout=120,
            )
            return self._parse_result(result.stdout)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return []

    def _parse_result(self, json_output: str) -> list[SecurityIssue]:
        import json
        try:
            data = json.loads(json_output)
            issues = []
            for result in data.get("results", []):
                issues.append(
                    SecurityIssue(
                        file=result.get("path", ""),
                        line=result.get("start", {}).get("line", 0),
                        severity=result.get("extra", {}).get("severity", "WARNING"),
                        confidence="HIGH",
                        cwe=result.get("extra", {}).get("metadata", {}).get("cwe", ""),
                        message=result.get("extra", {}).get("message", ""),
                    )
                )
            return issues
        except (json.JSONDecodeError, KeyError):
            return []


class SecretsScanner:
    def __init__(self, project_root: Path | str):
        self.project_root = Path(project_root)

    def scan(self, path: str = ".") -> list[SecurityIssue]:
        issues = []
        patterns = [
            "SECRET_KEY",
            "ENCRYPTION_KEY",
            "NID_HMAC_KEY",
            "REFRESH_TOKEN_SECRET",
            "DEVICE_HMAC_KEY",
            "-----BEGIN RSA PRIVATE KEY-----",
            "-----BEGIN OPENSSH PRIVATE KEY-----",
            "ghp_",
            "gho_",
            "ghu_",
            "xoxb-",
            "xoxp-",
            "sk-",
        ]
        for py_file in self.project_root.rglob("*.py"):
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            content = py_file.read_text()
            for i, line in enumerate(content.split("\n"), 1):
                for pattern in patterns:
                    if pattern in line:
                        issues.append(
                            SecurityIssue(
                                file=str(py_file.relative_to(self.project_root)),
                                line=i,
                                severity="HIGH",
                                confidence="MEDIUM",
                                cwe="CWE-312",
                                message=f"Possible secret exposure: '{pattern}' found in source",
                            )
                        )
        return issues
