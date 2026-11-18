"""Fail-closed synthetic authorization for the T6 HTTP evidence surface.

This is NOT a production identity system. A test client supplies a synthetic
principal through explicit headers; the dependency then enforces three rules:

1. no principal ....................... 401 (``login``)
2. missing scope or tenant/facility claim ... 403 (``denied``)
3. resource outside the claimed tenant/facility ... 403 (``denied``)

All denials are structured ``OperationOutcome`` bodies. No supplied token,
NID, identifier or claim value is echoed in a reason string, so a denial can
never become an identifier-leak sink. The value returned by the dependency is
an ``Authorization`` object rather than an exception because this router is
mounted with ``app.include_router(router)`` only and therefore cannot register
an application-level exception handler.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from fastapi import Header

from app.health_core.common import is_synthetic_id
from app.health_core.fhir.support import EXT_TENANT
from app.interoperability.fhir_http.errors import ErrorBody, forbidden, unauthenticated

__all__ = [
    "EXT_FACILITY",
    "READ_SCOPE",
    "WRITE_SCOPE",
    "Authorization",
    "Principal",
    "assert_resource_scope",
    "authorize_read",
    "authorize_write",
]

READ_SCOPE: Final[str] = "fhir.read"
WRITE_SCOPE: Final[str] = "fhir.write"

#: Local extension used only by this evidence surface to carry the synthetic
#: facility claim alongside the canonical Health Core tenant extension.
EXT_FACILITY: Final[str] = "urn:gula:synthetic:fhir:R4:extension/facility"


@dataclass(frozen=True, slots=True)
class Principal:
    """A fully claimed synthetic principal. Never carries real identity data."""

    subject: str
    scopes: frozenset[str]
    tenant_id: str
    facility_id: str


@dataclass(frozen=True, slots=True)
class Authorization:
    """Either an authorised principal or a client-safe denial (never both)."""

    principal: Principal | None = None
    error: ErrorBody | None = None

    @property
    def ok(self) -> bool:
        """Return whether this authorization may proceed."""
        return self.principal is not None and self.error is None


def _extension_code(resource: dict[str, object], url: str) -> str | None:
    """Read a synthetic ``valueCode`` extension without raising or echoing."""
    extensions = resource.get("extension")
    if not isinstance(extensions, list):
        return None
    for item in extensions:
        if isinstance(item, dict) and item.get("url") == url:
            value = item.get("valueCode")
            if isinstance(value, str) and value:
                return value
    return None


def _authorize(
    required_scope: str,
    subject: str | None,
    scopes: str | None,
    tenant_id: str | None,
    facility_id: str | None,
) -> Authorization:
    """Apply the three fail-closed authorization rules without leaking claims."""
    if not subject or not subject.strip():
        return Authorization(error=unauthenticated())

    granted = frozenset(
        piece.strip() for piece in (scopes or "").split(",") if piece.strip()
    )
    if required_scope not in granted:
        return Authorization(error=forbidden("Principal lacks the required FHIR scope"))

    if not tenant_id or not facility_id:
        return Authorization(error=forbidden("Principal lacks a tenant or facility claim"))
    # Synthetic shape checks are claim-shape checks, not value echoes. A malformed
    # claim is rejected with a generic reason and never reflected in diagnostics.
    if not is_synthetic_id(tenant_id) or not is_synthetic_id(facility_id):
        return Authorization(error=forbidden("Principal claims are not synthetic references"))

    return Authorization(
        principal=Principal(
            subject=subject.strip(),
            scopes=granted,
            tenant_id=tenant_id.strip(),
            facility_id=facility_id.strip(),
        )
    )


async def authorize_read(
    x_gula_principal: str | None = Header(default=None, alias="X-GULA-Principal"),
    x_gula_scopes: str | None = Header(default=None, alias="X-GULA-Scopes"),
    x_gula_tenant: str | None = Header(default=None, alias="X-GULA-Tenant"),
    x_gula_facility: str | None = Header(default=None, alias="X-GULA-Facility"),
) -> Authorization:
    """Require an explicit ``fhir.read`` scope and complete tenant/facility claims."""
    return _authorize(READ_SCOPE, x_gula_principal, x_gula_scopes, x_gula_tenant, x_gula_facility)


async def authorize_write(
    x_gula_principal: str | None = Header(default=None, alias="X-GULA-Principal"),
    x_gula_scopes: str | None = Header(default=None, alias="X-GULA-Scopes"),
    x_gula_tenant: str | None = Header(default=None, alias="X-GULA-Tenant"),
    x_gula_facility: str | None = Header(default=None, alias="X-GULA-Facility"),
) -> Authorization:
    """Require an explicit ``fhir.write`` scope and complete tenant/facility claims."""
    return _authorize(WRITE_SCOPE, x_gula_principal, x_gula_scopes, x_gula_tenant, x_gula_facility)


def assert_resource_scope(principal: Principal, resource: dict[str, object]) -> ErrorBody | None:
    """Deny access to a resource outside the principal's tenant/facility scope."""
    resource_tenant = _extension_code(resource, EXT_TENANT)
    resource_facility = _extension_code(resource, EXT_FACILITY)
    if resource_tenant is None or resource_facility is None:
        return forbidden("Resource has no synthetic tenant or facility scope")
    if resource_tenant != principal.tenant_id or resource_facility != principal.facility_id:
        return forbidden("Resource is outside the authenticated tenant or facility scope")
    return None
