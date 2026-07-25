from __future__ import annotations

import logging
import re
from typing import Any

from pydantic import BaseModel

from security.modules.container.models import DockerSecurityConfig

logger = logging.getLogger(__name__)

DOCKERFILE_BEST_PRACTICES: dict[str, dict[str, Any]] = {
    "no_root_user": {"rule": "DL3002", "description": "Do not use root as the last USER in Dockerfile", "severity": "HIGH"},
    "pin_base_image": {"rule": "DL3006", "description": "Always tag base image with a specific version", "severity": "MEDIUM"},
    "apt_get_cleanup": {"rule": "DL3009", "description": "Delete apt-get lists after install to reduce image size", "severity": "LOW"},
    "no_latest_tag": {"rule": "DL3007", "description": "Do not use the :latest tag", "severity": "MEDIUM"},
    "copy_not_add": {"rule": "DL3010", "description": "Use COPY over ADD when not extracting archives", "severity": "LOW"},
    "no_sudo": {"rule": "DL3011", "description": "Do not use sudo", "severity": "HIGH"},
    "no_apt_get_upgrade": {"rule": "DL3015", "description": "Avoid apt-get upgrade in Dockerfile", "severity": "LOW"},
    "no_cd_back": {"rule": "DL3003", "description": "Use WORKDIR instead of cd", "severity": "LOW"},
    "expose_right_port": {"rule": "DL3018", "description": "Pin package versions in apk add", "severity": "MEDIUM"},
    "no_curl_pipe_bash": {"rule": "DL4006", "description": "Do not pipe curl output to bash", "severity": "HIGH"},
    "no_add_ssh_keys": {"rule": "DL4005", "description": "Do not add SSH keys in Dockerfile", "severity": "HIGH"},
}


class DockerfileFinding(BaseModel):
    rule_id: str
    line_number: int
    severity: str
    description: str
    remediation: str


class ImageVulnerability(BaseModel):
    cve_id: str
    package: str
    installed_version: str
    fixed_version: str | None = None
    severity: str
    cvss_score: float = 0.0


