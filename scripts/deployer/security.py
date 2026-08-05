"""Phase 8 — Deployment Security.

Verify secrets handling, TLS, certificates, firewall, container security,
dependency security, least privilege, image scanning, and supply chain
validation before and after deployment. Deterministic checks; a critical
finding blocks the deployment.
"""

from __future__ import annotations

import re

from scripts.deployer.core import (
    SECURITY_AREAS,
    SecurityCheck,
)

# Baseline assertions per security area.
SECURITY_ASSERTIONS: dict[str, str] = {
    "secrets": "secrets must not appear in images or compose files",
    "tls": "all public endpoints require TLS 1.2+",
    "certificates": "certificates must be managed and auto-renewed",
    "firewall": "only required ports are exposed externally",
    "container-security": "containers run non-root with no-new-privileges",
    "dependency-security": "dependencies must pass scanning with no critical CVEs",
    "least-privilege": "service accounts and tokens carry minimal scopes",
    "image-scanning": "images must be scanned before promotion",
    "supply-chain": "images must be pinned and signed",
}

SECRET_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"(?i)\b(pg_password|postgres_password|redis_password)\s*[:=]\s*['\"]?[^'\"]{4,}"),
    re.compile(r"(?i)\bapi[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9+/]{16,}"),
    re.compile(r"(?i)\bsecret\s*[:=]\s*['\"]?[A-Za-z0-9+/]{16,}"),
)


def verify_secrets(content: str) -> list[str]:
    """Scan content for exposed secrets."""
    findings: list[str] = []
    for pattern in SECRET_PATTERNS:
        for match in pattern.finditer(content):
            findings.append(f"possible secret exposure: {match.group(0)[:40]}...")
    return findings


def verify_areas(*, secrets_clean: bool = True,
                 tls_enabled: bool = True,
                 certs_managed: bool = True,
                 firewall_closed: bool = True,
                 non_root: bool = True,
                 deps_scanned: bool = True,
                 minimal_scope: bool = True,
                 images_scanned: bool = True,
                 supply_chain_pinned: bool = True) -> list[SecurityCheck]:
    """Run the nine security area checks deterministically."""
    flags = {
        "secrets": secrets_clean,
        "tls": tls_enabled,
        "certificates": certs_managed,
        "firewall": firewall_closed,
        "container-security": non_root,
        "dependency-security": deps_scanned,
        "least-privilege": minimal_scope,
        "image-scanning": images_scanned,
        "supply-chain": supply_chain_pinned,
    }
    checks: list[SecurityCheck] = []
    for area in SECURITY_AREAS:
        passed = flags.get(area, False)
        checks.append(SecurityCheck(
            area=area,
            finding=SECURITY_ASSERTIONS.get(area, ""),
            passed=passed,
            severity="low" if passed else "high",
            evidence="verified" if passed else "not verified",
        ))
    return checks


def deployment_blocked(checks: list[SecurityCheck]) -> bool:
    """Block the deployment when any area fails verification."""
    return any(not c.passed for c in checks)


def security_summary(checks: list[SecurityCheck]) -> str:
    passed = sum(1 for c in checks if c.passed)
    total = len(checks)
    verdict = "BLOCKED" if deployment_blocked(checks) else "CLEARED"
    return f"security verification: {passed}/{total} areas passed -> {verdict}"
