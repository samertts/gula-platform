from __future__ import annotations

import io
import logging
import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

DEFAULT_RABBITMQ_CREDENTIALS: List[Dict[str, str]] = [
    {"username": "guest", "password": "guest"},
    {"username": "admin", "password": "admin"},
    {"username": "rabbitmq", "password": "rabbitmq"},
]

WEAK_AUTH_MECHANISMS: List[str] = [
    "PLAIN",
    "AMQPLAIN",
]

STRONG_AUTH_MECHANISMS: List[str] = [
    "EXTERNAL",
    "SCRAM-SHA-256",
    "SCRAM-SHA-512",
]


class RabbitMQUser(BaseModel):
    username: str
    tags: List[str] = Field(default_factory=list)
    vhost_permissions: Dict[str, Dict[str, List[str]]] = Field(default_factory=dict)


class RabbitMQPolicy(BaseModel):
    name: str
    vhost: str
    pattern: str
    definition: Dict[str, Any] = Field(default_factory=dict)
    priority: int = 0


class RabbitMQSecurityFinding(BaseModel):
    finding_type: str
    severity: str
    description: str
    remediation: str


class RabbitMQSecurityReport(BaseModel):
    findings: List[RabbitMQSecurityFinding] = Field(default_factory=list)
    passed: bool = True
    overall_severity: str = "PASS"


