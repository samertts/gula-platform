"""PROGRAM-STABLE-004 — Shared Core catalog (Phase 2).

Every Domain must consume ONLY the official Shared Core. No Domain may
reimplement any of these services. This module is the single canonical
catalog of Shared Core services and the enforcement helpers that detect
reimplementation and unauthorized infrastructure coupling.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain_platform.core import SHARED_CORE_SERVICES as SHARED_CORE_SERVICES

# Canonical Shared Core catalog: service -> (provider module, description).
# Every entry maps to a real, existing module in the GULA platform (``shared/``
# or ``backend/app/``). Domains consume these; they never rebuild them. A
# service may appear here only if exactly ONE authoritative provider exists;
# providers that exist elsewhere in the tree are documented as consolidation
# findings in MASTER_REMAINING_WORK.md and must be migrated before they may
# join this registry.
SHARED_CORE_CATALOG: dict[str, dict[str, str]] = {
    # ── Identity & Digital Trust ────────────────────────────────────────────
    "identity": {
        "provider": "backend/app/identity",
        "description": "NIAM identity registry (person, enterprise, machine, guest).",
    },
    "authentication": {
        "provider": "backend/app/identity/api/auth.py",
        "description": "Authentication (password, passkeys, OTP, OAuth2, OIDC, smart cards).",
    },
    "authorization": {
        "provider": "backend/app/identity/services/authorization_service.py",
        "description": "RBAC + ABAC + workspace-scoped permission checks.",
    },
    "organizations": {
        "provider": "backend/app/identity/models/niam_organization.py",
        "description": "Ministry/Directorate/Hospital/Laboratory hierarchy + org guard.",
    },
    "users": {
        "provider": "backend/app/identity/api/accounts.py",
        "description": "User/account registry and lifecycle.",
    },
    "sessions": {
        "provider": "backend/app/identity/api/sessions.py",
        "description": "Session registry, workspace binding, max concurrent enforcement.",
    },
    "audit": {
        "provider": "backend/app/identity/models/audit.py",
        "description": "Immutable, hash-chained audit log for every platform event.",
    },
    "rbac": {
        "provider": "shared/rbac/permissions.py",
        "description": "Role-based access control primitives.",
    },
    "abac": {
        "provider": "backend/app/security/abac.py",
        "description": "Attribute-based access control (subject/resource/context attributes).",
    },
    "encryption": {
        "provider": "shared/security/encryption.py",
        "description": "Symmetric/asymmetric encryption and at-rest protection.",
    },
    "digital_signature": {
        "provider": "shared/security/hmac.py",
        "description": "HMAC signatures, integrity and signing primitives.",
    },
    "mfa": {
        "provider": "shared/auth/mfa.py",
        "description": "Multi-factor authentication primitives (TOTP/OTP).",
    },
    "auth_primitives": {
        "provider": "shared/auth",
        "description": "JWT, password hashing and passkey/WebAuthn primitives.",
    },
    "service_accounts": {
        "provider": "backend/app/security/service_accounts.py",
        "description": "Machine/service identity and credentials.",
    },
    # ── Core platform services ──────────────────────────────────────────────
    "notifications": {
        "provider": "backend/app/notifications",
        "description": "Push, email, SMS, in-app notification delivery.",
    },
    "workflow_engine": {
        "provider": "backend/app/workflows",
        "description": "Workflow engine for multi-step clinical and operational flows.",
    },
    "rule_engine": {
        "provider": "shared/rules_engine",
        "description": "Deterministic business/clinical rule engine.",
    },
    "barcode_engine": {
        "provider": "shared/barcode",
        "description": "Barcode generation and decoding.",
    },
    "qr_engine": {
        "provider": "shared/qr",
        "description": "QR generation and decoding.",
    },
    "search_engine": {
        "provider": "backend/app/capabilities/search_service",
        "description": "Unified search engine over platform records.",
    },
    "reporting_framework": {
        "provider": "backend/app/capabilities/reporting_service",
        "description": "Report generation framework (domain reports build on it).",
    },
    "document_engine": {
        "provider": "backend/app/capabilities/document_management",
        "description": "Clinical and administrative document management.",
    },
    "files": {
        "provider": "shared/storage",
        "description": "File storage and retrieval (MinIO / object storage).",
    },
    "media": {
        "provider": "shared/storage",
        "description": "Image and media asset handling.",
    },
    "pdf_engine": {
        "provider": "shared/pdf/generator.py",
        "description": "PDF generation for reports, labels and documents.",
    },
    "printing": {
        "provider": "shared/printing/printer.py",
        "description": "Label/report printing primitives.",
    },
    "payments": {
        "provider": "shared/payments.py",
        "description": "Payment processing primitives (country-agnostic gateways).",
    },
    "scheduler": {
        "provider": "shared/scheduler.py",
        "description": "Recurring job scheduling (domain workflows consume it).",
    },
    "event_bus": {
        "provider": "shared/events",
        "description": "Event bus for async cross-domain events.",
    },
    "api_gateway": {
        "provider": "backend/app/routes",
        "description": "Gateway routing, versioning, rate limiting.",
    },
    "api_schemas": {
        "provider": "shared/schemas",
        "description": "Shared pagination/response schemas for stable API contracts.",
    },
    "validators": {
        "provider": "shared/validators/common.py",
        "description": "Cross-cutting input and value validators.",
    },
    "localization": {
        "provider": "shared/localization.py",
        "description": "Arabic-first localization and i18n.",
    },
    "design_system": {
        "provider": "shared/design_system",
        "description": "RTL-first design tokens and components.",
    },
    "config_loader": {
        "provider": "shared/config/loader.py",
        "description": "Environment-aware configuration loading.",
    },
    "settings": {
        "provider": "backend/app/config.py",
        "description": "Platform configuration and settings.",
    },
    "dependency_injection": {
        "provider": "shared/di_container",
        "description": "DI container for modular composition.",
    },
    "device_integration": {
        "provider": "shared/device",
        "description": "Analyzer/modality integration (ASTM, HL7 adapters).",
    },
    "communication": {
        "provider": "shared/communication",
        "description": "Provider-neutral communication platform (channels, queue, policy).",
    },
    "ai_gateway": {
        "provider": "shared/ai",
        "description": "Self-hosted AI inference gateway (Ollama-first, provider-swappable).",
    },
    # ── Observability & resilience ──────────────────────────────────────────
    "feature_flags": {
        "provider": "shared/feature_flags.py",
        "description": "Feature flag evaluation and rollout controls.",
    },
    "health_checks": {
        "provider": "shared/health/checker.py",
        "description": "Liveness/readiness health check primitives.",
    },
    "monitoring": {
        "provider": "backend/app/services/metrics_service.py",
        "description": "Metrics, health checks, Prometheus endpoints.",
    },
    "logging": {
        "provider": "shared/logging",
        "description": "Structured logging and tracing.",
    },
    "telemetry": {
        "provider": "shared/observability/tracer.py",
        "description": "Distributed tracing (OTLP) and metrics collection.",
    },
    "cache": {
        "provider": "shared/cache/backends.py",
        "description": "Multi-backend caching (Redis, in-memory).",
    },
    "retry": {
        "provider": "shared/retry/decorators.py",
        "description": "Retry decorators with backoff for resilience.",
    },
    "circuit_breaker": {
        "provider": "shared/circuit_breaker.py",
        "description": "Circuit breaker for failing dependencies.",
    },
    "backup_recovery": {
        "provider": "shared/backup/manager.py",
        "description": "Backup and recovery orchestration.",
    },
    "fhir_engine": {
        "provider": "backend/app/fhir",
        "description": "FHIR R4 engine (resources, profiles, mappers, validation).",
    },
}

# Module paths that are allowed Shared Core providers. A Domain module may
# import these freely. Everything else in a Domain's module set must be its
# own blueprint content or a declared cross-domain contract.
SHARED_CORE_PROVIDER_PREFIXES: tuple[str, ...] = (
    "shared.",
    "app.identity.",
    "app.security.",
    "app.audit.",
    "app.notifications.",
    "app.workflows.",
    "app.fhir.",
    "app.rules.",
    "app.events.",
    "app.telemetry",
    "app.config",
    "app.middleware",
)

# Shared Core services that are commonly reimplemented by accident inside a
# Domain (infrastructure reimplementation detection, Phase 7 check #2).
# Signals are matched as whole identifiers (word boundaries) so class names
# such as "RareDiseaseRegistry" never trigger "Redis".
INFRASTRUCTURE_REIMPLEMENTATION_SIGNALS: dict[str, tuple[str, ...]] = {
    "cache": ("lru_cache", "redis_client", "redis\\.Redis", "cachetools", "simple_cache"),
    "queue": ("task_queue", "celery", "huey", "from rq ", "import rq"),
    "database": ("create_engine", "create_async_engine", "sessionmaker", "engine_from_config"),
    "encryption": ("Fernet", "encrypt_value", "decrypt_value", "AESGCM"),
    "logging": ("basicConfig", "RotatingFileHandler"),
    "events": ("EventEmitter", "publish_event", "emit_event"),
    "barcode": ("create_barcode", "barcode\\.generate", "barcode_engine"),
    "qr": ("import qrcode", "qrcode\\.make", "QRCode\\(", "qr_engine"),
}


@dataclass(frozen=True)
class SharedCoreService:
    service: str
    provider: str
    description: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "service": self.service,
            "provider": self.provider,
            "description": self.description,
        }


def shared_core_services() -> list[SharedCoreService]:
    return [
        SharedCoreService(
            service=name,
            provider=entry["provider"],
            description=entry["description"],
        )
        for name, entry in SHARED_CORE_CATALOG.items()
    ]


def is_shared_core_import(module: str) -> bool:
    """Return True when ``module`` is an allowed Shared Core provider."""
    for prefix in SHARED_CORE_PROVIDER_PREFIXES:
        if module.startswith(prefix):
            return True
    return module == "shared" or module.startswith("shared.")


def is_infrastructure_reimplementation(code: str) -> list[str]:
    """Heuristic detection of a Domain reimplementing Shared Core.

    Returns the names of Shared Core services that appear to be reimplemented
    by the given source. Signals are matched as whole identifiers so that
    class/attribute names never trigger false positives. Used by the Phase 7
    certification check #2 (no duplicated infrastructure).
    """
    import re

    findings: list[str] = []
    for service, signals in INFRASTRUCTURE_REIMPLEMENTATION_SIGNALS.items():
        for signal in signals:
            pattern = rf"\b{signal}\b" if re.match(r"^[\w\.]+$", signal) else signal
            if re.search(pattern, code, re.IGNORECASE):
                findings.append(service)
                break
    return findings
