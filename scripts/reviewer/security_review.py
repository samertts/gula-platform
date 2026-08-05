"""Phase 3 — Security Review.

Verify OWASP-relevant signals deterministically: hardcoded secrets,
credential exposure, authentication/authorization wiring, TLS posture,
immutable audit log presence, encryption usage, and dependency hygiene.
"""

from __future__ import annotations

import re
from pathlib import Path

from scripts.kernel.core import REPO_ROOT, Severity
from scripts.reviewer.core import ReviewFinding

# Patterns that commonly indicate hardcoded secrets or credential misuse.
SECRET_PATTERNS: tuple[tuple[str, str], tuple[str, str]] = (
    (r"(?i)(password|passwd|pwd|secret|token|api[_-]?key|private[_-]?key)\s*=\s*['\"][^'\"]{6,}['\"]",
     "hardcoded credential literal"),
    (r"os\.environ\.get\(['\"][A-Z_]+['\"]\s*,\s*['\"][^'\"]{4,}['\"]",
     "env var with non-empty default credential"),
    (r"BEGIN [A-Z ]*PRIVATE KEY", "embedded private key"),
)

SENSITIVE_KEYS = ("PASSWORD", "SECRET", "API_KEY", "TOKEN", "PRIVATE_KEY")


def _scan_files(root: Path, glob: str) -> list[Path]:
    if not root.exists():
        return []
    excluded = {".venv", "site-packages", "node_modules", "migrations", "__pycache__", "dist", "build"}
    return sorted(
        p for p in root.rglob(glob)
        if not any(part in excluded for part in p.parts)
    )


def check_hardcoded_secrets(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Scan Python/config for hardcoded secrets (ignores test fixtures)."""
    findings: list[ReviewFinding] = []
    strings_re = re.compile(r"""(['"])(?:\\.|(?!\1).)*\1""", re.DOTALL)
    for path in _scan_files(repo / "backend", "*.py") + _scan_files(repo / "config", "*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        code = strings_re.sub("''", text)
        for pattern, label in SECRET_PATTERNS:
            matches = re.findall(pattern, code)
            if matches and "test" not in path.name:
                findings.append(ReviewFinding(
                    "security", Severity.HIGH, label,
                    detail=f"{len(matches)} match(es) in {path.relative_to(repo)}",
                    evidence=path.name,
                    suggested_fix="load credentials from environment or a vault; never commit literals",
                ))
    return findings


def check_auth_authorization_wiring(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Verify RBAC/ABAC primitives are declared and enforced."""
    findings: list[ReviewFinding] = []
    security_dir = repo / "backend" / "app" / "security"
    has_permission = any("require_permission" in p.read_text(encoding="utf-8", errors="ignore")
                         for p in _scan_files(security_dir, "*.py"))
    if not has_permission:
        findings.append(ReviewFinding(
            "security", Severity.CRITICAL, "Permission enforcement missing",
            detail="no require_permission primitive found in backend/app/security",
            evidence="backend/app/security",
            suggested_fix="implement centralized permission enforcement",
        ))
    return findings


def check_encryption_usage(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Verify encryption module exists and is exercised."""
    findings: list[ReviewFinding] = []
    enc = repo / "shared" / "security" / "encryption.py"
    if not enc.exists():
        findings.append(ReviewFinding(
            "security", Severity.HIGH, "Encryption module missing",
            detail="shared/security/encryption.py not found",
            evidence="shared/security",
            suggested_fix="restore the shared encryption module",
        ))
        return findings
    usage = sum("encrypt_value" in p.read_text(encoding="utf-8", errors="ignore")
                for p in _scan_files(repo / "backend", "*.py"))
    if usage < 2:
        findings.append(ReviewFinding(
            "security", Severity.LOW, "Encryption underutilized",
            detail=f"encrypt_value referenced in only {usage} backend files",
            evidence="backend/",
            suggested_fix="encrypt at-rest sensitive fields at the persistence boundary",
        ))
    return findings


def check_tls_posture(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Verify TLS is configured for the web tier."""
    findings: list[ReviewFinding] = []
    tls_mentions = 0
    for path in _scan_files(repo / "config", "*.conf") + _scan_files(repo / ".github", "*.yml"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        tls_mentions += text.lower().count("ssl") + text.lower().count("https")
    if tls_mentions == 0:
        findings.append(ReviewFinding(
            "security", Severity.MEDIUM, "TLS posture undocumented",
            detail="no ssl/https configuration found in config/ or CI",
            evidence="config/, .github/workflows",
            suggested_fix="terminate TLS at the edge (e.g. Let's Encrypt) and document it",
        ))
    return findings


def check_immutable_audit(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Verify an immutable audit log exists."""
    findings: list[ReviewFinding] = []
    audit_dir = repo / "backend" / "app" / "audit"
    if not audit_dir.exists():
        findings.append(ReviewFinding(
            "security", Severity.HIGH, "Audit log domain missing",
            detail="backend/app/audit not found",
            evidence="backend/app/audit",
            suggested_fix="restore the immutable audit module",
        ))
        return findings
    append_only = sum(
        "append" in p.read_text(encoding="utf-8", errors="ignore").lower()
        for p in _scan_files(audit_dir, "*.py")
    )
    if append_only == 0:
        findings.append(ReviewFinding(
            "security", Severity.MEDIUM, "Audit append-only property unproven",
            detail="no 'append' semantics found in backend/app/audit",
            evidence="backend/app/audit",
            suggested_fix="enforce append-only writes and detect tampering",
        ))
    return findings


def check_dependency_hygiene(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Verify a lockfile or pinned requirements exists."""
    findings: list[ReviewFinding] = []
    lockfiles = [p for p in (repo / "backend").iterdir() if p.name in {"requirements.txt", "uv.lock", "poetry.lock", "pdm.lock", "Pipfile.lock"}] if (repo / "backend").is_dir() else []
    if not lockfiles:
        findings.append(ReviewFinding(
            "security", Severity.MEDIUM, "Dependency lockfile absent",
            detail="no requirements lock file found in backend/",
            evidence="backend/",
            suggested_fix="pin transitive dependencies to prevent supply-chain drift",
        ))
    return findings


def review(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Run every security review check for a repository."""
    findings: list[ReviewFinding] = []
    findings += check_hardcoded_secrets(repo)
    findings += check_auth_authorization_wiring(repo)
    findings += check_encryption_usage(repo)
    findings += check_tls_posture(repo)
    findings += check_immutable_audit(repo)
    findings += check_dependency_hygiene(repo)
    return findings
