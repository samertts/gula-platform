"""
Reference Implementation — GULA Architecture-Conformant Patterns.

This package demonstrates COMPLIANT layering per the Platform Constitution.
Every layer respects strict dependency direction:

    Routes → Services → Domain → (no outward deps)
                     ↓
              Infrastructure (wires everything)

Rules enforced:
  - Domain:      zero framework imports (no FastAPI, SQLAlchemy, Pydantic)
  - Services:    import only from domain
  - Routes:      import only from services (via FastAPI Depends())
  - Infra:       only layer with SQLAlchemy / FastAPI wiring

Use these modules as the canonical example when adding new features.

All internal imports use ``app.reference`` prefix to match the monorepo's
established import convention (see ``app/routes/`` and ``app/services/``).
"""

from __future__ import annotations
