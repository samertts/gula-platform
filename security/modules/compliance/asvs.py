from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from security.modules.compliance.models import (
    ComplianceControl,
    ComplianceFramework,
    ComplianceReport,
    ControlStatus,
)

logger = logging.getLogger(__name__)

ASVS_CHAPTERS: dict[str, dict[str, Any]] = {
    "V1": {
        "name": "Architecture, Design and Threat Modeling",
        "controls": {
            "1.1.1": {"description": "Verify the use of a secure software development lifecycle", "category": "Architecture"},
            "1.1.2": {"description": "Verify the use of threat modeling for every design change", "category": "Threat Modeling"},
            "1.2.1": {"description": "Verify all components are documented and have assigned owners", "category": "Component Documentation"},
            "1.2.2": {"description": "Verify all communication is encrypted", "category": "Communications"},
            "1.3.1": {"description": "Verify all application components are defined in terms of business function", "category": "Business Architecture"},
            "1.4.1": {"description": "Verify the use of a consistent and secure data classification scheme", "category": "Data Classification"},
            "1.5.1": {"description": "Verify all security controls have a centralized implementation", "category": "Security Controls"},
            "1.6.1": {"description": "Verify the application uses a single, well-known, vetted TLS implementation", "category": "TLS"},
            "1.7.1": {"description": "Verify secure coding checklist is used", "category": "Secure Coding"},
            "1.8.1": {"description": "Verify all application components are upgradable", "category": "Component Management"},
            "1.9.1": {"description": "Verify the application is designed to fail securely", "category": "Error Handling"},
            "1.10.1": {"description": "Verify the application has defined security requirements", "category": "Security Requirements"},
            "1.11.1": {"description": "Verify a software supply chain security policy is in place", "category": "Supply Chain"},
            "1.12.1": {"description": "Verify all external services are documented", "category": "External Services"},
            "1.14.1": {"description": "Verify the application segregates components logically and physically", "category": "Segregation"},
            "1.15.1": {"description": "Verify the application implements a secure configuration management system", "category": "Configuration"},
        },
    },
    "V2": {
        "name": "Authentication Verification",
        "controls": {
            "2.1.1": {"description": "Verify all authentication credentials use strong hashing", "category": "Password Security"},
            "2.1.2": {"description": "Verify password minimum length is 12 characters", "category": "Password Security"},
            "2.1.3": {"description": "Verify no password composition rules are in place limiting character types", "category": "Password Security"},
            "2.1.4": {"description": "Verify passwords are not used as PIN codes or one-time passwords", "category": "Password Security"},
            "2.2.1": {"description": "Verify anti-automation controls are in place", "category": "Anti-automation"},
            "2.2.2": {"description": "Verify the application uses multi-factor authentication", "category": "MFA"},
            "2.2.3": {"description": "Verify MFA is enforced for all privileged accounts", "category": "MFA"},
            "2.3.1": {"description": "Verify credential storage uses approved cryptographic functions", "category": "Credential Storage"},
            "2.3.2": {"description": "Verify credentials are salted using unique per-user salts", "category": "Credential Storage"},
            "2.4.1": {"description": "Verify password managers can provide credentials", "category": "Credential Management"},
            "2.4.2": {"description": "Verify DNS lookups of authentication services are secure", "category": "Authentication Service"},
            "2.5.1": {"description": "Verify the application allows users to change their password", "category": "Password Change"},
            "2.5.2": {"description": "Verify the application allows users to initiate a password reset", "category": "Password Reset"},
            "2.5.3": {"description": "Verify the weakest link in the reset process is at least as strong as the password", "category": "Password Reset"},
            "2.5.4": {"description": "Verify credential recovery does not reveal the current password", "category": "Credential Recovery"},
            "2.6.1": {"description": "Verify that evidence of user enumeration is prevented", "category": "User Enumeration"},
            "2.7.1": {"description": "Verify the application maintains a risk-based authentication system", "category": "Risk-based Auth"},
            "2.8.1": {"description": "Verify the application implements step-up authentication", "category": "Step-up Auth"},
        },
    },
    "V3": {
        "name": "Session Management Verification",
        "controls": {
            "3.1.1": {"description": "Verify the application never reveals session tokens in URLs or logs", "category": "Session Binding"},
            "3.1.2": {"description": "Verify session tokens use secure cryptographic random generation", "category": "Session Tokens"},
            "3.2.1": {"description": "Verify the application generates new session tokens on authentication", "category": "Session Creation"},
            "3.2.2": {"description": "Verify session tokens are invalidated on logout", "category": "Session Termination"},
            "3.2.3": {"description": "Verify session timeout is configurable and enforced", "category": "Session Timeout"},
            "3.3.1": {"description": "Verify the application has a session inactivity timeout", "category": "Session Timeout"},
            "3.3.2": {"description": "Verify the application terminates sessions after a period of inactivity", "category": "Session Timeout"},
            "3.4.1": {"description": "Verify cookie attributes are set: HttpOnly, Secure, SameSite", "category": "Cookie Security"},
            "3.4.2": {"description": "Verify cookies are scoped to the minimum path", "category": "Cookie Security"},
            "3.5.1": {"description": "Verify the application binds the session token to the browser fingerprint", "category": "Session Binding"},
            "3.6.1": {"description": "Verify the application prevents concurrent sessions", "category": "Session Management"},
            "3.7.1": {"description": "Verify session tokens are stored securely on the server", "category": "Session Storage"},
        },
    },
    "V4": {
        "name": "Access Control Verification",
        "controls": {
            "4.1.1": {"description": "Verify the principle of least privilege exists for all users", "category": "Least Privilege"},
            "4.1.2": {"description": "Verify the application enforces access controls at the server side", "category": "Server-side Enforcement"},
            "4.1.3": {"description": "Verify the application denies access by default", "category": "Deny by Default"},
            "4.2.1": {"description": "Verify the application implements role-based access control", "category": "RBAC"},
            "4.2.2": {"description": "Verify the application implements attribute-based access control", "category": "ABAC"},
            "4.3.1": {"description": "Verify administrative interfaces use appropriate access controls", "category": "Admin Interfaces"},
            "4.3.2": {"description": "Verify the application logs all access control failures", "category": "Audit Logging"},
            "4.4.1": {"description": "Verify the application enforces access controls on all RESTful endpoints", "category": "API Access"},
            "4.5.1": {"description": "Verify the application has a centralized access control mechanism", "category": "Centralized"},
        },
    },
    "V5": {
        "name": "Validation, Sanitization and Encoding",
        "controls": {
            "5.1.1": {"description": "Verify the application validates all input from any trusted source", "category": "Input Validation"},
            "5.1.2": {"description": "Verify the application uses a positive validation strategy", "category": "Positive Validation"},
            "5.1.3": {"description": "Verify the application validates all untrusted data before processing", "category": "Input Validation"},
            "5.2.1": {"description": "Verify the application sanitizes all output to prevent injection attacks", "category": "Output Encoding"},
            "5.2.2": {"description": "Verify output encoding is context-appropriate", "category": "Output Encoding"},
            "5.3.1": {"description": "Verify the application prevents SQL injection", "category": "SQL Injection"},
            "5.3.2": {"description": "Verify the application uses parameterized queries", "category": "SQL Injection"},
            "5.3.3": {"description": "Verify the application prevents NoSQL injection", "category": "NoSQL Injection"},
            "5.4.1": {"description": "Verify the application prevents cross-site scripting (XSS)", "category": "XSS"},
            "5.4.2": {"description": "Verify HTTP Content-Type and X-Content-Type-Options headers are set", "category": "XSS"},
            "5.5.1": {"description": "Verify the application prevents XML injection", "category": "XML Injection"},
            "5.5.2": {"description": "Verify the application prevents LDAP injection", "category": "LDAP Injection"},
            "5.5.3": {"description": "Verify the application prevents OS command injection", "category": "Command Injection"},
            "5.5.4": {"description": "Verify the application prevents SSRF", "category": "SSRF"},
            "5.6.1": {"description": "Verify the application validates file uploads by type and content", "category": "File Upload"},
            "5.6.2": {"description": "Verify the application validates file upload size", "category": "File Upload"},
        },
    },
    "V6": {
        "name": "Stored Cryptography Verification",
        "controls": {
            "6.1.1": {"description": "Verify the application uses approved cryptographic algorithms", "category": "Algorithm Selection"},
            "6.1.2": {"description": "Verify cryptographic keys are managed securely", "category": "Key Management"},
            "6.1.3": {"description": "Verify the application uses unique per-operation cryptographic keys", "category": "Key Management"},
            "6.2.1": {"description": "Verify random numbers are generated using approved algorithms", "category": "Random Generation"},
            "6.2.2": {"description": "Verify the application uses a secure random number generator", "category": "Random Generation"},
            "6.3.1": {"description": "Verify secret keys and passwords are stored encrypted", "category": "Secret Storage"},
            "6.3.2": {"description": "Verify the application supports key rotation", "category": "Key Rotation"},
            "6.4.1": {"description": "Verify the application uses authenticated encryption (AEAD)", "category": "Encryption"},
            "6.4.2": {"description": "Verify the application implements encryption at rest", "category": "Encryption"},
            "6.5.1": {"description": "Verify the application validates certificates properly", "category": "Certificate Validation"},
            "6.5.2": {"description": "Verify the application uses TLS for all communications", "category": "TLS"},
        },
    },
    "V7": {
        "name": "Error Handling and Logging Verification",
        "controls": {
            "7.1.1": {"description": "Verify the application does not leak sensitive information in error responses", "category": "Error Handling"},
            "7.1.2": {"description": "Verify the application handles exceptions gracefully", "category": "Error Handling"},
            "7.2.1": {"description": "Verify all authentication events are logged", "category": "Audit Logging"},
            "7.2.2": {"description": "Verify all access control events are logged", "category": "Audit Logging"},
            "7.2.3": {"description": "Verify logs contain sufficient detail for forensic analysis", "category": "Audit Logging"},
            "7.2.4": {"description": "Verify logs are protected from unauthorized access", "category": "Log Protection"},
            "7.2.5": {"description": "Verify time sources are synchronized to ensure accurate audit timestamps", "category": "Time Synchronization"},
            "7.3.1": {"description": "Verify the application monitors for security events", "category": "Security Monitoring"},
            "7.3.2": {"description": "Verify the application sends alerts for critical security events", "category": "Alerting"},
            "7.4.1": {"description": "Verify the application logs are immutable", "category": "Log Integrity"},
        },
    },
    "V8": {
        "name": "Data Protection Verification",
        "controls": {
            "8.1.1": {"description": "Verify the application protects sensitive data at rest", "category": "Data at Rest"},
            "8.1.2": {"description": "Verify the application protects sensitive data in transit", "category": "Data in Transit"},
            "8.2.1": {"description": "Verify the application implements data classification", "category": "Data Classification"},
            "8.2.2": {"description": "Verify the application enforces data retention policies", "category": "Data Retention"},
            "8.3.1": {"description": "Verify the application implements data minimization", "category": "Data Minimization"},
            "8.3.2": {"description": "Verify the application provides secure data disposal", "category": "Data Disposal"},
            "8.3.3": {"description": "Verify the application supports data portability", "category": "Data Portability"},
            "8.4.1": {"description": "Verify the application implements cache control for sensitive data", "category": "Cache Control"},
            "8.4.2": {"description": "Verify the application sanitizes sensitive data in client-side storage", "category": "Client Storage"},
        },
    },
    "V9": {
        "name": "Communications Verification",
        "controls": {
            "9.1.1": {"description": "Verify TLS is used for all client connections", "category": "TLS"},
            "9.1.2": {"description": "Verify TLS certificate validation is properly configured", "category": "TLS"},
            "9.1.3": {"description": "Verify TLS 1.2 or later is enforced", "category": "TLS"},
            "9.2.1": {"description": "Verify server connections use mutual TLS", "category": "mTLS"},
            "9.2.2": {"description": "Verify the application validates upstream server certificates", "category": "Upstream Verification"},
            "9.3.1": {"description": "Verify the application implements HSTS", "category": "HSTS"},
            "9.3.2": {"description": "Verify the application implements certificate pinning", "category": "Certificate Pinning"},
            "9.4.1": {"description": "Verify the application uses secure DNS", "category": "DNS Security"},
        },
    },
    "V10": {
        "name": "Malicious Code Verification",
        "controls": {
            "10.1.1": {"description": "Verify the application uses a code analysis tool", "category": "Code Analysis"},
            "10.1.2": {"description": "Verify the application undergoes regular security testing", "category": "Security Testing"},
            "10.2.1": {"description": "Verify the application does not include backdoor code", "category": "Backdoor Prevention"},
            "10.2.2": {"description": "Verify the application does not include debug code in production", "category": "Debug Code"},
            "10.3.1": {"description": "Verify the application validates all third-party code", "category": "Third-party Code"},
            "10.3.2": {"description": "Verify the application scans for malicious dependencies", "category": "Dependency Scanning"},
            "10.4.1": {"description": "Verify the application verifies software integrity", "category": "Software Integrity"},
            "10.4.2": {"description": "Verify the application supports code signing", "category": "Code Signing"},
        },
    },
    "V11": {
        "name": "Business Logic Verification",
        "controls": {
            "11.1.1": {"description": "Verify the application validates the integrity of business logic flows", "category": "Business Logic"},
            "11.1.2": {"description": "Verify the application prevents parameter tampering", "category": "Business Logic"},
            "11.2.1": {"description": "Verify the application enforces business rules server-side", "category": "Business Rules"},
            "11.2.2": {"description": "Verify the application implements rate limiting per business operation", "category": "Rate Limiting"},
            "11.3.1": {"description": "Verify the application logs business logic failures", "category": "Business Logic"},
            "11.4.1": {"description": "Verify the application prevents race conditions", "category": "Concurrency"},
            "11.4.2": {"description": "Verify the application uses atomic operations for transactions", "category": "Concurrency"},
        },
    },
    "V12": {
        "name": "Files and Resources Verification",
        "controls": {
            "12.1.1": {"description": "Verify the application validates file uploads", "category": "File Upload"},
            "12.1.2": {"description": "Verify the application stores files outside the webroot", "category": "File Storage"},
            "12.2.1": {"description": "Verify the application restricts file execution permissions", "category": "File Permissions"},
            "12.2.2": {"description": "Verify the application prevents path traversal", "category": "Path Traversal"},
            "12.3.1": {"description": "Verify the application limits upload file size", "category": "File Upload"},
            "12.3.2": {"description": "Verify the application scans uploaded files for malware", "category": "File Upload"},
            "12.4.1": {"description": "Verify the application uses a content delivery network for static files", "category": "Content Delivery"},
            "12.5.1": {"description": "Verify the application validates file download requests", "category": "File Download"},
        },
    },
    "V13": {
        "name": "API and Web Service Verification",
        "controls": {
            "13.1.1": {"description": "Verify the application validates API schemas", "category": "API Validation"},
            "13.1.2": {"description": "Verify the application validates API request parameters", "category": "API Validation"},
            "13.2.1": {"description": "Verify the application implements API rate limiting", "category": "API Security"},
            "13.2.2": {"description": "Verify the application implements API authentication", "category": "API Security"},
            "13.3.1": {"description": "Verify the application implements API authorization", "category": "API Security"},
            "13.3.2": {"description": "Verify the application logs API access", "category": "API Logging"},
            "13.4.1": {"description": "Verify the application restricts API HTTP methods", "category": "API Security"},
            "13.4.2": {"description": "Verify the application validates Content-Type headers", "category": "API Security"},
            "13.5.1": {"description": "Verify the application implements GraphQL query depth limiting", "category": "API Security"},
            "13.5.2": {"description": "Verify the application implements API versioning", "category": "API Versioning"},
        },
    },
    "V14": {
        "name": "Configuration Verification",
        "controls": {
            "14.1.1": {"description": "Verify the application hardens the web server configuration", "category": "Server Hardening"},
            "14.1.2": {"description": "Verify the application disables unnecessary HTTP methods", "category": "Server Hardening"},
            "14.2.1": {"description": "Verify the application disables directory listing", "category": "Server Hardening"},
            "14.2.2": {"description": "Verify the application removes default accounts and credentials", "category": "Default Config"},
            "14.3.1": {"description": "Verify the application implements CSP headers", "category": "Security Headers"},
            "14.3.2": {"description": "Verify the application implements CORS policy", "category": "CORS"},
            "14.4.1": {"description": "Verify the application uses secure deployment configurations", "category": "Deployment"},
            "14.4.2": {"description": "Verify the application enforces container security", "category": "Container Security"},
            "14.4.3": {"description": "Verify the application implements network segmentation", "category": "Network Security"},
            "14.5.1": {"description": "Verify the application uses environment-specific configuration files", "category": "Configuration Mgmt"},
        },
    },
}


