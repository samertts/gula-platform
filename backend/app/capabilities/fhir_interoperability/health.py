from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/fhir-interoperability/health", tags=["health"])


@router.get("/")
async def health_check() -> dict:
    # Scaffolding must not answer "ok": a health probe that always passes
    # is not a probe. This router is mounted nowhere (NR-089).
    return {"status": "not_implemented", "capability": "fhir_interoperability", "version": "1.0.0"}


@router.get("/ready")
async def readiness() -> dict:
    return {"ready": False, "capability": "fhir_interoperability", "reason": "generated scaffolding"}
