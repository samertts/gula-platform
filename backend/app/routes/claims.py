"""Claims / Insurance endpoints.

Endpoints:
    POST   /claims                      — create a new claim (draft)
    POST   /claims/{claim_id}/validate  — validate a draft claim
    POST   /claims/{claim_id}/submit    — submit a validated claim to insurer
    GET    /claims/{claim_id}           — get claim details

All endpoints require authentication. All service calls filter by
current_user.lab_id (security invariant).
"""
from app.services.route_audit import audit_route_mutation

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.claim import Claim
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user
from ..services import claims_service

router = APIRouter(prefix="/claims", tags=["claims"])


# ─── Pydantic schemas ─────────────────────────────────────────────────────────


class ClaimItemCreate(BaseModel):
    test_code: str
    description: str | None = None
    quantity: int = Field(default=1, ge=1)
    unit_price: Decimal = Field(..., gt=0)
    amount: Decimal = Field(..., gt=0)


class ClaimCreate(BaseModel):
    patient_id: int
    order_id: int | None = None
    items: list[ClaimItemCreate] = Field(..., min_length=1)
    idempotency_key: str | None = None


class ClaimItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    claim_id: int
    test_code: str
    description: str | None
    quantity: int
    unit_price: Decimal
    amount: Decimal


class ClaimResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lab_id: int
    patient_id: int
    order_id: int | None
    status: str
    total_amount: Decimal | None
    currency: str
    idempotency_key: str | None
    external_ref: str | None
    submitted_at: str | None
    created_at: str | None
    updated_at: str | None
    items: list[ClaimItemResponse]


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _claim_to_response(claim: Claim) -> ClaimResponse:
    return ClaimResponse(
        id=claim.id,
        lab_id=claim.lab_id,
        patient_id=claim.patient_id,
        order_id=claim.order_id,
        status=claim.status,
        total_amount=claim.total_amount,
        currency=claim.currency,
        idempotency_key=claim.idempotency_key,
        external_ref=claim.external_ref,
        submitted_at=claim.submitted_at.isoformat() if claim.submitted_at else None,
        created_at=claim.created_at.isoformat() if claim.created_at else None,
        updated_at=claim.updated_at.isoformat() if claim.updated_at else None,
        items=[
            ClaimItemResponse(
                id=item.id,
                claim_id=item.claim_id,
                test_code=item.test_code,
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                amount=item.amount,
            )
            for item in claim.items
        ],
    )


# ─── Endpoints ────────────────────────────────────────────────────────────────


@audit_route_mutation(action="route.create_claim", resource_type="claims")
@router.post("", status_code=201, response_model=ClaimResponse)
def create_claim(
    data: ClaimCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new insurance claim in 'draft' status."""
    if not data.items:
        raise HTTPException(status_code=400, detail="At least one claim item is required")

    items_dicts = [item.model_dump() for item in data.items]

    try:
        claim = claims_service.create_claim(
            db=db,
            lab_id=current_user.lab_id,
            patient_id=data.patient_id,
            items=items_dicts,
            order_id=data.order_id,
            idempotency_key=data.idempotency_key,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Resource not found") from exc

    return _claim_to_response(claim)


@router.post("/{claim_id}/validate", response_model=ClaimResponse)
def validate_claim(
    claim_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Validate a draft claim (draft → validated)."""
    try:
        claim = claims_service.validate_claim(
            db=db,
            claim_id=claim_id,
            lab_id=current_user.lab_id,
        )
    except ValueError as exc:
        msg = str(exc)
        if "not found" in msg:
            raise HTTPException(status_code=404, detail="Resource not found") from exc
        raise HTTPException(status_code=400, detail="Invalid request") from exc

    return _claim_to_response(claim)


@router.post("/{claim_id}/submit", response_model=ClaimResponse)
def submit_claim(
    claim_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit a validated claim to the insurance system (validated → submitted)."""
    try:
        claim = claims_service.submit_claim(
            db=db,
            claim_id=claim_id,
            lab_id=current_user.lab_id,
        )
    except ValueError as exc:
        msg = str(exc)
        if "not found" in msg:
            raise HTTPException(status_code=404, detail="Resource not found") from exc
        raise HTTPException(status_code=400, detail="Invalid request") from exc

    return _claim_to_response(claim)


@router.get("/{claim_id}", response_model=ClaimResponse)
def get_claim(
    claim_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get claim details. Only accessible within the same lab."""
    try:
        claim = claims_service.get_claim(
            db=db,
            claim_id=claim_id,
            lab_id=current_user.lab_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Resource not found") from exc

    return _claim_to_response(claim)