class ASVSValidator:
    def __init__(self):
        self._controls: dict[str, ComplianceControl] = {}
        self._initialize_controls()

    def _initialize_controls(self) -> None:
        for chapter_id, chapter in ASVS_CHAPTERS.items():
            for control_id, control_info in chapter["controls"].items():
                self._controls[control_id] = ComplianceControl(
                    control_id=f"ASVS-{control_id}",
                    framework=ComplianceFramework.OWASP_ASVS,
                    category=control_info["category"],
                    description=f"[{chapter_id}] {chapter['name']}: {control_info['description']}",
                    implementation_status=ControlStatus.NOT_IMPLEMENTED,
                    test_procedure=self._get_test_procedure(control_id),
                    risk_if_missing=f"Non-compliance with ASVS {control_id}",
                )

    @staticmethod
    def _get_test_procedure(control_id: str) -> str:
        test_procedures = {
            "2.1.1": "Verify password hashing configuration (Argon2id/bcrypt/scrypt) and cost factors",
            "2.1.2": "Verify minimum password length enforcement in authentication system",
            "2.3.1": "Review credential storage implementation against NIST SP 800-63B",
            "3.1.1": "Check session token handling across application (URLs, logs, referrer headers)",
            "3.4.1": "Inspect cookie configuration for HttpOnly, Secure, SameSite attributes",
            "5.1.1": "Review input validation implementation across all application endpoints",
            "5.3.1": "Verify SQL injection prevention (parameterized queries, ORM, stored procedures)",
            "5.4.1": "Verify XSS prevention (output encoding, CSP headers, input validation)",
            "6.1.1": "Verify approved cryptographic algorithms (AES-256-GCM, ChaCha20-Poly1305, SHA-256/384)",
            "7.1.1": "Review error handling to ensure no stack traces are exposed",
            "7.2.1": "Verify audit logging of authentication events (success, failure, MFA)",
            "9.1.1": "Verify TLS configuration (protocols, ciphers, certificate validation)",
            "13.1.1": "Verify OpenAPI schema validation for all API endpoints",
            "14.2.1": "Check server configuration for directory listing prevention",
            "14.3.1": "Verify CSP headers are properly configured and enforced",
        }
        return test_procedures.get(control_id, "Manual verification required per ASVS documentation")

    def update_control_status(self, control_id: str, status: ControlStatus,
                               evidence: list[str] | None = None) -> bool:
        if control_id in self._controls:
            self._controls[control_id].implementation_status = status
            if evidence:
                self._controls[control_id].evidence = evidence
            self._controls[control_id].last_assessed = datetime.now(UTC)
            return True
        return False

    def update_controls_batch(self, updates: dict[str, ControlStatus]) -> int:
        updated = 0
        for control_id, status in updates.items():
            if self.update_control_status(control_id, status):
                updated += 1
        return updated

    def verify_control(self, control_id: str, verification_data: dict[str, Any]) -> dict[str, Any]:
        if control_id not in self._controls:
            return {"found": False, "message": f"Control {control_id} not found"}

        control = self._controls[control_id]
        chapter_id = control_id.split(".")[0]
        chapter = ASVS_CHAPTERS.get(f"V{chapter_id}", {})

        automated_checks = {
            "2.1.1": lambda d: d.get("password_hashing") in ("bcrypt", "argon2id", "scrypt"),
            "3.4.1": lambda d: d.get("httponly") and d.get("secure") and d.get("samesite"),
            "5.3.1": lambda d: d.get("parameterized_queries", False) or d.get("orm_used", False),
            "9.1.1": lambda d: d.get("tls_version", "") in ("TLSv1.2", "TLSv1.3"),
            "14.3.1": lambda d: d.get("csp_enabled", False),
        }

        check_fn = automated_checks.get(control_id, lambda d: False)
        automated_result = check_fn(verification_data)

        return {
            "found": True,
            "control": control_id,
            "description": control.description,
            "chapter": chapter.get("name", ""),
            "automated_check_passed": automated_result,
            "current_status": control.implementation_status.value,
            "last_assessed": control.last_assessed,
        }

    def get_control(self, control_id: str) -> ComplianceControl | None:
        return self._controls.get(control_id)

    def get_all_controls(self) -> dict[str, ComplianceControl]:
        return dict(self._controls)

    def get_controls_by_chapter(self) -> dict[str, list[ComplianceControl]]:
        chapters: dict[str, list[ComplianceControl]] = {}
        for control_id, control in self._controls.items():
            chapter_key = f"V{control_id.split('-')[1].split('.')[0]}"
            if chapter_key not in chapters:
                chapters[chapter_key] = []
            chapters[chapter_key].append(control)
        return chapters

    def generate_report(self) -> ComplianceReport:
        controls = list(self._controls.values())
        passed = sum(1 for c in controls if c.implementation_status in (
            ControlStatus.IMPLEMENTED, ControlStatus.NOT_APPLICABLE))
        failed = sum(1 for c in controls if c.implementation_status in (
            ControlStatus.NOT_IMPLEMENTED, ControlStatus.PARTIALLY_IMPLEMENTED))

        not_implemented = [c for c in controls if c.implementation_status == ControlStatus.NOT_IMPLEMENTED]
        remediation = {c.control_id: f"Implement {c.description[:60]}..." for c in not_implemented[:20]}

        if passed / max(len(controls), 1) >= 0.9:
            overall = ControlStatus.IMPLEMENTED
        elif passed / max(len(controls), 1) >= 0.5:
            overall = ControlStatus.PARTIALLY_IMPLEMENTED
        else:
            overall = ControlStatus.NOT_IMPLEMENTED

        return ComplianceReport(
            framework=ComplianceFramework.OWASP_ASVS,
            overall_status=overall,
            control_count=len(controls),
            passed=passed,
            failed=failed,
            not_applicable=sum(1 for c in controls if c.implementation_status == ControlStatus.NOT_APPLICABLE),
            findings=not_implemented[:50],
            remediation_plan=remediation,
        )

    def gap_analysis(self) -> dict[str, Any]:
        controls = list(self._controls.values())
        total = len(controls)

        by_chapter: dict[str, dict[str, int]] = {}
        for control_id, control in self._controls.items():
            chapter_key = f"V{control_id.split('-')[1].split('.')[0]}"
            chapter_name = ASVS_CHAPTERS.get(chapter_key, {}).get("name", "Unknown")
            if chapter_key not in by_chapter:
                by_chapter[chapter_key] = {"name": chapter_name, "total": 0, "implemented": 0, "partial": 0, "missing": 0}
            by_chapter[chapter_key]["total"] += 1
            if control.implementation_status == ControlStatus.IMPLEMENTED:
                by_chapter[chapter_key]["implemented"] += 1
            elif control.implementation_status == ControlStatus.PARTIALLY_IMPLEMENTED:
                by_chapter[chapter_key]["partial"] += 1
            else:
                by_chapter[chapter_key]["missing"] += 1

        implemented = sum(1 for c in controls if c.implementation_status == ControlStatus.IMPLEMENTED)
        partial = sum(1 for c in controls if c.implementation_status == ControlStatus.PARTIALLY_IMPLEMENTED)
        missing = sum(1 for c in controls if c.implementation_status == ControlStatus.NOT_IMPLEMENTED)

        return {
            "total_controls": total,
            "implemented": implemented,
            "partially_implemented": partial,
            "not_implemented": missing,
            "implementation_percentage": round(implemented / max(total, 1) * 100, 1),
            "by_chapter": by_chapter,
            "critical_gaps": [c.control_id for c in controls
                             if c.implementation_status == ControlStatus.NOT_IMPLEMENTED],
        }
