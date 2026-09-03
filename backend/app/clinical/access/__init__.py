"""Canonical Clinical Access and Sharing Core (Slice 05)."""

from .models import CoreAccessGrant, CoreAccessHistory
from .routes import router
from .service import AccessService

__all__ = ["AccessService", "CoreAccessGrant", "CoreAccessHistory", "router"]
