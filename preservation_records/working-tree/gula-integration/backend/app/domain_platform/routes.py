"""PROGRAM-STABLE-004 — Domain Platform Framework API.

Public REST surface for the Domain Platform Framework. Every Domain is
installed, activated, suspended, upgraded, rolled back, backed up, restored,
health-checked, measured, and certified through this API. Cross-domain
contracts and the Domain <-> Workspace binding are enforced here too.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_niam_db as get_db
from app.domain_platform.services import DomainError, DomainService
from app.identity.security import get_current_identity

router = APIRouter(
    prefix="/niam/domains",
    tags=["Domain Platform"],
    dependencies=[Depends(get_current_identity)],
)


def _service(db: AsyncSession = Depends(get_db)) -> DomainService:
    return DomainService(db)


@router.get("")
async def list_domains(service: DomainService = Depends(_service)):
    registrations = await service.list_registrations()
    return {
        "count": len(registrations),
        "domains": [r.to_dict() for r in registrations],
    }


@router.get("/canonical")
async def canonical_domains(service: DomainService = Depends(_service)):
    manifests = service.canonical_domains()
    return {"count": len(manifests), "domains": [m.to_dict() for m in manifests]}


@router.post("/register/{code}")
async def register_domain(code: str, service: DomainService = Depends(_service)):
    try:
        registration = await service.register_domain(code)
    except DomainError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return registration.to_dict()


@router.get("/{code}")
async def get_domain(code: str, service: DomainService = Depends(_service)):
    registration = await service.get_registration(code)
    if not registration:
        raise HTTPException(status_code=404, detail="domain_not_registered")
    return registration.to_dict()


@router.post("/{code}/activate")
async def activate_domain(code: str, service: DomainService = Depends(_service)):
    try:
        registration = await service.activate(code)
    except (DomainError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return registration.to_dict()


@router.post("/{code}/suspend")
async def suspend_domain(code: str, service: DomainService = Depends(_service)):
    try:
        registration = await service.suspend(code)
    except (DomainError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return registration.to_dict()


@router.post("/{code}/upgrade")
async def upgrade_domain(
    code: str, new_version: str, service: DomainService = Depends(_service)
):
    try:
        registration = await service.upgrade(code, new_version)
    except (DomainError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return registration.to_dict()


@router.post("/{code}/rollback")
async def rollback_domain(code: str, service: DomainService = Depends(_service)):
    try:
        registration = await service.rollback(code)
    except (DomainError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return registration.to_dict()


@router.get("/{code}/versions")
async def domain_versions(code: str, service: DomainService = Depends(_service)):
    try:
        versions = await service.list_versions(code)
    except DomainError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"domain": code, "versions": [v.to_dict() for v in versions]}


@router.get("/{code}/binding")
async def domain_binding(code: str, service: DomainService = Depends(_service)):
    try:
        binding = await service.get_binding(code)
    except DomainError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if not binding:
        raise HTTPException(status_code=404, detail="binding_not_found")
    return binding.to_dict()


@router.post("/contracts")
async def register_contract(
    contract_id: str,
    provider_domain: str,
    consumer_domain: str,
    kind: str,
    version: str,
    endpoint: str,
    documentation_url: str,
    summary: str = "",
    service: DomainService = Depends(_service),
):
    try:
        record = await service.register_contract(
            contract_id=contract_id,
            provider_domain=provider_domain,
            consumer_domain=consumer_domain,
            kind=kind,
            version=version,
            endpoint=endpoint,
            documentation_url=documentation_url,
            summary=summary,
        )
    except (DomainError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return record.to_dict()


@router.get("/{code}/contracts")
async def domain_contracts(code: str, service: DomainService = Depends(_service)):
    try:
        contracts = await service.list_contracts(code)
    except DomainError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"domain": code, "contracts": [c.to_dict() for c in contracts]}


@router.get("/{code}/health")
async def domain_health(code: str, service: DomainService = Depends(_service)):
    try:
        return await service.health_check(code)
    except DomainError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{code}/metrics")
async def domain_metrics(code: str, service: DomainService = Depends(_service)):
    try:
        return await service.metrics(code)
    except DomainError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{code}/certify")
async def certify_domain(code: str, service: DomainService = Depends(_service)):
    try:
        return await service.certify(code)
    except (DomainError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{code}/history")
async def domain_history(code: str, service: DomainService = Depends(_service)):
    try:
        events = await service.lifecycle_history(code)
    except DomainError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"domain": code, "events": [e.to_dict() for e in events]}
