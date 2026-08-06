"""PROGRAM-STABLE-004 — Domain Platform pipeline.

Resolves the real GULA modules for every Domain, feeds them to the shared
Domain Platform Framework (backend/app/domain_platform), and produces the
isolation report + certification verdicts that drive the official documents.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_BACKEND = REPO_ROOT / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.domain_platform.certification import (  # noqa: E402
    CERTIFICATION_CHECKS,
    DomainCertificationEngine,
)
from app.domain_platform.core import (  # noqa: E402
    BLUEPRINT_SECTIONS,
    DOMAIN_LIFECYCLE_TRANSITIONS,
    DOMAIN_WORKSPACE_TYPES,
    SHARED_CORE_SERVICES,
)
from app.domain_platform.isolation import IsolationValidator  # noqa: E402
from app.domain_platform.lifecycle import DomainLifecycle  # noqa: E402
from app.domain_platform.manifest import CANONICAL_DOMAINS  # noqa: E402
from app.domain_platform.shared_core import shared_core_services  # noqa: E402

from .core import (  # noqa: E402
    DOMAIN_SOURCE_ROOTS,
    read_module_source,
    resolve_domain_modules,
)


def build_manifests_with_modules() -> list[Any]:
    """Attach the real resolved modules to the canonical manifests."""
    module_map = resolve_domain_modules()
    manifests = list(CANONICAL_DOMAINS.values())
    for manifest in manifests:
        manifest.modules = module_map.get(manifest.code, [])
        manifest.tables = _extract_tables(manifest.modules)
    return manifests


def _extract_tables(modules: list[str]) -> list[str]:
    tables: set[str] = set()
    for module in modules:
        source = read_module_source(module)
        for line in source.splitlines():
            stripped = line.strip()
            if "__tablename__" in stripped and "=" in stripped:
                value = stripped.split("=", 1)[1].strip().strip("\"'")
                if value:
                    tables.add(value)
    return sorted(tables)


def run_pipeline() -> dict[str, Any]:
    """Run the full isolation + certification pipeline over the real code."""
    manifests = build_manifests_with_modules()

    # Real module sources for the shared framework validators.
    sources: dict[str, str] = {}
    for manifest in manifests:
        for module in manifest.modules:
            sources[module] = read_module_source(module)

    validator = IsolationValidator(manifests)
    isolation_report = validator.run()

    engine = DomainCertificationEngine(isolation_report=isolation_report)
    engine.set_module_sources(sources)
    certifications = engine.certify_all(manifests)
    platform = engine.platform_certification(manifests)

    lifecycle: dict[str, Any] = {}
    for manifest in manifests:
        lifecycle[manifest.code] = _lifecycle_snapshot(manifest.code)

    return {
        "manifests": [m.to_dict() for m in manifests],
        "isolation": isolation_report.to_dict(),
        "certifications": [c.to_dict() for c in certifications],
        "platform_certification": platform,
        "lifecycle": lifecycle,
        "blueprint_sections": list(BLUEPRINT_SECTIONS),
        "lifecycle_transitions": DOMAIN_LIFECYCLE_TRANSITIONS,
        "workspace_bindings": DOMAIN_WORKSPACE_TYPES,
        "shared_core": [s.to_dict() for s in shared_core_services()],
        "shared_core_names": list(SHARED_CORE_SERVICES),
        "certification_checks": list(CERTIFICATION_CHECKS),
        "source_roots": DOMAIN_SOURCE_ROOTS,
    }


def _lifecycle_snapshot(domain_code: str) -> dict[str, Any]:
    lifecycle = DomainLifecycle(domain_code)
    manifest = CANONICAL_DOMAINS.get(domain_code)
    try:
        lifecycle.install(manifest.version if manifest else "1.0.0")
        return {
            "state": lifecycle.state.value,
            "version": lifecycle.versions.latest.version if lifecycle.versions.latest else None,
            "history": [e.to_dict() for e in lifecycle.history],
        }
    except Exception as exc:  # pragma: no cover - defensive
        return {"state": "error", "error": str(exc)}
