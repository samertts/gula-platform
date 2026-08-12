"""Master Patient Index — national-layer identity service.

See architecture/FOUNDATION.md for the boundary contract.

Public surface:
  - router:           FastAPI router (wired in app/main.py)
  - resolve_identity: programmatic entry for non-HTTP callers
  - merge_citizens:   admin-level merge operation
  - Citizen, IdentityClaim, MergeAudit: SQLAlchemy models
"""

from .models import Citizen, IdentityClaim, MergeAudit
from .resolver import merge_citizens, resolve_identity


def __getattr__(name):
    if name == "router":
        from .api import router
        return router
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "Citizen",
    "IdentityClaim",
    "MergeAudit",
    "merge_citizens",
    "resolve_identity",
    "router",
]