class RabbitMQSecurityManager:
    def __init__(self, config_content: str = ""):
        self.config_content = config_content
        self.users: List[RabbitMQUser] = []
        self.policies: List[RabbitMQPolicy] = []
        self.parameters: Dict[str, Any] = {}

    def check_default_credentials(self, users: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        check_users = users or [{"username": "guest", "password": "guest"}]
        findings: List[str] = []
        passed = True

        for user in check_users:
            for default in DEFAULT_RABBITMQ_CREDENTIALS:
                if (user.get("username", "").lower() == default["username"] and
                        user.get("password", "").lower() == default["password"]):
                    findings.append(f"Default credentials found: {default['username']}/{default['password']}")
                    passed = False

        return {"findings": findings, "passed": passed}

    def check_tls(self, config_content: Optional[str] = None) -> Dict[str, Any]:
        content = config_content or self.config_content
        findings: List[str] = []
        passed = True

        if "ssl_options" not in content.lower() and "ssl" not in content.lower():
            findings.append("TLS/SSL not configured for RabbitMQ connections")
            passed = False

        tls_cert = re.search(r"ssl_options\.cacertfile\s*=|cacertfile\s*:", content)
        tls_key = re.search(r"ssl_options\.keyfile\s*=|keyfile\s*:", content)
        tls_cert_file = re.search(r"ssl_options\.certfile\s*=|certfile\s*:", content)

        if not tls_cert and not tls_cert_file:
            findings.append("TLS certificate files not configured")
            passed = False
        if not tls_key:
            findings.append("TLS private key not configured")
            passed = False

        ssl_only = re.search(r"ssl_only\s*[:=]\s*true", content, re.IGNORECASE)
        listener = re.search(r"listeners\.ssl\s*\.", content)
        if not ssl_only and not listener:
            findings.append("Non-SSL listener still enabled alongside SSL")

        if "verify" in content.lower() or "verify_peer" in content.lower():
            pass
        else:
            findings.append("TLS peer verification not configured")

        return {"findings": findings, "passed": passed}

    def validate_vhost_isolation(self, users: Optional[List[RabbitMQUser]] = None,
                                  vhosts: Optional[List[str]] = None) -> Dict[str, Any]:
        user_list = users or self.users
        vhost_list = vhosts or []

        findings: List[str] = []
        passed = True

        if not vhost_list:
            findings.append("No virtual hosts defined - all services share default vhost")
            passed = False

        for user in user_list:
            configured_vhosts = set(user.vhost_permissions.keys())
            if configured_vhosts and len(configured_vhosts) > 1:
                for vhost in configured_vhosts:
                    other_vhosts = configured_vhosts - {vhost}
                    if other_vhosts:
                        findings.append(
                            f"User '{user.username}' has access to multiple vhosts ({', '.join(configured_vhosts)}) - "
                            "violates isolation principle"
                        )
                        passed = False
                        break

        return {"findings": findings, "passed": passed}

    def audit_user_permissions(self, users: Optional[List[RabbitMQUser]] = None) -> Dict[str, Any]:
        user_list = users or self.users
        findings: List[str] = []
        passed = True

        for user in user_list:
            if "administrator" in user.tags:
                findings.append(f"User '{user.username}' has administrator tag - limit admin users")
                passed = False

            for vhost, permissions in user.vhost_permissions.items():
                read = permissions.get("read", [])
                write = permissions.get("write", [])
                configure = permissions.get("configure", [])

                if ".*" in configure and ".*" in write and ".*" in read:
                    findings.append(
                        f"User '{user.username}' has full access (configure/read/write .*) to vhost '{vhost}'"
                    )
                    passed = False

        return {"findings": findings, "passed": passed}

    def review_policies(self, policies: Optional[List[RabbitMQPolicy]] = None) -> Dict[str, Any]:
        policy_list = policies or self.policies
        findings: List[str] = []
        passed = True

        for policy in policy_list:
            if policy.definition.get("ha-mode") == "all":
                findings.append(
                    f"Policy '{policy.name}' on vhost '{policy.vhost}' mirrors to all nodes "
                    "- consider 'exactly' with N-1 nodes"
                )

            if "ttl" in policy.definition:
                ttl = policy.definition["ttl"]
                if ttl == 0:
                    findings.append(
                        f"Policy '{policy.name}' has TTL=0 - messages expire immediately"
                    )
                    passed = False

            if "dead-letter-exchange" not in policy.definition:
                findings.append(
                    f"Policy '{policy.name}' has no dead letter exchange configured"
                )

        return {"findings": findings, "passed": passed}

    def validate_auth_mechanism(self, mechanisms: Optional[List[str]] = None) -> Dict[str, Any]:
        auth_mechs = mechanisms or ["PLAIN", "AMQPLAIN"]
        findings: List[str] = []
        passed = True

        for mech in auth_mechs:
            if mech in WEAK_AUTH_MECHANISMS:
                findings.append(f"Weak authentication mechanism enabled: '{mech}' - transmits credentials in cleartext")
                passed = False

        has_strong = any(m in STRONG_AUTH_MECHANISMS for m in auth_mechs)
        if not has_strong:
            findings.append("No strong authentication mechanism (SCRAM, EXTERNAL) configured")
            passed = False

        return {"findings": findings, "passed": passed}

    def check_shovel_federation(self, config_content: Optional[str] = None) -> Dict[str, Any]:
        content = config_content or self.config_content
        findings: List[str] = []
        passed = True

        if "rabbitmq_shovel" in content or "shovel" in content.lower():
            findings.append("Shovel plugin configured - ensure cross-cluster connections use TLS")
            shovel_pattern = re.compile(r"(\w+://[^@\s]+@[^\s]+)", re.IGNORECASE)
            for match in shovel_pattern.finditer(content):
                uri = match.group(1)
                if "amqp://" in uri.lower() and "amqps://" not in uri.lower():
                    findings.append(f"Shovel URI {uri[:50]}... does not use AMQPS (TLS)")
                    passed = False

        if "rabbitmq_federation" in content or "federation" in content.lower():
            findings.append("Federation plugin configured - review upstream trust")
            fed_pattern = re.compile(r"upstream\s*[:=]\s*(\S+)")
            for match in fed_pattern.finditer(content):
                findings.append(f"Federation upstream configured: {match.group(1)}")

        return {"findings": findings, "passed": passed}

    def full_security_audit(self, config_content: Optional[str] = None,
                            users: Optional[List[RabbitMQUser]] = None) -> RabbitMQSecurityReport:
        if config_content:
            self.config_content = config_content

        report_findings: List[RabbitMQSecurityFinding] = []
        passed = True

        default_creds = self.check_default_credentials(
            [{"username": u.username, "password": "password"} for u in (users or [])] if users else None
        )
        for f in default_creds["findings"]:
            report_findings.append(RabbitMQSecurityFinding(
                finding_type="default_credentials",
                severity="CRITICAL",
                description=f,
                remediation="Change default credentials immediately",
            ))
        if not default_creds["passed"]:
            passed = False

        tls = self.check_tls()
        for f in tls["findings"]:
            report_findings.append(RabbitMQSecurityFinding(
                finding_type="tls",
                severity="HIGH",
                description=f,
                remediation="Configure TLS for all RabbitMQ connections",
            ))
        if not tls["passed"]:
            passed = False

        isolation = self.validate_vhost_isolation(users)
        for f in isolation["findings"]:
            report_findings.append(RabbitMQSecurityFinding(
                finding_type="vhost_isolation",
                severity="MEDIUM",
                description=f,
                remediation="Ensure each user only accesses required vhosts",
            ))
        if not isolation["passed"]:
            passed = False

        permissions = self.audit_user_permissions(users)
        for f in permissions["findings"]:
            report_findings.append(RabbitMQSecurityFinding(
                finding_type="permissions",
                severity="HIGH",
                description=f,
                remediation="Apply least privilege principle to user permissions",
            ))
        if not permissions["passed"]:
            passed = False

        policies = self.review_policies()
        for f in policies["findings"]:
            report_findings.append(RabbitMQSecurityFinding(
                finding_type="policy",
                severity="LOW",
                description=f,
                remediation="Review and update policy configuration",
            ))

        auth = self.validate_auth_mechanism()
        for f in auth["findings"]:
            report_findings.append(RabbitMQSecurityFinding(
                finding_type="auth_mechanism",
                severity="HIGH",
                description=f,
                remediation="Disable PLAIN/AMQPLAIN and use SCRAM or EXTERNAL",
            ))
        if not auth["passed"]:
            passed = False

        shovel = self.check_shovel_federation()
        for f in shovel["findings"]:
            report_findings.append(RabbitMQSecurityFinding(
                finding_type="shovel_federation",
                severity="MEDIUM",
                description=f,
                remediation="Ensure TLS for all cross-cluster connections",
            ))

        severity = "PASS"
        if report_findings:
            severities = [f.severity for f in report_findings]
            if "CRITICAL" in severities:
                severity = "CRITICAL"
            elif "HIGH" in severities:
                severity = "HIGH"
            elif "MEDIUM" in severities:
                severity = "MEDIUM"

        return RabbitMQSecurityReport(
            findings=report_findings,
            passed=passed,
            overall_severity=severity,
        )
