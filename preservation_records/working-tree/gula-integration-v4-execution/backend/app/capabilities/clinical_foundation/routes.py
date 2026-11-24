from __future__ import annotations

from app.capabilities._shared.routes import build_crud_router

# Real CRUD backed by capability_records; generated handlers use distinct
# operation IDs and are isolated by the "clinical_foundation" capability namespace.
router = build_crud_router(
    "clinical_foundation",
    "/clinical-foundation",
    ["Clinical Foundation"],
)
