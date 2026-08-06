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
# Every entry maps to a real module in the GULA platform (``shared/`` or
# ``backend/app/``). Domains consume these; they never rebuild them.
SHARED_CORE_CATALOG: dict[str, dict[str, str]] = {
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
    "audit": {
        "provider": "backend/app/identity/models/audit.py",
        "description": "Immutable, hash-chained audit log for every platform event.",
    },
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
    "scheduler": {
        "provider": "shared/scheduler.py",
        "description": "Recurring job scheduling (domain workflows consume it).",
    },
    "localization": {
        "provider": "shared/localization.py",
        "description": "Arabic-first localization and i18n.",
    },
    "monitoring": {
        "provider": "backend/app/services/metrics_service.py",
        "description": "Metrics, health checks, Prometheus endpoints.",
    },
    "logging": {
        "provider": "shared/logging",
        "description": "Structured logging and tracing.",
    },
    "api_gateway": {
        "provider": "backend/app/routes",
        "description": "Gateway routing, versioning, rate limiting.",
    },
    "fhir_engine": {
        "provider": "backend/app/fhir",
        "description": "FHIR R4 engine (resources, profiles, mappers, validation).",
    },
    "event_bus": {
        "provider": "shared/events",
        "description": "Event bus for async cross-domain events.",
    },
    "settings": {
        "provider": "backend/app/config.py",
        "description": "Platform configuration and settings.",
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
