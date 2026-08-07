"""PROGRAM-ALPHA — Architecture Constitution (Phase 7).

Deterministic gate that makes the GULA architecture constitution permanent:

    Future Pull Requests must automatically fail if they:
      - duplicate infrastructure (identity, notifications, audit, barcode,
        QR, workflow, rules, encryption, caching, search, events, DI)
      - break Shared Core / Domain Sovereignty / Workspace isolation
      - introduce country-specific hard-coding outside the national layer

The engine scans the repository for files that re-implement a Shared Core
service OUTSIDE its canonical provider paths. Findings that already exist are
tracked in a committed baseline (known debt awaiting migration); any finding
NOT in the baseline is a hard gate failure — that is what makes future PRs
automatically fail.

Run `architecture-baseline` only when intentionally acknowledging new debt.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Canonical provider paths per Shared Core service. A file under one of these
# prefixes is the authoritative implementation and is exempt from the rule.
CANONICAL_PROVIDERS: dict[str, tuple[str, ...]] = {
    "identity": (
        "backend/app/identity",
        "shared/identity",
        "backend/app/security",
    ),
    "authentication": (
        "backend/app/identity",
        "backend/app/security",
        "shared/auth",
    ),
    "authorization": (
        "backend/app/identity",
        "backend/app/security",
        "shared/rbac",
    ),
    "notifications": (
        "backend/app/notifications",
        "shared/notifications",
        "shared/communication",
        "shared/communication_providers",
    ),
    "audit": (
        "shared/audit",
        "backend/app/identity/models/audit.py",
        "backend/app/identity/services/audit_service.py",
        "backend/app/services/audit_service.py",
        "backend/app/audit",
    ),
    "workflow_engine": (
        "shared/workflow",
        "backend/app/workflows",
        "backend/app/capabilities/workflow_engine",
    ),
    "rule_engine": (
        "shared/rules_engine",
        "backend/app/rules",
    ),
    "barcode_engine": ("shared/barcode",),
    "qr_engine": ("shared/qr",),
    "search_engine": (
        "shared/search.py",
        "backend/app/capabilities/search_service",
    ),
    "encryption": (
        "shared/security",
        "backend/app/security",
    ),
    "cache": ("shared/cache",),
    "events": ("shared/events",),
    "dependency_injection": ("shared/di_container",),
    "scheduler": ("shared/scheduler.py",),
    "document_engine": (
        "backend/app/capabilities/document_management",
        "shared/pdf",
    ),
}

# Reimplementation signals per rule. Matched with word boundaries so names
# like "SchedulerRepository" or "IdentityDocument" never false-positive.
RULES: dict[str, dict[str, object]] = {
    "identity": {
        "description": "A new identity/authentication implementation outside the NIAM identity platform.",
        "signals": (
            r"class\s+\w*(?:IdentityService|IdentityProvider|LoginService|AuthService|AuthenticationService)\b",
            r"def\s+(?:authenticate|login|register_user)\s*\(",
            r"class\s+\w*UserRepository\b",
        ),
    },
    "authentication": {
        "description": "A new password/JWT/MFA/SSO implementation outside shared/auth + NIAM.",
        "signals": (
            r"class\s+\w*(?:JwtProvider|TokenService|MfaService|SsoProvider)\b",
            r"create_access_token\s*\(",
            r"verify_password\s*\(",
        ),
    },
    "authorization": {
        "description": "A new RBAC/ABAC permission implementation outside the platform.",
        "signals": (
            r"class\s+\w*(?:Rbac|Abac|PermissionService|PolicyEnforcer)\b",
            r"def\s+check_permission\s*\(",
        ),
    },
    "notifications": {
        "description": "A new notification delivery system outside the platform notification core.",
        "signals": (
            r"class\s+\w*(?:NotificationService|NotificationCenter|Notifier|NotificationSender)\b",
            r"def\s+send_notification\s*\(",
            r"class\s+\w*(?:SmsProvider|EmailProvider|PushProvider)\b",
        ),
    },
    "audit": {
        "description": "A new audit-log implementation outside the platform audit core.",
        "signals": (
            r"class\s+\w*(?:AuditService|AuditLogger|AuditLogRepository)\b",
            r"def\s+write_audit\s*\(",
            r"def\s+record_audit_event\s*\(",
        ),
    },
    "workflow_engine": {
        "description": "A new workflow engine outside the platform workflow core.",
        "signals": (
            r"class\s+\w*(?:WorkflowEngine|WorkflowManager|WorkflowExecutor)\b",
            r"def\s+execute_workflow\s*\(",
        ),
    },
    "rule_engine": {
        "description": "A new business-rules engine outside the platform rules core.",
        "signals": (
            r"class\s+\w*(?:RuleEngine|RulesEngine|RuleEvaluator)\b",
            r"def\s+evaluate_rule\s*\(",
        ),
    },
    "barcode_engine": {
        "description": "A new barcode generator/decoder outside shared/barcode.",
        "signals": (
            r"class\s+\w*(?:BarcodeGenerator|BarcodeEngine|BarcodeEncoder)\b",
            r"def\s+(?:create_barcode|generate_barcode|decode_barcode)\s*\(",
        ),
    },
    "qr_engine": {
        "description": "A new QR generator/decoder outside shared/qr.",
        "signals": (
            r"class\s+\w*(?:QRCoder|QRGenerator|QrService)\b",
            r"def\s+(?:generate_qr|decode_qr)\s*\(",
        ),
    },
    "search_engine": {
        "description": "A new search implementation outside the platform search core.",
        "case_sensitive": True,
        "signals": (
            r"class\s+\w*(?:SearchService|SearchIndex|SearchEngine)\b",
            r"def\s+full_text_search\s*\(",
        ),
    },
    "encryption": {
        "description": "A new encryption/crypto implementation outside shared/security.",
        "signals": (
            r"class\s+\w*(?:Encryptor|Cipher|CryptoService)\b",
            r"\bFernet\s*\(",
            r"def\s+(?:encrypt|decrypt)_value\s*\(",
        ),
    },
    "cache": {
        "description": "A new cache backend outside shared/cache.",
        "signals": (
            r"class\s+\w*(?:CacheBackend|CacheService|RedisCache)\b",
            r"def\s+cache_get\s*\(",
        ),
    },
    "events": {
        "description": "A new event bus outside shared/events.",
        "signals": (
            r"class\s+\w*(?:EventBus|EventEmitter|MessageBus)\b",
            r"def\s+publish_event\s*\(",
        ),
    },
    "dependency_injection": {
        "description": "A new DI container outside shared/di_container.",
        "signals": (
            r"class\s+\w*(?:DiContainer|ServiceLocator)\b",
            r"def\s+resolve_dependency\s*\(",
        ),
    },
    "scheduler": {
        "description": "A new scheduler outside shared/scheduler.",
        "signals": (
            r"class\s+\w*(?:Scheduler|JobManager|CronEngine)\b",
            r"def\s+schedule_job\s*\(",
        ),
    },
    "document_engine": {
        "description": "A new document/PDF engine outside the platform document core.",
        "signals": (
            r"class\s+\w*(?:DocumentManager|PdfGenerator|DocumentRepository)\b",
            r"def\s+generate_pdf\s*\(",
        ),
    },
}

# Files that never represent application code.
_EXCLUDE_DIRS = ("__pycache__", ".venv", "node_modules", "dist", "build", ".git", "egg-info", "tests")
_EXCLUDE_PARTS = (
    "backend/tests",
    "backend/migrations",
    "backend/app/national/tests",
    "backend/app/routes/",
    "scripts/",
    "frontend",
    "android",
    "docs",
)


@dataclass(frozen=True)
class ConstitutionFinding:
    rule_id: str
    path: str
    signal: str

    def to_dict(self) -> dict[str, str]:
        return {"rule_id": self.rule_id, "path": self.path, "signal": self.signal}


def _is_canonical(rule_id: str, rel_path: str) -> bool:
    providers = CANONICAL_PROVIDERS.get(rule_id, ())
    normalized = rel_path.replace("\\", "/")
    for prefix in providers:
        prefix = prefix.replace("\\", "/")
        if normalized == prefix:
            return True
        if normalized.startswith(prefix.rstrip("/") + "/"):
            return True
        if normalized.endswith("/" + prefix):
            return True
        if "/" + prefix.rstrip("/") + "/" in normalized:
            return True
    return False


def iter_source_files(roots: Iterable[Path]) -> Iterable[Path]:
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.py")):
            parts = path.parts
            if any(seg in _EXCLUDE_DIRS for seg in parts):
                continue
            try:
                rel = path.relative_to(REPO_ROOT).as_posix()
            except ValueError:
                rel = str(path)
            if any(rel.startswith(part) for part in _EXCLUDE_PARTS):
                continue
            yield path, rel


def scan(roots: Iterable[Path]) -> list[ConstitutionFinding]:
    """Scan source for Shared Core reimplementation outside canonical providers.

    Deterministic: files are visited in sorted order, signals matched with word
    boundaries, one finding per (file, rule) pair (first signal reported).
    """
    findings: list[ConstitutionFinding] = []
    for path, rel in iter_source_files(roots):
        for rule_id, rule in RULES.items():
            if _is_canonical(rule_id, rel):
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            flags = 0 if rule.get("case_sensitive") else re.IGNORECASE
            for signal in rule["signals"]:
                if re.search(signal, text, flags):
                    findings.append(
                        ConstitutionFinding(rule_id=rule_id, path=rel, signal=signal)
                    )
                    break
    return findings
