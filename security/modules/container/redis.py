from __future__ import annotations

import logging
import re
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

REDIS_KNOWN_WEAK_PASSWORDS: list[str] = [
    "redis", "password", "admin", "123456", "default",
    "changeme", "pass", "root", "test", "guest",
]

EVICTION_POLICY_RISK: dict[str, str] = {
    "noeviction": "Safe - returns errors on memory limit",
    "allkeys-lru": "Medium - evicts any key, potential data loss",
    "volatile-lru": "Safe - evicts only keys with TTL set",
    "allkeys-random": "Medium - arbitrary eviction",
    "volatile-random": "Safe - evicts only keys with TTL",
    "volatile-ttl": "Safe - evicts keys with shortest TTL",
    "allkeys-lfu": "Medium - evicts least frequently used any key",
    "volatile-lfu": "Safe - evicts LFU keys with TTL only",
}


class RedisConfigIssue(BaseModel):
    parameter: str
    current_value: str
    recommended_value: str
    severity: str
    description: str


class RedisSecurityReport(BaseModel):
    issues: list[RedisConfigIssue] = Field(default_factory=list)
    passed: bool = True
    overall_severity: str = "PASS"


class RedisSecurityManager:
    def __init__(self, config_content: str = "", config_lines: list[str] | None = None):
        self.config_content = config_content
        self.config_lines = config_lines or config_content.split("\n") if config_content else []

    def _get_config_value(self, key: str) -> str | None:
        for line in self.config_lines:
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith(";"):
                continue
            match = re.match(rf"^\s*{re.escape(key)}\s+(.+)$", stripped)
            if match:
                return match.group(1).strip()
        return None

    def validate_config(self, content: str | None = None) -> RedisSecurityReport:
        if content:
            self.config_content = content
            self.config_lines = content.split("\n")

        issues: list[RedisConfigIssue] = []
        passed = True

        requirepass = self._get_config_value("requirepass")
        if not requirepass:
            issues.append(RedisConfigIssue(
                parameter="requirepass",
                current_value="(not set)",
                recommended_value="<strong-random-password>",
                severity="CRITICAL",
                description="No password set for Redis authentication",
            ))
            passed = False
        elif requirepass in REDIS_KNOWN_WEAK_PASSWORDS or len(requirepass) < 16:
            issues.append(RedisConfigIssue(
                parameter="requirepass",
                current_value=requirepass[:4] + "****",
                recommended_value="<password-minimum-16-characters>",
                severity="HIGH",
                description="Weak Redis password - must be at least 16 characters and complex",
            ))
            passed = False

        rename_commands = self._get_config_value("rename-command")
        dangerous_commands = ["FLUSHALL", "FLUSHDB", "CONFIG", "EVAL", "SCRIPT", "SHUTDOWN", "DEBUG", "KEYS"]
        for cmd in dangerous_commands:
            rename = self._get_config_value(f"rename-command {cmd}")
            if rename is None:
                issues.append(RedisConfigIssue(
                    parameter=f"rename-command {cmd}",
                    current_value="(not renamed)",
                    recommended_value="'' or <hard-to-guess-alias>",
                    severity="MEDIUM",
                    description=f"Dangerous command '{cmd}' not renamed or disabled",
                ))
                passed = False

        protected_mode = self._get_config_value("protected-mode")
        if protected_mode and protected_mode.lower() == "no":
            issues.append(RedisConfigIssue(
                parameter="protected-mode",
                current_value="no",
                recommended_value="yes",
                severity="HIGH",
                description="Protected mode is disabled - Redis exposed without protection",
            ))
            passed = False

        bind = self._get_config_value("bind")
        if bind is None or bind.strip() == "0.0.0.0":
            issues.append(RedisConfigIssue(
                parameter="bind",
                current_value=bind or "0.0.0.0 (default)",
                recommended_value="127.0.0.1 or private subnet",
                severity="HIGH",
                description="Redis bound to all interfaces",
            ))
            passed = False

        port = self._get_config_value("port")
        if port and int(port) == 6379 and bind and bind.strip() == "0.0.0.0":
            issues.append(RedisConfigIssue(
                parameter="port",
                current_value=str(port),
                recommended_value="6379 (but bind to internal IP only)",
                severity="MEDIUM",
                description="Redis on default port 6379 exposed on all interfaces",
            ))

        tls_port = self._get_config_value("tls-port")
        tls_cert = self._get_config_value("tls-cert-file")
        tls_key = self._get_config_value("tls-key-file")
        if not tls_port and not tls_cert:
            issues.append(RedisConfigIssue(
                parameter="tls-port / tls-cert-file",
                current_value="(not configured)",
                recommended_value="tls-port 6379 + tls-cert-file / tls-key-file",
                severity="HIGH",
                description="TLS not configured for Redis connections",
            ))
            passed = False

        acl_file = self._get_config_value("aclfile")
        acl_users = self._get_config_value("user")
        if not acl_file and not acl_users:
            issues.append(RedisConfigIssue(
                parameter="aclfile / user",
                current_value="(not configured)",
                recommended_value="aclfile /etc/redis/users.acl",
                severity="MEDIUM",
                description="ACL not configured - using legacy authentication only",
            ))

        aof_enabled = self._get_config_value("appendonly")
        rdb_enabled = self._get_config_value("save")
        if aof_enabled and aof_enabled.lower() == "yes":
            aof_use_rdb_preamble = self._get_config_value("aof-use-rdb-preamble")
            if aof_use_rdb_preamble and aof_use_rdb_preamble.lower() == "yes":
                pass

        eviction_policy = self._get_config_value("maxmemory-policy")
        if eviction_policy and eviction_policy in EVICTION_POLICY_RISK:
            risk = EVICTION_POLICY_RISK[eviction_policy]
            if risk.startswith("Medium"):
                issues.append(RedisConfigIssue(
                    parameter="maxmemory-policy",
                    current_value=eviction_policy,
                    recommended_value="noeviction or volatile-lru",
                    severity="LOW",
                    description=f"Eviction policy '{eviction_policy}': {risk}",
                ))

        maxmemory = self._get_config_value("maxmemory")
        if not maxmemory or maxmemory.strip() == "0":
            issues.append(RedisConfigIssue(
                parameter="maxmemory",
                current_value=str(maxmemory or "not set"),
                recommended_value="<available-memory-80%>",
                severity="MEDIUM",
                description="No memory limit configured - risk of OOM on host",
            ))
            passed = False

        severity = "PASS"
        if issues:
            severities = [i.severity for i in issues]
            if "CRITICAL" in severities:
                severity = "CRITICAL"
            elif "HIGH" in severities:
                severity = "HIGH"
            elif "MEDIUM" in severities:
                severity = "MEDIUM"

        return RedisSecurityReport(issues=issues, passed=passed, overall_severity=severity)

    def validate_acl(self, acl_content: str) -> dict[str, Any]:
        findings: list[str] = []
        passed = True

        for line in acl_content.split("\n"):
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                continue

            if stripped.startswith("user ") and " on " in stripped:
                parts = stripped.split()
                if len(parts) >= 4:
                    username = parts[1]
                    permissions = parts[3:]
                    if ">" in stripped:
                        pwd_match = re.search(r">([^\s]+)", stripped)
                        if pwd_match:
                            pwd = pwd_match.group(1)
                            if pwd in REDIS_KNOWN_WEAK_PASSWORDS or len(pwd) < 16:
                                findings.append(f"User '{username}' has weak password")
                                passed = False
                    if "~*" in stripped:
                        findings.append(f"User '{username}' has access to all keys (~*)")
                        passed = False
                    if "+@all" in stripped:
                        findings.append(f"User '{username}' has all permissions (+@all)")
                        passed = False
                    if "+@dangerous" in stripped:
                        findings.append(f"User '{username}' has dangerous channel access")
                        passed = False

            if "default" in stripped:
                if "off" not in stripped:
                    findings.append("Default user is enabled - consider disabling")
                    passed = False

        return {"findings": findings, "passed": passed}

    def check_tls(self, config_content: str | None = None) -> dict[str, Any]:
        if config_content:
            self.config_lines = config_content.split("\n")

        tls_port = self._get_config_value("tls-port")
        tls_cert = self._get_config_value("tls-cert-file")
        tls_key = self._get_config_value("tls-key-file")
        tls_ca = self._get_config_value("tls-ca-cert-file")
        tls_auth = self._get_config_value("tls-auth-clients")

        findings: list[str] = []
        passed = True

        if not tls_port:
            findings.append("TLS port not configured")
            passed = False

        if not tls_cert:
            findings.append("TLS certificate not configured")
            passed = False

        if not tls_key:
            findings.append("TLS private key not configured")
            passed = False

        if not tls_ca:
            findings.append("TLS CA certificate not configured for client verification")
            passed = False

        if tls_auth and tls_auth.lower() == "no":
            findings.append("TLS client authentication is disabled")
            passed = False

        tls_protocols = self._get_config_value("tls-protocols")
        if tls_protocols:
            if "TLSv1" in tls_protocols and "TLSv1.2" not in tls_protocols:
                findings.append("TLSv1 configured - should use TLSv1.2+")
                passed = False

        return {"findings": findings, "passed": passed}

    def check_network_exposure(self, bind_address: str | None = None, port: int | None = None) -> dict[str, Any]:
        bind = bind_address or self._get_config_value("bind") or "0.0.0.0"
        port_val = port or int(self._get_config_value("port") or "6379")

        findings: list[str] = []
        passed = True

        if bind in ("0.0.0.0", "::", "*"):
            findings.append(f"Redis bound to {bind} - accessible from all network interfaces")
            passed = False
        elif bind == "127.0.0.1":
            pass

        return {"findings": findings, "passed": passed}

    def check_default_credentials(self) -> dict[str, Any]:
        requirepass = self._get_config_value("requirepass")
        findings: list[str] = []
        passed = True

        if requirepass is None:
            findings.append("No authentication configured (requirepass not set)")
            passed = False
        elif requirepass.lower() in REDIS_KNOWN_WEAK_PASSWORDS:
            findings.append(f"Default/weak password detected: '{requirepass}'")
            passed = False

        return {"findings": findings, "passed": passed}

    def validate_persistence_security(self) -> dict[str, Any]:
        findings: list[str] = []
        passed = True

        aof = self._get_config_value("appendonly")
        rdb_save = self._get_config_value("save")

        if aof and aof.lower() == "yes":
            aof_file = self._get_config_value("appendfilename")
            if aof_file and "/" in aof_file:
                dir_path = self._get_config_value("dir") or "/var/lib/redis"
                findings.append(f"AOF file stored in {dir_path} - ensure filesystem encryption")
        elif rdb_save and rdb_save.strip() != "":
            dir_path = self._get_config_value("dir") or "/var/lib/redis"
            findings.append(f"RDB persistence enabled - ensure {dir_path} is encrypted at rest")
            passed = False

        return {"findings": findings, "passed": passed}

    def review_eviction_policy(self) -> dict[str, Any]:
        policy = self._get_config_value("maxmemory-policy") or "noeviction"
        findings: list[str] = []
        passed = True

        risk_info = EVICTION_POLICY_RISK.get(policy, "Unknown - review manually")
        if risk_info.startswith("Medium"):
            findings.append(f"Eviction policy '{policy}': {risk_info}")
            passed = True

        return {"findings": findings, "passed": passed, "policy": policy, "risk": risk_info}

    def full_security_audit(self, config_content: str | None = None) -> RedisSecurityReport:
        return self.validate_config(config_content)
