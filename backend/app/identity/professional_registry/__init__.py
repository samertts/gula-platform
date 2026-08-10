"""National Professional Registry — PROGRAM-STABLE-003 Phase 4 + Wave A (A4).

Professional permissions become active ONLY after verification by the
responsible authority. Clinical privileges are never activated automatically.

A4 adds the separable authorization layer: operational privilege records
(scope/duration/lifecycle) derived from verified registry entries, keeping the
identity layer (registry entry) distinct from the privilege layer
(authorization).
"""

from __future__ import annotations

from app.identity.professional_registry.authorization import (
    AuthorizationError,
    ProfessionalAuthorizationService,
    ScopeError,
    scope_matches,
    validate_scope,
)
from app.identity.professional_registry.models import (
    PROFESSION_CATEGORIES,
    AuthorizationScopeType,
    AuthorizationStatus,
    ProfessionalAuthorization,
    ProfessionalRegistryEntry,
)
from app.identity.professional_registry.services import (
    ProfessionalRegistryService,
    RegistryError,
    VerificationRequiredError,
)

__all__ = [
    "PROFESSION_CATEGORIES",
    "AuthorizationError",
    "AuthorizationScopeType",
    "AuthorizationStatus",
    "ProfessionalAuthorization",
    "ProfessionalAuthorizationService",
    "ProfessionalRegistryEntry",
    "ProfessionalRegistryService",
    "RegistryError",
    "ScopeError",
    "VerificationRequiredError",
    "scope_matches",
    "validate_scope",
]
