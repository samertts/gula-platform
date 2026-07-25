from __future__ import annotations

import logging
import re
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

SENSITIVE_ENV_PATTERNS: list[str] = [
    r"(?i)(password|passwd|pwd|secret|token|api_key|apikey|auth|credential)",
    r"(?i)(AWS_ACCESS_KEY|AWS_SECRET_KEY|AWS_SESSION_TOKEN)",
    r"(?i)(DATABASE_URL|DB_URL|REDIS_URL|RABBITMQ_URL|AMQP_URL)",
    r"(?i)(PRIVATE_KEY|CERTIFICATE|CA_BUNDLE)",
    r"(?i)(JWT_SECRET|SESSION_SECRET|ENCRYPTION_KEY)",
    r"(?i)(MFA_SECRET|OTP_SECRET|TOTP_SECRET)",
    r"(?i)(SENTRY_DSN|DD_API_KEY|NEW_RELIC_LICENSE_KEY)",
    r"(?i)(GITHUB_TOKEN|GITLAB_TOKEN|SLACK_TOKEN)",
    r"(?i)(SERVICE_ACCOUNT|SA_KEY|CLIENT_SECRET)",
]


class ComposeServiceFinding(BaseModel):
    service_name: str
    findings: list[str] = Field(default_factory=list)
    severity: str = "MEDIUM"


class ComposeSecurityReport(BaseModel):
    file_path: str
    service_findings: list[ComposeServiceFinding] = Field(default_factory=list)
    global_findings: list[str] = Field(default_factory=list)
    passed: bool = True
    overall_severity: str = "PASS"


