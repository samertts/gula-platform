"""National Professional Registry — PROGRAM-STABLE-003 Phase 4.

Professional permissions become active ONLY after verification by the
responsible authority. Clinical privileges are never activated automatically.
"""

from __future__ import annotations

from app.identity.professional_registry.services import (
    ProfessionalRegistryService,
    RegistryError,
    VerificationRequiredError,
)

__all__ = [
    "ProfessionalRegistryService",
    "RegistryError",
    "VerificationRequiredError",
]
