"""Country-agnostic Citizen Registry — PROGRAM-STABLE-003 Phase 5.

Configurable identity providers; nothing is hard-coded to a specific country.
"""

from __future__ import annotations

from app.identity.citizen_registry.services import (
    CitizenRegistryError,
    CitizenRegistryService,
    ProviderDisabledError,
    UnsupportedIdentifierTypeError,
)

__all__ = [
    "CitizenRegistryError",
    "CitizenRegistryService",
    "ProviderDisabledError",
    "UnsupportedIdentifierTypeError",
]