class ComposeSecurityManager:
    def __init__(self, compose_content: str = ""):
        self.compose_content = compose_content
        self._parsed: dict[str, Any] | None = None

    def parse_compose(self, content: str | None = None) -> dict[str, Any]:
        if content:
            self.compose_content = content

        if not self.compose_content.strip():
            return {}

        parsed: dict[str, Any] = {}
        current_section: str | None = None
        current_service: str | None = None
        in_services = False
        in_networks = False
        in_volumes = False

        lines = self.compose_content.split("\n")
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("//"):
                continue

            if stripped == "services:" or stripped.startswith("services:"):
                in_services = True
                in_networks = False
                in_volumes = False
                continue
            if stripped == "networks:" or stripped.startswith("networks:"):
                in_services = False
                in_networks = True
                in_volumes = False
                continue
            if stripped == "volumes:" or stripped.startswith("volumes:"):
                in_services = False
                in_networks = False
                in_volumes = True
                continue

            if in_services and stripped and not stripped.startswith(" ") and not stripped.startswith("\t"):
                service_name = stripped.rstrip(":").strip()
                if ":" not in stripped:
                    current_service = service_name
                    if "services" not in parsed:
                        parsed["services"] = {}
                    parsed["services"][current_service] = {}
                    continue

            if in_services and current_service and ":" in stripped:
                key, _, value = stripped.partition(":")
                key = key.strip()
                value = value.strip()
                if current_service and "services" in parsed and current_service in parsed["services"]:
                    if key == "image":
                        parsed["services"][current_service]["image"] = value
                    elif key == "build":
                        parsed["services"][current_service]["build"] = value
                    elif key == "ports":
                        if "ports" not in parsed["services"][current_service]:
                            parsed["services"][current_service]["ports"] = []
                        parsed["services"][current_service]["ports"].append(value)
                    elif key == "environment":
                        parsed["services"][current_service]["environment"] = value
                    elif key in ("networks", "network_mode"):
                        if "networks" not in parsed["services"][current_service]:
                            parsed["services"][current_service]["networks"] = []
                        parsed["services"][current_service]["networks"].append(value)
                    elif key == "volumes":
                        if "volumes" not in parsed["services"][current_service]:
                            parsed["services"][current_service]["volumes"] = []
                        parsed["services"][current_service]["volumes"].append(value)
                    elif key == "restart":
                        parsed["services"][current_service]["restart"] = value
                    elif key == "healthcheck":
                        parsed["services"][current_service]["healthcheck"] = True
                    elif key == "privileged":
                        parsed["services"][current_service]["privileged"] = value.lower() == "true"
                    elif key == "user":
                        parsed["services"][current_service]["user"] = value
                    elif key == "cap_add":
                        if "cap_add" not in parsed["services"][current_service]:
                            parsed["services"][current_service]["cap_add"] = []
                        parsed["services"][current_service]["cap_add"].append(value)
                    elif key == "cap_drop":
                        if "cap_drop" not in parsed["services"][current_service]:
                            parsed["services"][current_service]["cap_drop"] = []
                        parsed["services"][current_service]["cap_drop"].append(value)

                if stripped.startswith("- ") and current_service:
                    item = stripped.removeprefix("- ").strip()
                    if ":" in item:
                        env_key, _, env_val = item.partition(":")
                        if "environment" not in parsed["services"].get(current_service, {}):
                            parsed["services"][current_service]["environment"] = env_key.strip()
                    elif "=" in item:
                        if "environment_list" not in parsed["services"].get(current_service, {}):
                            parsed["services"][current_service]["environment_list"] = []
                        parsed["services"][current_service]["environment_list"].append(item)

        return parsed

    def audit_network_isolation(self, parsed: dict[str, Any] | None = None) -> dict[str, Any]:
        if parsed is None:
            parsed = self.parse_compose()

        findings: list[str] = []
        passed = True
        services = parsed.get("services", {})

        for svc_name, svc_config in services.items():
            if not isinstance(svc_config, dict):
                continue
            network_mode = svc_config.get("network_mode", "")
            if network_mode == "host":
                findings.append(f"Service '{svc_name}' uses host network mode - no network isolation")
                passed = False
            networks = svc_config.get("networks", [])
            if isinstance(networks, list) and len(networks) == 0:
                if not network_mode:
                    findings.append(f"Service '{svc_name}' is not attached to any defined network")
                    passed = False

        global_networks = parsed.get("networks", {})
        if not global_networks:
            findings.append("No custom networks defined - services use default network")
            passed = False

        return {"findings": findings, "passed": passed}

    def validate_volume_mounts(self, parsed: dict[str, Any] | None = None) -> dict[str, Any]:
        if parsed is None:
            parsed = self.parse_compose()

        findings: list[str] = []
        passed = True
        services = parsed.get("services", {})

        for svc_name, svc_config in services.items():
            if not isinstance(svc_config, dict):
                continue
            volumes = svc_config.get("volumes", [])
            if not isinstance(volumes, list):
                continue
            for vol in volumes:
                vol_str = str(vol)
                if vol_str.startswith("/") or vol_str.startswith("./") or vol_str.startswith("../"):
                    parts = vol_str.split(":")
                    if len(parts) >= 2:
                        host_path = parts[0]
                        if host_path in ("/", "/etc", "/usr", "/bin", "/sbin", "/lib", "/proc", "/sys", "/dev"):
                            findings.append(f"Service '{svc_name}' mounts critical host path '{host_path}'")
                            passed = False
                        if host_path.startswith("/var/run/docker.sock"):
                            findings.append(f"Service '{svc_name}' mounts docker socket - privilege escalation risk")
                            passed = False
                if ":ro" not in vol_str.lower() and "bind" not in vol_str.lower():
                    findings.append(f"Service '{svc_name}' volume '{vol}' not mounted read-only")
                    passed = False

        return {"findings": findings, "passed": passed}

    def detect_secrets_in_env(self, parsed: dict[str, Any] | None = None) -> dict[str, Any]:
        if parsed is None:
            parsed = self.parse_compose()

        findings: list[str] = []
        passed = True
        services = parsed.get("services", {})

        for svc_name, svc_config in services.items():
            if not isinstance(svc_config, dict):
                continue
            env_direct = svc_config.get("environment", "")
            env_file = svc_config.get("env_file", [])
            env_list = svc_config.get("environment_list", [])

            for env_entry in [env_direct] + env_list:
                if isinstance(env_entry, str):
                    for pattern in SENSITIVE_ENV_PATTERNS:
                        if re.search(pattern, env_entry):
                            val_match = re.search(r"(password|secret|token|key)\s*[:=]\s*(?:\"?)([^\s\"']+)", env_entry, re.IGNORECASE)
                            if val_match and not val_match.group(2).startswith("${"):
                                findings.append(
                                    f"Service '{svc_name}': hardcoded {val_match.group(1)} in environment"
                                )
                                passed = False

        if not findings:
            for svc_name, svc_config in services.items():
                if isinstance(svc_config, dict) and "env_file" in svc_config:
                    findings.append(f"Service '{svc_name}' uses env_file - ensure file is in .gitignore")

        return {"findings": findings, "passed": passed}

    def analyze_port_exposure(self, parsed: dict[str, Any] | None = None) -> dict[str, Any]:
        if parsed is None:
            parsed = self.parse_compose()

        findings: list[str] = []
        passed = True
        services = parsed.get("services", {})

        for svc_name, svc_config in services.items():
            if not isinstance(svc_config, dict):
                continue
            ports = svc_config.get("ports", [])
            if not isinstance(ports, list):
                continue
            for port_mapping in ports:
                port_str = str(port_mapping)
                if ":" in port_str:
                    host_port = port_str.split(":")[0]
                    if host_port in ("0.0.0.0", "0.0.0.0:") or port_str.startswith("0.0.0.0:"):
                        findings.append(f"Service '{svc_name}' port {port_str} is exposed on 0.0.0.0 - all interfaces")
                        passed = False
                elif port_str.replace(" ", "").startswith('"'):
                    findings.append(f"Service '{svc_name}' exposes port {port_str} on all interfaces")

        return {"findings": findings, "passed": passed}

    def validate_dependency_versions(self, parsed: dict[str, Any] | None = None) -> dict[str, Any]:
        if parsed is None:
            parsed = self.parse_compose()

        findings: list[str] = []
        passed = True
        services = parsed.get("services", {})

        for svc_name, svc_config in services.items():
            if not isinstance(svc_config, dict):
                continue
            image = svc_config.get("image", "")
            if image and ":" in image:
                tag = image.split(":")[1]
                if tag in ("latest", "dev", "develop", "master", "main", "unstable", "nightly"):
                    findings.append(f"Service '{svc_name}' uses unstable image tag '{tag}' - pin to specific version")
                    passed = False
            elif image:
                findings.append(f"Service '{svc_name}' image '{image}' has no tag - :latest implied")

        return {"findings": findings, "passed": passed}

    def validate_healthcheck(self, parsed: dict[str, Any] | None = None) -> dict[str, Any]:
        if parsed is None:
            parsed = self.parse_compose()

        findings: list[str] = []
        passed = True
        services = parsed.get("services", {})

        for svc_name, svc_config in services.items():
            if not isinstance(svc_config, dict):
                continue
            if svc_name in ("redis", "postgres", "rabbitmq", "nginx", "traefik", "haproxy") or svc_name.endswith("-db"):
                continue
            if "healthcheck" not in svc_config:
                findings.append(f"Service '{svc_name}' has no healthcheck configured")
                passed = False

        return {"findings": findings, "passed": passed}

    def validate_restart_policy(self, parsed: dict[str, Any] | None = None) -> dict[str, Any]:
        if parsed is None:
            parsed = self.parse_compose()

        findings: list[str] = []
        passed = True
        services = parsed.get("services", {})

        for svc_name, svc_config in services.items():
            if not isinstance(svc_config, dict):
                continue
            restart = svc_config.get("restart", "")
            if restart == "always":
                findings.append(f"Service '{svc_name}' uses restart: always in production - use 'unless-stopped' or 'on-failure'")
                passed = False
            if not restart:
                findings.append(f"Service '{svc_name}' has no restart policy - use 'unless-stopped'")

        return {"findings": findings, "passed": passed}

    def full_audit(self, content: str | None = None) -> ComposeSecurityReport:
        parsed = self.parse_compose(content)
        all_findings: list[ComposeServiceFinding] = []
        global_findings: list[str] = []
        overall_passed = True
        severities: list[str] = []

        network = self.audit_network_isolation(parsed)
        volumes = self.validate_volume_mounts(parsed)
        secrets = self.detect_secrets_in_env(parsed)
        ports = self.analyze_port_exposure(parsed)
        deps = self.validate_dependency_versions(parsed)
        health = self.validate_healthcheck(parsed)
        restart = self.validate_restart_policy(parsed)

        for check_name, result in [
            ("network_isolation", network),
            ("volume_mounts", volumes),
            ("secrets", secrets),
            ("port_exposure", ports),
            ("dependency_versions", deps),
            ("healthcheck", health),
            ("restart_policy", restart),
        ]:
            if not result["passed"]:
                overall_passed = False
                for f in result["findings"]:
                    global_findings.append(f"[{check_name}] {f}")
                severities.append("MEDIUM")

        for svc_name in parsed.get("services", {}):
            svc_findings: list[str] = []
            svc_config = parsed["services"][svc_name]

            if svc_config.get("privileged"):
                svc_findings.append("Container runs in privileged mode")
                overall_passed = False

            if not svc_config.get("user"):
                svc_findings.append("No user specified - runs as root")

            cap_add = svc_config.get("cap_add", [])
            if isinstance(cap_add, list) and "ALL" in cap_add:
                svc_findings.append("ALL capabilities added - maximum privilege")
                overall_passed = False

            if svc_findings:
                all_findings.append(ComposeServiceFinding(
                    service_name=svc_name,
                    findings=svc_findings,
                    severity="HIGH" if svc_config.get("privileged") else "MEDIUM",
                ))

        overall_severity = "PASS"
        if overall_passed is False:
            overall_severity = "HIGH" if any("privileged" in str(f) for f in global_findings) else "MEDIUM"

        return ComposeSecurityReport(
            file_path="docker-compose.yml",
            service_findings=all_findings,
            global_findings=global_findings,
            passed=overall_passed,
            overall_severity=overall_severity,
        )

    def suggest_remediation(self, finding: str) -> str:
        remediation_map: dict[str, str] = {
            "host network": "Add 'network_mode: bridge' and define custom networks",
            "docker.sock": "Remove docker socket mount or use docker-in-docker pattern",
            "privileged": "Remove 'privileged: true' and add only required capabilities",
            "root": "Add 'user: <non-root-user>' to service definition",
            "healthcheck": "Add healthcheck configuration",
            "restart: always": "Change to 'restart: unless-stopped'",
            "ALL capabilities": "Replace with specific capabilities list",
            "0.0.0.0": "Bind to specific IP or use internal networks only",
            "hardcoded": "Use environment variables from .env file or secrets manager",
            "read-only": "Add ':ro' suffix to volume mount",
            "unstable tag": "Pin to specific version tag",
            "no tag": "Add version tag to image reference",
            "no network": "Attach service to a custom defined network",
        }

        for key, remediation in remediation_map.items():
            if key in finding.lower():
                return remediation

        return "Review configuration against security best practices"

    def generate_security_report(self, content: str | None = None) -> str:
        report = self.full_audit(content)
        lines: list[str] = [
            "=" * 60,
            "Docker Compose Security Audit Report",
            "=" * 60,
            f"File: {report.file_path}",
            f"Overall Status: {'PASS' if report.passed else 'FAIL'}",
            f"Severity: {report.overall_severity}",
            "",
        ]

        if report.global_findings:
            lines.append("Global Findings:")
            for f in report.global_findings:
                lines.append(f"  - {f}")

        if report.service_findings:
            lines.append("\nService Findings:")
            for sf in report.service_findings:
                lines.append(f"\n  [{sf.severity}] {sf.service_name}:")
                for f in sf.findings:
                    remediation = self.suggest_remediation(f)
                    lines.append(f"    - {f}")
                    lines.append(f"      Remediation: {remediation}")

        if report.passed:
            lines.append("\nNo security issues found.")
        else:
            lines.append("\nRemediation required before production deployment.")

        return "\n".join(lines)
