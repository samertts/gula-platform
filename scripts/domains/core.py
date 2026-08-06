"""PROGRAM-STABLE-004 — Domain Platform Engine (GULA-DOMAIN-001).

The permanent governance engine for the Domain Platform Framework. It scans
the real GULA codebase, validates Domain Sovereignty, and publishes the
official Domain Platform documents:

  DOMAIN_FRAMEWORK.md
  DOMAIN_BLUEPRINT.md
  DOMAIN_CONTRACTS.md
  DOMAIN_ISOLATION_CERTIFICATION.md
  DOMAIN_LIFECYCLE.md
  DOMAIN_VERSIONING.md
  DOMAIN_REGISTRY.md

The engine shares ONE implementation with the runtime framework in
``backend/app/domain_platform`` — it never duplicates business logic or
infrastructure. It adds only codebase scanning and report rendering.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = REPO_ROOT / "backend"

DOMAINS_DIR = REPO_ROOT / ".ai" / "core" / "domains"
STATE_DIR = DOMAINS_DIR / "state"
DOCS_DIR = REPO_ROOT / "docs" / "domains"

# The official output documents (repo root, matching the other program docs).
OUTPUT_DOCS: dict[str, str] = {
    "DOMAIN_FRAMEWORK.md": "Domain Platform Framework — architecture, sovereignty, and governance",
    "DOMAIN_BLUEPRINT.md": "Domain Blueprint — the official structure every Domain must follow",
    "DOMAIN_CONTRACTS.md": "Cross-Domain Contracts — the only legal communication channels",
    "DOMAIN_ISOLATION_CERTIFICATION.md": "Domain Isolation Certification — Phase 3 + Phase 7 validation",
    "DOMAIN_LIFECYCLE.md": "Domain Lifecycle — install, activate, suspend, upgrade, rollback, backup, restore",
    "DOMAIN_VERSIONING.md": "Domain Versioning — independent SemVer releases with backward compatibility",
    "DOMAIN_REGISTRY.md": "Domain Registry — the canonical catalog of every GULA Domain",
}

# Domain code -> backend source roots (packages) that own its modules.
DOMAIN_SOURCE_ROOTS: dict[str, tuple[str, ...]] = {
    "laboratory": ("app/lims",),
    "pharmacy": ("app/pharmacy",),
    "radiology": ("app/radiology",),
    "hospital": ("app/hospital",),
    "blood_bank": ("app/blood_bank",),
    "public_health": ("app/public_health",),
    "insurance": ("app/insurance",),
    "emergency": ("app/ems", "app/critical_care"),
    "research": ("app/research_platform", "app/biomedical"),
    "citizen_portal": ("app/citizen_platform",),
    "provider_portal": ("app/identity/professional_registry",),
}

# Files excluded from module scanning (never domain-owned).
_EXCLUDED_SUFFIXES = ("__init__.py", "test_", "_test")


@dataclass(frozen=True)
class DomainModule:
    """A module owned by a Domain (resolved from the real codebase)."""

    domain_code: str
    module: str  # e.g. "app/lims/models.py"

    def to_dict(self) -> dict[str, Any]:
        return {"domain_code": self.domain_code, "module": self.module}


def resolve_domain_modules() -> dict[str, list[str]]:
    """Resolve the real module list owned by every Domain.

    The module list drives isolation scanning. Only blueprint-bearing
    modules are included; package init files are excluded.
    """
    resolved: dict[str, list[str]] = {}
    for domain_code, roots in DOMAIN_SOURCE_ROOTS.items():
        modules: list[str] = []
        for root in roots:
            base = BACKEND_DIR / root
            if not base.exists():
                continue
            for path in sorted(base.rglob("*.py")):
                name = path.name
                if name.startswith("_") and not name.endswith("__init__.py"):
                    continue
                if any(name.startswith(s) for s in _EXCLUDED_SUFFIXES):
                    continue
                if name == "__init__.py":
                    continue
                rel = path.relative_to(BACKEND_DIR).as_posix()
                modules.append(rel)
        resolved[domain_code] = sorted(modules)
    return resolved


def read_module_source(module: str) -> str:
    """Read a module's source from the backend tree (empty when absent)."""
    path = BACKEND_DIR / module
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""
