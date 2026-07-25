from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

AUTH_METHOD_RANKING: Dict[str, int] = {
    "trust": 0,
    "password": 1,
    "md5": 2,
    "scram-sha-256": 3,
    "cert": 4,
    "ldap": 4,
    "gss": 5,
    "sspi": 5,
    "pam": 5,
    "reject": 10,
}

UNTRUSTED_LANGUAGES: Set[str] = {"plpgsql", "sql"}
TRUSTED_LANGUAGES: Set[str] = {"plperl", "pltcl", "plpython3u", "pljava", "plr", "plsh"}


class PgHbaEntry(BaseModel):
    connection_type: str
    database: str
    user: str
    address: Optional[str] = None
    auth_method: str
    auth_options: str = ""


class PostgreSQLConfigFinding(BaseModel):
    finding_type: str
    severity: str
    description: str
    remediation: str
    line_reference: Optional[str] = None


class PostgreSQLSecurityReport(BaseModel):
    findings: List[PostgreSQLConfigFinding] = Field(default_factory=list)
    passed: bool = True
    overall_severity: str = "PASS"


class PostgreSQLSecurityManager:
    def __init__(self, pg_hba_content: str = "", postgresql_conf_content: str = ""):
        self.pg_hba_content = pg_hba_content
        self.postgresql_conf_content = postgresql_conf_content
        self._pg_hba_entries: List[PgHbaEntry] = []

    def _parse_pg_hba(self, content: Optional[str] = None) -> List[PgHbaEntry]:
        if content:
            self.pg_hba_content = content

        entries: List[PgHbaEntry] = []
        for line in self.pg_hba_content.split("\n"):
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                continue

            parts = stripped.split()
            if len(parts) >= 4:
                conn_type = parts[0]
                database = parts[1]
                user = parts[2]
                address = parts[3] if len(parts) > 4 and not parts[3].startswith("/") else None
                auth_idx = 3 if address is None else 4
                auth_method = parts[auth_idx] if auth_idx < len(parts) else "trust"
                auth_options = " ".join(parts[auth_idx + 1:]) if auth_idx + 1 < len(parts) else ""

                entries.append(PgHbaEntry(
                    connection_type=conn_type,
                    database=database,
                    user=user,
                    address=address,
                    auth_method=auth_method,
                    auth_options=auth_options,
                ))

        self._pg_hba_entries = entries
        return entries

    def analyze_pg_hba(self, content: Optional[str] = None) -> Dict[str, Any]:
        entries = self._parse_pg_hba(content)
        findings: List[str] = []
        passed = True

        for entry in entries:
            if entry.auth_method == "trust":
                findings.append(f"TRUST authentication for {entry.user}@{entry.database} from {entry.address or 'local'}")
                passed = False

            if entry.address in ("0.0.0.0/0", "::/0"):
                findings.append(f"Open access from any IP ({entry.address}) for {entry.user}@{entry.database}")
                passed = False

            if entry.auth_method in ("password", "md5"):
                findings.append(f"Weak authentication method '{entry.auth_method}' for {entry.user}@{entry.database}")
                passed = False

        has_scram = any(e.auth_method == "scram-sha-256" for e in entries)
        has_cert = any(e.auth_method == "cert" for e in entries)

        if not has_scram and not has_cert:
            findings.append("No scram-sha-256 or cert authentication found")

        return {"findings": findings, "passed": passed}

    def validate_auth_methods(self, content: Optional[str] = None) -> Dict[str, Any]:
        entries = self._parse_pg_hba(content)
        findings: List[str] = []
        passed = True

        for entry in entries:
            method = entry.auth_method
            if method in ("trust", "password", "md5"):
                findings.append(
                    f"Weak auth '{method}' for {entry.user}@{entry.database} - use scram-sha-256 or cert"
                )
                passed = False

        return {"findings": findings, "passed": passed}

    def check_ssl_tls(self, conf_content: Optional[str] = None) -> Dict[str, Any]:
        content = conf_content or self.postgresql_conf_content
        findings: List[str] = []
        passed = True

        ssl_match = re.search(r"^\s*ssl\s*=\s*(on|off|true|false|1|0)\s*$", content, re.MULTILINE | re.IGNORECASE)
        if ssl_match:
            val = ssl_match.group(1).lower()
            if val in ("off", "false", "0"):
                findings.append("SSL is disabled in postgresql.conf")
                passed = False
        else:
            findings.append("SSL not configured in postgresql.conf")
            passed = False

        for key in ("ssl_cert_file", "ssl_key_file", "ssl_ca_file"):
            match = re.search(rf"^\s*{re.escape(key)}\s*=\s*'([^']+)'", content, re.MULTILINE)
            if not match:
                findings.append(f"'{key}' not configured")

        ssl_ciphers = re.search(r"^\s*ssl_ciphers\s*=\s*'([^']+)'", content, re.MULTILINE)
        if ssl_ciphers:
            ciphers = ssl_ciphers.group(1)
            if "NULL" in ciphers or "EXPORT" in ciphers or "LOW" in ciphers or "MEDIUM" in ciphers:
                findings.append(f"Weak SSL ciphers configured: {ciphers}")
                passed = False

        ssl_min = re.search(r"^\s*ssl_min_protocol_version\s*=\s*'([^']+)'", content, re.MULTILINE)
        if ssl_min:
            if ssl_min.group(1).lower() in ("tlsv1", "tlsv1.1"):
                findings.append(f"Outdated TLS version: {ssl_min.group(1)}")
                passed = False

        return {"findings": findings, "passed": passed}

    def audit_role_permissions(self, roles: Dict[str, List[str]]) -> Dict[str, Any]:
        findings: List[str] = []
        passed = True

        for role_name, privileges in roles.items():
            if "SUPERUSER" in privileges or "superuser" in privileges:
                findings.append(f"Role '{role_name}' has SUPERUSER privileges - should be extremely limited")
                passed = False

            if "CREATEDB" in privileges or "createdb" in privileges:
                findings.append(f"Role '{role_name}' has CREATEDB privilege - review necessity")
                passed = False

            if "CREATEROLE" in privileges or "createrole" in privileges:
                findings.append(f"Role '{role_name}' has CREATEROLE privilege - security risk")
                passed = False

            if "BYPASSRLS" in privileges:
                findings.append(f"Role '{role_name}' bypasses row-level security")
                passed = False

        return {"findings": findings, "passed": passed}

    def validate_row_level_security(self, tables_with_rls: Dict[str, bool]) -> Dict[str, Any]:
        findings: List[str] = []
        passed = True

        sensitive_tables = ["patient", "patient_record", "consent", "audit_log",
                           "users", "user_credentials", "phi_data", "clinical_data"]

        non_rls_sensitive = [t for t, has_rls in tables_with_rls.items()
                            if not has_rls and any(s in t.lower() for s in sensitive_tables)]

        if non_rls_sensitive:
            findings.append(f"Sensitive tables without RLS: {', '.join(non_rls_sensitive)}")
            passed = False

        return {"findings": findings, "passed": passed}

    def check_audit_logging(self, conf_content: Optional[str] = None) -> Dict[str, Any]:
        content = conf_content or self.postgresql_conf_content
        findings: List[str] = []
        passed = True

        shared_preload = re.search(r"^\s*shared_preload_libraries\s*=\s*'([^']*)'", content, re.MULTILINE)
        if shared_preload and "pgaudit" not in shared_preload.group(1).lower():
            findings.append("pgaudit extension not loaded in shared_preload_libraries")
            passed = False
        elif not shared_preload:
            findings.append("shared_preload_libraries not configured")
            passed = False

        log_statement = re.search(r"^\s*log_statement\s*=\s*'([^']+)'", content, re.MULTILINE)
        if log_statement:
            if log_statement.group(1).lower() == "none":
                findings.append("log_statement is 'none' - no statement logging")
                passed = False
        else:
            findings.append("log_statement not configured")

        log_line_prefix = re.search(r"^\s*log_line_prefix\s*=\s*'([^']+)'", content, re.MULTILINE)
        if log_line_prefix:
            if "%m" not in log_line_prefix.group(1):
                findings.append("log_line_prefix missing timestamp")
        else:
            findings.append("log_line_prefix not configured")

        log_connections = re.search(r"^\s*log_connections\s*=\s*(on|off|true|false|1|0)", content, re.MULTILINE | re.IGNORECASE)
        if log_connections and log_connections.group(1).lower() in ("off", "false", "0"):
            findings.append("log_connections is disabled")
            passed = False

        return {"findings": findings, "passed": passed}

    def review_extensions(self, installed_extensions: List[str]) -> Dict[str, Any]:
        findings: List[str] = []
        passed = True

        for ext in installed_extensions:
            if ext.lower() in UNTRUSTED_LANGUAGES:
                continue
            if ext.lower() in TRUSTED_LANGUAGES:
                findings.append(f"Untrusted language extension '{ext}' installed - potential code execution risk")
                passed = False

        dangerous_extensions = ["dblink", "postgres_fdw", "file_fdw", "pg_exec", "adminpack"]
        for ext in installed_extensions:
            if ext.lower() in dangerous_extensions:
                findings.append(f"Dangerous extension '{ext}' installed - remote access or file operations")
                passed = False

        return {"findings": findings, "passed": passed}

    def check_connection_security(self, conf_content: Optional[str] = None) -> Dict[str, Any]:
        content = conf_content or self.postgresql_conf_content
        findings: List[str] = []
        passed = True

        listen_addresses = re.search(r"^\s*listen_addresses\s*=\s*'([^']+)'", content, re.MULTILINE)
        if listen_addresses:
            addr = listen_addresses.group(1)
            if addr in ("*", "0.0.0.0", "::"):
                findings.append(f"PostgreSQL listening on all interfaces ('{addr}')")
                passed = False

        port = re.search(r"^\s*port\s*=\s*(\d+)", content, re.MULTILINE)
        if port and port.group(1) == "5432" and listen_addresses and listen_addresses.group(1) != "localhost":
            findings.append("PostgreSQL on default port - consider changing for security through obscurity")

        max_connections = re.search(r"^\s*max_connections\s*=\s*(\d+)", content, re.MULTILINE)
        if max_connections:
            conn_count = int(max_connections.group(1))
            if conn_count > 500:
                findings.append(f"max_connections is {conn_count} - very high, potential resource exhaustion")
                passed = False

        return {"findings": findings, "passed": passed}

    def enforce_password_policy(self, password: str, username: Optional[str] = None) -> Dict[str, Any]:
        findings: List[str] = []
        passed = True

        if len(password) < 12:
            findings.append(f"Password length ({len(password)}) is less than 12 characters")
            passed = False

        if not re.search(r"[A-Z]", password):
            findings.append("Password missing uppercase letter")
            passed = False

        if not re.search(r"[a-z]", password):
            findings.append("Password missing lowercase letter")
            passed = False

        if not re.search(r"\d", password):
            findings.append("Password missing digit")
            passed = False

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            findings.append("Password missing special character")
            passed = False

        if username and username.lower() in password.lower():
            findings.append("Password contains username")
            passed = False

        common_patterns = ["password", "postgres", "admin", "1234", "qwerty", "letmein"]
        for pattern in common_patterns:
            if pattern in password.lower():
                findings.append(f"Password contains common pattern '{pattern}'")
                passed = False

        return {"findings": findings, "passed": passed}

    def validate_encryption_at_rest(self, data_directory: Optional[str] = None) -> Dict[str, Any]:
        findings: List[str] = []
        passed = True

        if data_directory:
            if data_directory.startswith("/var/lib/postgresql") or data_directory.startswith("/pgdata"):
                findings.append(f"Data directory '{data_directory}' - ensure filesystem-level encryption is enabled")
                passed = False
        else:
            findings.append("Data directory not specified - verify encryption at rest")

        return {"findings": findings, "passed": passed}

    def full_security_audit(self, pg_hba: Optional[str] = None,
                           conf: Optional[str] = None) -> PostgreSQLSecurityReport:
        if pg_hba:
            self.pg_hba_content = pg_hba
        if conf:
            self.postgresql_conf_content = conf

        report_findings: List[PostgreSQLConfigFinding] = []
        passed = True

        hba_result = self.analyze_pg_hba()
        for f in hba_result["findings"]:
            report_findings.append(PostgreSQLConfigFinding(
                finding_type="pg_hba",
                severity="HIGH" if "trust" in f.lower() else "MEDIUM",
                description=f,
                remediation="Use scram-sha-256 authentication and restrict access by IP",
            ))
        if not hba_result["passed"]:
            passed = False

        ssl_result = self.check_ssl_tls()
        for f in ssl_result["findings"]:
            report_findings.append(PostgreSQLConfigFinding(
                finding_type="ssl_tls",
                severity="HIGH",
                description=f,
                remediation="Enable SSL and configure certificates",
            ))
        if not ssl_result["passed"]:
            passed = False

        audit_result = self.check_audit_logging()
        for f in audit_result["findings"]:
            report_findings.append(PostgreSQLConfigFinding(
                finding_type="audit_logging",
                severity="MEDIUM",
                description=f,
                remediation="Configure pgaudit and enable statement logging",
            ))
        if not audit_result["passed"]:
            passed = False

        conn_result = self.check_connection_security()
        for f in conn_result["findings"]:
            report_findings.append(PostgreSQLConfigFinding(
                finding_type="connection",
                severity="HIGH" if "all interfaces" in f.lower() else "MEDIUM",
                description=f,
                remediation="Bind to localhost or private network only",
            ))
        if not conn_result["passed"]:
            passed = False

        severity = "PASS"
        if report_findings:
            severities = [f.severity for f in report_findings]
            if "HIGH" in severities:
                severity = "HIGH"
            elif "MEDIUM" in severities:
                severity = "MEDIUM"

        return PostgreSQLSecurityReport(
            findings=report_findings,
            passed=passed,
            overall_severity=severity,
        )
