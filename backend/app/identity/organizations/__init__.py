"""Organization administration guard — PROGRAM-STABLE-003 Phase 3.

Enforces zero cross-domain administration: organization owners may only
administer the organization they belong to. Reusable by any identity
administrative surface.
"""

from __future__ import annotations

from app.identity.organizations.guard import (
    OrganizationAccessDecision,
    OrganizationAccessDeniedError,
    OrganizationAccessGuard,
)

__all__ = [
    "OrganizationAccessDecision",
    "OrganizationAccessDeniedError",
    "OrganizationAccessGuard",
]
