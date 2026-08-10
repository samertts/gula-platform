"""Governance — authority boundaries, councils, approvals, appeals.

Exposes the authority-boundary model (A3) alongside the existing governance
registry.
"""

from app.identity.governance.boundaries import (
    AUTHORITY_BOUNDARY_TYPE_MAP,
    DEFAULT_BOUNDARY_TYPE,
    PRIVILEGED_ACTION_POLICY,
    AuthorityBoundary,
    AuthorityBoundaryConflict,
    AuthorityBoundaryDecision,
    AuthorityBoundaryError,
    AuthorityBoundaryService,
    AuthorityBoundaryType,
    boundary_for_authority,
    boundary_type_for,
)
from app.identity.governance.models import IdentityAuthority

__all__ = [
    "AUTHORITY_BOUNDARY_TYPE_MAP",
    "DEFAULT_BOUNDARY_TYPE",
    "PRIVILEGED_ACTION_POLICY",
    "AuthorityBoundary",
    "AuthorityBoundaryConflict",
    "AuthorityBoundaryDecision",
    "AuthorityBoundaryError",
    "AuthorityBoundaryService",
    "AuthorityBoundaryType",
    "IdentityAuthority",
    "boundary_for_authority",
    "boundary_type_for",
]
