from __future__ import annotations

import logging
import re
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

INSECURE_TLS_VERSIONS: set[str] = {"TLSv1", "TLSv1.1"}
SECURE_TLS_VERSIONS: set[str] = {"TLSv1.2", "TLSv1.3"}

WEAK_CIPHERS: set[str] = {
    "RC4", "DES", "3DES", "MD5", "EXPORT", "LOW", "MEDIUM",
    "NULL", "aNULL", "eNULL", "ADH", "AECDH", "PSK", "SRP",
}

SECURE_CIPHERS: str = "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384"


class NginxConfigFinding(BaseModel):
    finding_type: str
    severity: str
    description: str
    remediation: str
    line_number: int | None = None


class NginxSecurityReport(BaseModel):
    findings: list[NginxConfigFinding] = Field(default_factory=list)
    passed: bool = True
    overall_severity: str = "PASS"


class NginxSecurityManager:
    def __init__(self, config_content: str = ""):
        self.config_content = config_content

    def _strip_nginx_comments(self, content: str) -> str:
        return re.sub(r"#.*$", "", content, flags=re.MULTILINE)

    def _check_directive(self, content: str, directive: str, expected_value: str | None = None,
                        allow_absent: bool = False) -> tuple[bool, str | None]:
        pattern = rf"^\s*{re.escape(directive)}\s+(.+?);"
        match = re.search(pattern, content, re.MULTILINE)
        if not match:
            return (allow_absent, None)
        value = match.group(1).strip()
        if expected_value is not None:
            return (value.lower() == expected_value.lower(), value)
        return (True, value)

    def check_server_tokens(self, content: str | None = None) -> dict[str, Any]:
        c = self._strip_nginx_comments(content or self.config_content)
        findings: list[str] = []
        passed = True

        present, value = self._check_directive(c, "server_tokens")
        if not present:
            findings.append("server_tokens not configured - nginx version will be revealed in headers")
            passed = False
        elif value != "off":
            findings.append(f"server_tokens is '{value}' - should be 'off'")
            passed = False

        return {"findings": findings, "passed": passed}

    def validate_tls_config(self, content: str | None = None) -> dict[str, Any]:
        c = self._strip_nginx_comments(content or self.config_content)
        findings: list[str] = []
        passed = True

        present, value = self._check_directive(c, "ssl_protocols")
        if not present:
            findings.append("ssl_protocols not configured")
            passed = False
        else:
            protocols = set(value.upper().split())
            insecure = protocols & INSECURE_TLS_VERSIONS
            if insecure:
                findings.append(f"Insecure TLS protocols enabled: {', '.join(sorted(insecure))}")
                passed = False

        present, value = self._check_directive(c, "ssl_ciphers")
        if not present:
            findings.append("ssl_ciphers not configured")
            passed = False
        else:
            ciphers_upper = value.upper()
            for weak in WEAK_CIPHERS:
                if weak in ciphers_upper:
                    findings.append(f"Weak cipher '{weak}' included in ssl_ciphers")
                    passed = False

        present, value = self._check_directive(c, "ssl_prefer_server_ciphers")
        if not present:
            findings.append("ssl_prefer_server_ciphers not configured - should be 'on'")
            passed = False

        present, value = self._check_directive(c, "ssl_session_cache")
        if not present:
            findings.append("ssl_session_cache not configured")
            passed = False

        present, value = self._check_directive(c, "ssl_session_timeout")
        if not present:
            findings.append("ssl_session_timeout not configured")
            passed = False

        ssl_cert = re.search(r"ssl_certificate\s+", c)
        ssl_key = re.search(r"ssl_certificate_key\s+", c)
        if not ssl_cert:
            findings.append("ssl_certificate not configured")
            passed = False
        if not ssl_key:
            findings.append("ssl_certificate_key not configured")
            passed = False

        return {"findings": findings, "passed": passed}

    def check_hsts(self, content: str | None = None) -> dict[str, Any]:
        c = self._strip_nginx_comments(content or self.config_content)
        findings: list[str] = []
        passed = True

        present, value = self._check_directive(c, "add_header Strict-Transport-Security")
        if not present:
            findings.append("HSTS (Strict-Transport-Security) header not configured")
            passed = False
        elif "max-age" in (value or "").lower():
            age_match = re.search(r"max-age=(\d+)", value or "")
            if age_match:
                age = int(age_match.group(1))
                if age < 15552000:
                    findings.append(f"HSTS max-age is {age}s - minimum 15552000s (180 days) recommended")
                    passed = False
            if "includeSubDomains" not in (value or ""):
                findings.append("HSTS missing includeSubDomains flag")
                passed = False
            if "preload" not in (value or ""):
                findings.append("HSTS missing preload directive")

        return {"findings": findings, "passed": passed}

    def check_request_size_limit(self, content: str | None = None) -> dict[str, Any]:
        c = self._strip_nginx_comments(content or self.config_content)
        findings: list[str] = []
        passed = True

        present, value = self._check_directive(c, "client_max_body_size")
        if not present:
            findings.append("client_max_body_size not configured")
            passed = False
        else:
            size_match = re.match(r"(\d+)([kKmM]?)", value or "")
            if size_match:
                size = int(size_match.group(1))
                unit = size_match.group(2).lower()
                if unit == "m":
                    if size > 100:
                        findings.append(f"client_max_body_size is {size}M - very large, potential DoS vector")
                        passed = False
                elif unit == "k":
                    pass
                else:
                    if size > 10485760:
                        findings.append(f"client_max_body_size is very large ({size})")
                        passed = False
            else:
                findings.append(f"Could not parse client_max_body_size: {value}")

        return {"findings": findings, "passed": passed}

    def check_rate_limiting(self, content: str | None = None) -> dict[str, Any]:
        c = self._strip_nginx_comments(content or self.config_content)
        findings: list[str] = []
        passed = True

        limit_req_zone = re.search(r"limit_req_zone\s", c)
        limit_conn_zone = re.search(r"limit_conn_zone\s", c)

        if not limit_req_zone and not limit_conn_zone:
            findings.append("No rate limiting configured (limit_req_zone or limit_conn_zone)")
            passed = False

        limit_req = re.search(r"limit_req\s+zone=", c)
        if limit_req_zone and not limit_req:
            findings.append("limit_req_zone defined but not used in any location block")
            passed = False

        limit_conn = re.search(r"limit_conn\s+\w+", c)
        if limit_conn_zone and not limit_conn:
            findings.append("limit_conn_zone defined but not used")

        return {"findings": findings, "passed": passed}

    def validate_access_control(self, content: str | None = None) -> dict[str, Any]:
        c = self._strip_nginx_comments(content or self.config_content)
        findings: list[str] = []
        passed = True

        has_allow = re.search(r"^\s*allow\s", c, re.MULTILINE)
        has_deny = re.search(r"^\s*deny\s", c, re.MULTILINE)
        has_deny_all = re.search(r"^\s*deny\s+all", c, re.MULTILINE)

        if not has_allow and not has_deny:
            findings.append("No access control directives (allow/deny) found")
            passed = False
        elif has_allow and not has_deny_all:
            locations_with_allow = set(re.findall(r"(location\s+\S+)", c))
            locations_with_deny_all = set(re.findall(r"(location\s+\S+).*?deny all", c, re.DOTALL))
            if locations_with_allow - locations_with_deny_all:
                findings.append("Some location blocks with allow rules missing 'deny all' fallback")

        sensitive_locations = ["/admin", "/config", "/api/admin", "/.env", "/.git", "/backup", "/debug"]
        for loc in sensitive_locations:
            escaped = re.escape(loc)
            location_pattern = re.search(rf"location\s+{escaped}\s*{{", c)
            if location_pattern:
                block_start = location_pattern.end()
                block_content = c[block_start:]
                brace_count = 1
                i = 0
                while i < len(block_content) and brace_count > 0:
                    if block_content[i] == "{":
                        brace_count += 1
                    elif block_content[i] == "}":
                        brace_count -= 1
                    i += 1
                location_body = block_content[:i - 1]
                if "deny all" not in location_body and "internal" not in location_body:
                    findings.append(f"Sensitive location '{loc}' is not protected by deny all or internal directive")

        auth_basic = re.search(r"auth_basic\s+", c)
        auth_request = re.search(r"auth_request\s+", c)
        jwt_auth = re.search(r"auth_jwt\s+", c)

        if not any([auth_basic, auth_request, jwt_auth]):
            findings.append("No authentication directives found (auth_basic, auth_request, or auth_jwt)")

        return {"findings": findings, "passed": passed}

    def check_upstream_security(self, content: str | None = None) -> dict[str, Any]:
        c = self._strip_nginx_comments(content or self.config_content)
        findings: list[str] = []
        passed = True

        upstream_blocks = re.findall(r"upstream\s+(\S+)\s*{([^}]*)}", c)
        for name, body in upstream_blocks:
            server_matches = re.findall(r"server\s+(\S+)", body)
            for server in server_matches:
                if ":" in server:
                    host, port = server.rsplit(":", 1)
                    port = port.strip(";")
                    try:
                        if int(port) < 1024:
                            pass
                    except ValueError:
                        pass
            if "internal" not in body.lower():
                findings.append(f"Upstream '{name}' not marked as 'internal' - may be externally accessible")
                passed = False

        proxy_pass = re.findall(r"proxy_pass\s+(\S+);", c)
        for proxy in proxy_pass:
            if proxy.startswith("http://"):
                if "localhost" not in proxy and "127.0.0.1" not in proxy:
                    findings.append(f"proxy_pass to '{proxy}' over HTTP (not HTTPS)")
                    passed = False
            elif proxy.startswith("https://"):
                present, val = self._check_directive(c, "proxy_ssl_verify")
                if not present or val != "on":
                    findings.append(f"proxy_ssl_verify not enabled for proxy_pass '{proxy}'")
                    passed = False

        return {"findings": findings, "passed": passed}

    def check_logging(self, content: str | None = None) -> dict[str, Any]:
        c = self._strip_nginx_comments(content or self.config_content)
        findings: list[str] = []
        passed = True

        access_log = re.search(r"access_log\s+", c)
        error_log = re.search(r"error_log\s+", c)

        if not access_log:
            findings.append("access_log not configured")
            passed = False

        if not error_log:
            findings.append("error_log not configured")
            passed = False

        log_format = re.search(r"log_format\s+\S+\s+", c)
        if not log_format:
            findings.append("No custom log_format defined - consider adding security-relevant fields")

        return {"findings": findings, "passed": passed}

    def check_http2_security(self, content: str | None = None) -> dict[str, Any]:
        c = content or self.config_content
        findings: list[str] = []
        passed = True

        http2_present = "http2" in c.lower()
        if http2_present:
            ssl_present = "ssl" in c.lower() or "ssl_certificate" in c
            if not ssl_present:
                findings.append("HTTP/2 configured without SSL - HTTP/2 over cleartext (h2c) is risky")
                passed = False
        else:
            findings.append("HTTP/2 not configured - enable for performance and security benefits")

        return {"findings": findings, "passed": passed}

    def validate_client_cert(self, content: str | None = None) -> dict[str, Any]:
        c = content or self.config_content
        findings: list[str] = []
        passed = True

        client_cert = re.search(r"ssl_client_certificate\s+", c)
        client_verify = re.search(r"ssl_verify_client\s+(on|optional)", c)

        if not client_cert:
            findings.append("ssl_client_certificate not configured")
            passed = False

        if not client_verify:
            findings.append("ssl_verify_client not configured - client certificates not required")
            passed = False

        return {"findings": findings, "passed": passed}

    def check_additional_security_headers(self, content: str | None = None) -> dict[str, Any]:
        c = self._strip_nginx_comments(content or self.config_content)
        findings: list[str] = []
        passed = True

        security_headers = {
            "X-Frame-Options": "SAMEORIGIN",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(self), microphone=()",
            "Content-Security-Policy": "default-src 'self'",
        }

        for header, expected in security_headers.items():
            present, value = self._check_directive(c, f"add_header {header}")
            if not present:
                findings.append(f"Security header '{header}' not configured")
                passed = False

        return {"findings": findings, "passed": passed}

    def full_security_audit(self, config_content: str | None = None) -> NginxSecurityReport:
        if config_content:
            self.config_content = config_content

        report_findings: list[NginxConfigFinding] = []
        passed = True

        checks = [
            ("server_tokens", self.check_server_tokens()),
            ("tls_config", self.validate_tls_config()),
            ("hsts", self.check_hsts()),
            ("request_size_limit", self.check_request_size_limit()),
            ("rate_limiting", self.check_rate_limiting()),
            ("access_control", self.validate_access_control()),
            ("upstream_security", self.check_upstream_security()),
            ("logging", self.check_logging()),
            ("http2", self.check_http2_security()),
            ("security_headers", self.check_additional_security_headers()),
        ]

        severity_map = {
            "server_tokens": "MEDIUM",
            "tls_config": "HIGH",
            "hsts": "MEDIUM",
            "request_size_limit": "MEDIUM",
            "rate_limiting": "MEDIUM",
            "access_control": "HIGH",
            "upstream_security": "HIGH",
            "logging": "LOW",
            "http2": "LOW",
            "security_headers": "MEDIUM",
        }

        for check_name, result in checks:
            if not result["passed"]:
                passed = False
                for f in result["findings"]:
                    report_findings.append(NginxConfigFinding(
                        finding_type=check_name,
                        severity=severity_map.get(check_name, "MEDIUM"),
                        description=f,
                        remediation=self._suggest_remediation(check_name),
                    ))

        severity = "PASS"
        if report_findings:
            severities = [f.severity for f in report_findings]
            if "HIGH" in severities:
                severity = "HIGH"
            elif "MEDIUM" in severities:
                severity = "MEDIUM"

        return NginxSecurityReport(
            findings=report_findings,
            passed=passed,
            overall_severity=severity,
        )

    @staticmethod
    def _suggest_remediation(check_name: str) -> str:
        remediations = {
            "server_tokens": "Set 'server_tokens off;' in http block",
            "tls_config": "Configure ssl_protocols TLSv1.2 TLSv1.3; with strong ciphers",
            "hsts": "Add 'add_header Strict-Transport-Security \"max-age=63072000; includeSubDomains; preload\";'",
            "request_size_limit": "Set 'client_max_body_size 10m;' or appropriate limit",
            "rate_limiting": "Configure limit_req_zone and limit_req directives",
            "access_control": "Add allow/deny directives and authentication to location blocks",
            "upstream_security": "Use HTTPS for all proxy_pass directives and enable proxy_ssl_verify",
            "logging": "Configure access_log and error_log with appropriate format",
            "http2": "Enable HTTP/2 with SSL: listen 443 ssl http2;",
            "security_headers": "Add all security headers via add_header directives",
        }
        return remediations.get(check_name, "Review configuration against security best practices")
