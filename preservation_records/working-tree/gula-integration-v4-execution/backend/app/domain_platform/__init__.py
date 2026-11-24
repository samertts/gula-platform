"""PROGRAM-STABLE-004 — Domain Platform Framework.

The permanent Domain Platform Framework for every current and future GULA
module. Every healthcare specialty is an independent Domain that inherits
this framework while enforcing:

  * Domain Sovereignty
  * Shared Core
  * Zero Cross-Domain Administration
  * Zero Cross-Domain Database Access
  * Zero Business Logic Duplication

Domains: laboratory, pharmacy, radiology, hospital, blood_bank,
public_health, insurance, emergency, research, citizen_portal,
provider_portal — and any future healthcare specialty.
"""

from __future__ import annotations


def get_router():
    from .routes import router as _router

    return _router


__all__ = ["get_router"]
