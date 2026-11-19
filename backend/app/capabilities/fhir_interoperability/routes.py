from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.lab_user import LabUser
from ...security.dependencies import require_institutional_permission
from .schemas import (
    FHIRCapabilityStatement,
    FHIRResourceInput,
    FHIRResourceListResponse,
    FHIRResourceResponse,
    FHIRSearchRequest,
    HL7ConversionRequest,
    HL7ConversionResponse,
    FHIR_RESOURCE_TYPES,
)
from .hl7 import HL7ConversionError, parse_oru_r01, to_fhir_bundle
from .service import create_resource, get_resource, search_resources

router = APIRouter(prefix="/fhir-interoperability", tags=["FHIR Interoperability"])


def _assert_resource_type(resource_type: str) -> None:
    if resource_type not in FHIR_RESOURCE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported FHIR resource type: {resource_type}",
        )


def _read_actor() -> LabUser:
    return Depends(require_institutional_permission("lab:read"))


def _write_actor() -> LabUser:
    return Depends(require_institutional_permission("lab:manage"))


@router.get("/health/", include_in_schema=False)
async def health() -> dict[str, str]:
    return {"status": "ok", "capability": "fhir_interoperability"}


@router.get("/metadata", response_model=FHIRCapabilityStatement)
def capability_metadata() -> FHIRCapabilityStatement:
    return FHIRCapabilityStatement(supportedResourceTypes=list(FHIR_RESOURCE_TYPES))


@router.get("/", response_model=dict)
def list_supported_resources(
    skip: int = 0,
    limit: int = 100,
    _actor: LabUser = _read_actor(),
) -> dict:
    resources = list(FHIR_RESOURCE_TYPES)[skip : skip + min(limit, 200)]
    return {
        "items": [{"resourceType": resource_type} for resource_type in resources],
        "total": len(FHIR_RESOURCE_TYPES),
        "skip": skip,
        "limit": limit,
    }


@router.post(
    "/hl7/convert",
    response_model=HL7ConversionResponse,
)
def convert_hl7_to_fhir(
    payload: HL7ConversionRequest,
    _actor: LabUser = _write_actor(),
) -> dict:
    # IA-064. to_fhir_bundle was called outside this block, so its own identity
    # guards would have surfaced as a 500. A message that cannot be converted
    # is the client's malformed input, not a server fault.
    try:
        message = parse_oru_r01(payload.message)
        bundle = to_fhir_bundle(message)
    except HL7ConversionError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return {
        "messageType": message.message_type,
        "resourceCount": len(bundle["entry"]),
        "simulationOnly": True,
        "bundle": bundle,
    }


@router.post(
    "/resources",
    response_model=FHIRResourceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_fhir_resource(
    payload: FHIRResourceInput,
    actor: LabUser = _write_actor(),
    db: Session = Depends(get_db),
    source_system: str | None = Header(default=None, alias="X-GULA-Source"),
) -> dict:
    try:
        return create_resource(
            db,
            lab_id=actor.lab_id,
            created_by=actor.id,
            payload=payload,
            source_system=source_system,
        )
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A FHIR resource with this id and version already exists in this institution",
        ) from exc


@router.get(
    "/resources/{resource_type}",
    response_model=FHIRResourceListResponse,
)
def search_fhir_resources(
    resource_type: str,
    query: FHIRSearchRequest = Depends(),
    actor: LabUser = _read_actor(),
    db: Session = Depends(get_db),
) -> dict:
    _assert_resource_type(resource_type)
    total, entries = search_resources(
        db,
        lab_id=actor.lab_id,
        resource_type=resource_type,
        subject=query.subject,
        patient=query.patient,
        limit=query.limit,
        offset=query.offset,
    )
    return {"total": total, "entry": entries}


@router.get(
    "/resources/{resource_type}/{resource_id}",
    response_model=FHIRResourceResponse,
)
def read_fhir_resource(
    resource_type: str,
    resource_id: str,
    actor: LabUser = _read_actor(),
    db: Session = Depends(get_db),
) -> dict:
    _assert_resource_type(resource_type)
    resource = get_resource(
        db,
        lab_id=actor.lab_id,
        resource_type=resource_type,
        resource_id=resource_id,
    )
    if resource is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FHIR resource not found")
    return resource