class DockerSecurityManager:
    def __init__(self, config: DockerSecurityConfig | None = None):
        self.config = config or DockerSecurityConfig()
        self._cve_cache: dict[str, list[ImageVulnerability]] = {}

    def analyze_dockerfile(self, dockerfile_content: str) -> list[DockerfileFinding]:
        findings: list[DockerfileFinding] = []
        lines = dockerfile_content.split("\n")

        last_user_root = True
        uses_add = False
        has_healthcheck = False
        has_multi_stage = False
        has_explicit_tag = True
        uses_latest = False
        has_apt_get_cleanup = False
        has_sudo = False
        has_apt_get_upgrade = False
        uses_curl_pipe = False
        has_pinned_apk = True

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            upper = stripped.upper()

            if upper.startswith("USER") and not stripped.endswith("root"):
                last_user_root = False
            if stripped.upper().startswith("ADD "):
                uses_add = True
                if re.search(r"https?://", stripped, re.IGNORECASE):
                    findings.append(DockerfileFinding(
                        rule_id="DL3010",
                        line_number=i,
                        severity="MEDIUM",
                        description="Use COPY over ADD for remote URLs",
                        remediation="Replace ADD with curl/wget + COPY",
                    ))
            if stripped.upper().startswith("HEALTHCHECK"):
                has_healthcheck = True
            if "AS " in stripped.upper() and stripped.upper().startswith("FROM"):
                has_multi_stage = True
            if "FROM " in stripped.upper():
                if ":" not in stripped:
                    has_explicit_tag = False
                elif ":latest" in stripped.lower():
                    uses_latest = True
            if "apt-get" in stripped.lower() and "clean" in stripped.lower():
                has_apt_get_cleanup = True
            if stripped.lower().startswith("run ") and ("sudo" in stripped.lower()):
                has_sudo = True
            if "apt-get" in stripped.lower() and "upgrade" in stripped.lower():
                has_apt_get_upgrade = True
            if re.search(r"curl\s+.*\|\s*(ba|sh)", stripped, re.IGNORECASE):
                uses_curl_pipe = True
            if stripped.upper().startswith("RUN ") and ("apk add" in stripped.lower()) and "-" not in stripped:
                has_pinned_apk = False

        if last_user_root:
            findings.append(DockerfileFinding(
                rule_id="DL3002",
                line_number=0,
                severity="HIGH",
                description="Dockerfile does not switch to non-root user",
                remediation="Add 'USER <non-root>' at the end of Dockerfile",
            ))
        if not has_explicit_tag:
            findings.append(DockerfileFinding(
                rule_id="DL3006",
                line_number=0,
                severity="MEDIUM",
                description="Base image tag not pinned to specific version",
                remediation="Use specific version tags like 'python:3.12-slim' instead of 'python'",
            ))
        if uses_latest:
            findings.append(DockerfileFinding(
                rule_id="DL3007",
                line_number=0,
                severity="MEDIUM",
                description="Using the :latest tag can lead to unpredictable builds",
                remediation="Pin to a specific version tag",
            ))
        if uses_add:
            findings.append(DockerfileFinding(
                rule_id="DL3010",
                line_number=0,
                severity="LOW",
                description="Use COPY instead of ADD when not extracting archives",
                remediation="Use COPY for local file copies",
            ))
        if not has_apt_get_cleanup:
            findings.append(DockerfileFinding(
                rule_id="DL3009",
                line_number=0,
                severity="LOW",
                description="apt-get lists not deleted after install",
                remediation="Add '&& rm -rf /var/lib/apt/lists/*' to RUN apt-get commands",
            ))
        if has_sudo:
            findings.append(DockerfileFinding(
                rule_id="DL3011",
                line_number=0,
                severity="HIGH",
                description="sudo command used in Dockerfile",
                remediation="Run as root directly instead of using sudo",
            ))
        if has_apt_get_upgrade:
            findings.append(DockerfileFinding(
                rule_id="DL3015",
                line_number=0,
                severity="LOW",
                description="apt-get upgrade in Dockerfile is unnecessary",
                remediation="Remove apt-get upgrade, use specific package versions",
            ))
        if uses_curl_pipe:
            findings.append(DockerfileFinding(
                rule_id="DL4006",
                line_number=0,
                severity="HIGH",
                description="Piping curl output to bash is unsafe",
                remediation="Download script, verify checksum, then execute",
            ))
        if not has_pinned_apk:
            findings.append(DockerfileFinding(
                rule_id="DL3018",
                line_number=0,
                severity="MEDIUM",
                description="Package versions not pinned in apk add",
                remediation="Pin package versions like 'apk add python3=3.12.0'",
            ))
        if not has_healthcheck:
            findings.append(DockerfileFinding(
                rule_id="DL4000",
                line_number=0,
                severity="MEDIUM",
                description="No HEALTHCHECK instruction found",
                remediation="Add HEALTHCHECK instruction for container health monitoring",
            ))
        if not has_multi_stage:
            findings.append(DockerfileFinding(
                rule_id="DL3020",
                line_number=0,
                severity="LOW",
                description="No multi-stage build used",
                remediation="Consider multi-stage builds to reduce final image size",
            ))

        return findings

    def detect_privilege_escalation(self, run_args: list[str]) -> list[str]:
        issues: list[str] = []
        privileged_keywords = ["--privileged", "CAP_SYS_ADMIN", "CAP_DAC_OVERRIDE",
                              "SYS_ADMIN", "DAC_OVERRIDE", "--cap-add=ALL"]

        for arg in run_args:
            for keyword in privileged_keywords:
                if keyword.lower() in arg.lower():
                    issues.append(f"Privilege escalation risk: '{keyword}' found in run arguments")

        if self.config.no_new_privileges is False:
            issues.append("Container running with no-new-privileges disabled")

        if self.config.security_opt_list:
            for opt in self.config.security_opt_list:
                if "seccomp=unconfined" in opt:
                    issues.append("Seccomp is disabled - all syscalls allowed")

        return issues

    def audit_capabilities(self, current_caps: list[str], required_caps: list[str] | None = None) -> dict[str, Any]:
        dangerous_caps = {
            "SYS_ADMIN": "Mount, namespace, and kernel operations",
            "SYS_RAWIO": "Raw I/O port access",
            "SYS_PTRACE": "Process inspection and tracing",
            "SYS_BOOT": "Reboot the system",
            "SYS_MODULE": "Insert/remove kernel modules",
            "KILL": "Send signals to any process",
            "NET_ADMIN": "Network administration",
            "NET_RAW": "Raw sockets",
            "DAC_OVERRIDE": "Bypass file permission checks",
            "DAC_READ_SEARCH": "Bypass file read/search checks",
            "SYSLOG": "View kernel syslog",
            "ALL": "All capabilities",
        }

        required = required_caps or ["CHOWN", "SETGID", "SETUID", "NET_BIND_SERVICE"]
        findings: list[str] = []
        excess_caps: list[str] = []

        for cap in current_caps:
            cap_name = cap.upper().removeprefix("CAP_") if cap.upper().startswith("CAP_") else cap.upper()
            if cap_name in dangerous_caps and cap_name not in required:
                excess_caps.append(cap_name)
                findings.append(f"Dangerous capability '{cap_name}' granted: {dangerous_caps[cap_name]}")

        missing_required = [c for c in required if c.upper() not in [x.upper().removeprefix("CAP_") for x in current_caps]]

        return {
            "findings": findings,
            "excess_capabilities": excess_caps,
            "missing_required": missing_required,
            "passed": len(findings) == 0 and len(missing_required) == 0,
        }

    def validate_user_namespace(self) -> dict[str, Any]:
        findings: list[str] = []
        passed = True

        if self.config.user_namespace == "host":
            findings.append("User namespace remapping is disabled (host mode)")
            passed = False

        return {"findings": findings, "passed": passed, "current_mode": self.config.user_namespace}

    def enforce_read_only_filesystem(self) -> dict[str, Any]:
        findings: list[str] = []
        passed = True

        if not self.config.security_opt_list:
            findings.append("No security options configured to enforce read-only filesystem")

        return {"findings": findings, "passed": passed}

    def validate_resource_limits(self, limits: dict[str, Any] | None = None) -> dict[str, Any]:
        limits = limits or self.config.resource_limits if hasattr(self.config, "resource_limits") else {}
        findings: list[str] = []
        passed = True

        cpu = limits.get("cpu", limits.get("nano_cpus", "unlimited"))
        memory = limits.get("memory", limits.get("mem_limit", "unlimited"))

        if memory == "unlimited" or (isinstance(memory, str) and memory.upper() in ("0", "-1", "UNLIMITED")):
            findings.append("Memory limit is not set - risk of DoS on host")
            passed = False

        if cpu == "unlimited" or cpu == 0:
            findings.append("CPU limit is not set")
            passed = False

        nofile = limits.get("nofile", {})
        if isinstance(nofile, dict):
            soft = nofile.get("soft", 0)
            hard = nofile.get("hard", 0)
            if soft > 1048576 or hard > 1048576:
                findings.append(f"nofile ulimit is unusually high: soft={soft}, hard={hard}")
                passed = False

        pids = self.config.ulimits.get("nproc", {})
        if isinstance(pids, dict) and pids.get("hard", 0) > 1000:
            findings.append(f"nproc ulimit is unusually high: {pids.get('hard')}")
            passed = False

        return {"findings": findings, "passed": passed, "limits": limits}

    def validate_healthcheck(self, dockerfile_content: str) -> dict[str, Any]:
        has_healthcheck = bool(re.search(r"^\s*HEALTHCHECK\s", dockerfile_content, re.MULTILINE))
        findings: list[str] = []
        passed = has_healthcheck

        if not has_healthcheck:
            findings.append("Missing HEALTHCHECK instruction in Dockerfile")

        return {"findings": findings, "passed": passed}

    def validate_non_root_user(self, dockerfile_content: str) -> dict[str, Any]:
        lines = dockerfile_content.split("\n")
        last_user_is_root = True

        for line in lines:
            stripped = line.strip()
            if stripped.upper().startswith("USER "):
                user = stripped.split(None, 1)[1].strip()
                if user.lower() != "root" and user != "0":
                    last_user_is_root = False

        findings: list[str] = []
        passed = not last_user_is_root

        if last_user_is_root:
            findings.append("Container will run as root - switch to non-root user")

        return {"findings": findings, "passed": passed}

    def validate_multi_stage_build(self, dockerfile_content: str) -> dict[str, Any]:
        lines = dockerfile_content.split("\n")
        stage_count = 0
        has_build_stage = False
        has_final_stage = False

        for line in lines:
            if line.strip().upper().startswith("FROM "):
                stage_count += 1
                if " AS " in line.upper() or " as " in line:
                    if "builder" in line.lower() or "build" in line.lower():
                        has_build_stage = True
                    has_final_stage = True

        findings: list[str] = []
        passed = stage_count >= 2 and has_build_stage and has_final_stage

        if stage_count < 2:
            findings.append("Single-stage build detected - multi-stage builds reduce attack surface")

        return {"findings": findings, "passed": passed, "stage_count": stage_count}

    def scan_secrets(self, content: str) -> list[dict[str, Any]]:
        import re as _re
        secrets: list[dict[str, Any]] = []

        patterns = {
            "aws_access_key": r"(?i)(AKIA[0-9A-Z]{16})",
            "aws_secret_key": r"(?i)((?=.*[a-z])(?=.*[0-9])[A-Za-z0-9+/]{40})",
            "private_key": r"-----BEGIN\s?(RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
            "password": r"(?i)(password|passwd|pwd)\s*[=:]\s*['\"](?!\$|%|env)[^'\"]+['\"]",
            "api_key": r"(?i)(api[_-]?key|apikey|api_token)\s*[=:]\s*['\"][^'\"]+['\"]",
            "secret": r"(?i)(secret|token|auth)\s*[=:]\s*['\"](?!\$|\{)[^'\"]+['\"]",
            "connection_string": r"(?i)(mongodb|mysql|postgresql|redis|amqp)://[^@]+@",
            "jwt_token": r"eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*",
            "github_token": r"(?i)ghp_[A-Za-z0-9]{36}",
            "slack_token": r"(?i)xox[baprs]-[0-9]{12}-[0-9]{12}-[0-9]{12}-[a-z0-9]{32}",
        }

        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            for pattern_name, pattern in patterns.items():
                matches = _re.findall(pattern, line)
                if matches:
                    for match in matches:
                        secret_value = match if isinstance(match, str) else match[0]
                        if len(secret_value) > 6:
                            masked = secret_value[:4] + "****" + secret_value[-4:]
                            secrets.append({
                                "line": i,
                                "type": pattern_name,
                                "match": masked,
                                "severity": "HIGH",
                            })

        return secrets

    def scan_dockerfile_secrets(self, dockerfile_content: str) -> dict[str, Any]:
        secrets = self.scan_secrets(dockerfile_content)

        findings: list[str] = []
        passed = len(secrets) == 0

        if secrets:
            for s in secrets:
                findings.append(f"Line {s['line']}: potential {s['type']} detected ({s['match']})")

        return {"findings": findings, "passed": passed, "secrets_found": len(secrets)}

    def analyze_compose_security(self, compose_content: str) -> dict[str, Any]:
        findings: list[str] = []
        passed = True
        secrets = self.scan_secrets(compose_content)

        for s in secrets:
            findings.append(f"Potential secret exposed in compose file ({s['type']} at line {s['line']})")
            passed = False

        if "build:" in compose_content.lower() and "image:" not in compose_content.lower():
            findings.append("Compose service uses build without image reference")
            passed = False

        return {"findings": findings, "passed": passed, "secrets_found": len(secrets)}

    def lookup_cve(self, package: str, version: str) -> list[ImageVulnerability]:
        if package in self._cve_cache:
            return self._cve_cache[package]

        logger.info(f"CVE lookup for {package}@{version} - using embedded CVE database abstraction")
        known_vulnerabilities: dict[str, list[dict[str, Any]]] = {
            "openssl": [
                {"cve": "CVE-2024-5535", "fixed": "3.0.14", "severity": "HIGH", "score": 7.5},
                {"cve": "CVE-2024-4741", "fixed": "3.0.13", "severity": "HIGH", "score": 7.4},
            ],
            "libssl3": [
                {"cve": "CVE-2024-5535", "fixed": "3.0.14", "severity": "HIGH", "score": 7.5},
            ],
            "log4j": [
                {"cve": "CVE-2021-44228", "fixed": "2.17.0", "severity": "CRITICAL", "score": 10.0},
                {"cve": "CVE-2021-45046", "fixed": "2.17.0", "severity": "CRITICAL", "score": 9.0},
            ],
            "node": [
                {"cve": "CVE-2024-27980", "fixed": "22.0.0", "severity": "HIGH", "score": 8.1},
            ],
            "python": [
                {"cve": "CVE-2024-0450", "fixed": "3.12.3", "severity": "HIGH", "score": 7.5},
            ],
        }

        vulns: list[ImageVulnerability] = []
        if package.lower() in known_vulnerabilities:
            for v in known_vulnerabilities[package.lower()]:
                fixed = v["fixed"]
                if self._is_version_affected(version, fixed):
                    vulns.append(ImageVulnerability(
                        cve_id=v["cve"],
                        package=package,
                        installed_version=version,
                        fixed_version=fixed,
                        severity=v["severity"],
                        cvss_score=v["score"],
                    ))

        self._cve_cache[package] = vulns
        return vulns

    @staticmethod
    def _is_version_affected(installed: str, fixed: str) -> bool:
        def parse_ver(v: str) -> tuple[int, ...]:
            parts = v.replace("~", "-").replace("+", ".").replace("-", ".").split(".")
            result: list[int] = []
            for p in parts:
                try:
                    result.append(int(p))
                except ValueError:
                    result.append(0)
            return tuple(result)

        if not installed or not fixed:
            return True
        try:
            return parse_ver(installed) < parse_ver(fixed)
        except Exception:
            logger.warning(f"Could not compare versions: {installed} vs {fixed}")
            return False

    def check_security_opt(self, opt_list: list[str] | None = None) -> dict[str, Any]:
        opts = opt_list or self.config.security_opt_list
        findings: list[str] = []
        passed = True

        if "no-new-privileges" not in opts:
            findings.append("no-new-privileges security option is not set")
            passed = False

        apparmor = [o for o in opts if "apparmor" in o]
        if not apparmor:
            findings.append("AppArmor profile not set")
            passed = False

        seccomp = [o for o in opts if "seccomp" in o]
        if seccomp and "unconfined" in seccomp[0]:
            findings.append("Seccomp is set to 'unconfined' - all syscalls allowed")
            passed = False

        return {"findings": findings, "passed": passed}
