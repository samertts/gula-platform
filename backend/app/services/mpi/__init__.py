"""Master Patient Index — national-layer identity service.

See architecture/FOUNDATION.md for the boundary contract.

Public surface:
  - router:           FastAPI router (wired in app/main.py)
  - resolve_identity: programmatic entry for non-HTTP callers
  - merge_citizens:   admin-level merge operation
  - Citizen, IdentityClaim, MergeAudit: SQLAlchemy models
"""

from .api import router
from .models import Citizen, IdentityClaim, MergeAudit
from .resolver import merge_citizens, resolve_identity

__all__ = [
    "Citizen",
    "IdentityClaim",
    "MergeAudit",
    "merge_citizens",
    "resolve_identity",
    "router",
]
