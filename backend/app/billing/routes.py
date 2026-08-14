from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.claim import Claim
from app.security.dependencies import require_permission

from .models import BillingAuditEvent, BillingInvoice
from .schemas import (
    AlertResponse,
    AuditEventResponse,
    BillingSummaryResponse,
    ClaimResponse,
    CoverageCreate,
    CoverageResponse,
    InvoiceCreate,
    InvoiceResponse,
    PaymentResponse,
)
from .service import BillingService

router = APIRouter(prefix="/billing", tags=["GULA Billing & Insurance"])
DbSession = Annotated[Session, Depends(get_db)]


def _service(db: Session) -> BillingService:
    return BillingService(db)


def _commit(db: Session) -> None:
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def _invoice_response(invoice) -> InvoiceResponse:
    return InvoiceResponse(
        id=invoice.id,
        patient_id=invoice.patient_id,
        encounter_ref=invoice.encounter_ref,
        invoice_number=invoice.invoice_number,
        status=invoice.status,
        currency=invoice.currency,
        gross_amount=invoice.gross_amount,
        covered_amount=invoice.covered_amount,
        patient_due=invoice.patient_due,
        claim_reference=invoice.claim_reference,
        due_at=invoice.due_at,
        issued_at=invoice.issued_at,
        created_at=invoice.created_at,
        lines=invoice.lines,
        payments=invoice.payments,
    )


def _claim_response(claim: Claim) -> ClaimResponse:
    return ClaimResponse(
        id=claim.id,
        patient_id=claim.patient_id,
        order_id=claim.order_id,
        status=claim.status,
        total_amount=claim.total_amount,
        currency=claim.currency,
        external_ref=claim.external_ref,
        submitted_at=claim.submitted_at,
        created_at=claim.created_at,
        updated_at=claim.updated_at,
    )


@router.get("/summary", response_model=BillingSummaryResponse)
def get_summary(
    db: DbSession,
    current_user=Depends(require_permission("payments:read")),
):
    return _service(db).summary(lab_id=current_user.lab_id)


@router.get("/invoices", response_model=list[InvoiceResponse])
def list_invoices(
    db: DbSession,
    search: str | None = Query(default=None, max_length=128),
    current_user=Depends(require_permission("payments:read")),
):
    return [_invoice_response(invoice) for invoice in _service(db).list_invoices(lab_id=current_user.lab_id, search=search)]


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: int,
    db: DbSession,
    current_user=Depends(require_permission("payments:read")),
):
    invoice = db.query(BillingInvoice).filter(
        BillingInvoice.id == invoice_id,
        BillingInvoice.lab_id == current_user.lab_id,
    ).first()
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return _invoice_response(invoice)


@router.post("/invoices", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(
    payload: InvoiceCreate,
    response: Response,
    db: DbSession,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    request_id: Annotated[str | None, Header(alias="X-Request-ID")] = None,
    current_user=Depends(require_permission("payments:write")),
):
    try:
        invoice = _service(db).create_invoice(
            lab_id=current_user.lab_id,
            patient_id=payload.patient_id,
            encounter_ref=payload.encounter_ref,
            lines=[line.model_dump() for line in payload.lines],
            covered_amount=payload.covered_amount,
            due_at=payload.due_at,
            idempotency_key=idempotency_key,
            actor_user_id=current_user.id,
            request_id=request_id,
        )
        _commit(db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid billing request") from exc
    if idempotency_key:
        response.headers["Idempotency-Key"] = idempotency_key
    return _invoice_response(invoice)


@router.post("/invoices/{invoice_id}/simulate-settlement", response_model=InvoiceResponse)
def simulate_settlement(
    invoice_id: int,
    db: DbSession,
    request_id: Annotated[str | None, Header(alias="X-Request-ID")] = None,
    current_user=Depends(require_permission("payments:write")),
):
    try:
        invoice, _payment = _service(db).simulate_settlement(
            invoice_id=invoice_id,
            lab_id=current_user.lab_id,
            actor_user_id=current_user.id,
            request_id=request_id,
        )
        _commit(db)
    except ValueError as exc:
        if "not found" in str(exc):
            raise HTTPException(status_code=404, detail="Invoice not found") from exc
        raise HTTPException(status_code=400, detail="Invoice cannot be settled in its current state") from exc
    return _invoice_response(invoice)


@router.get("/claims", response_model=list[ClaimResponse])
def list_claims(
    db: DbSession,
    search: str | None = Query(default=None, max_length=128),
    current_user=Depends(require_permission("payments:read")),
):
    return [_claim_response(claim) for claim in _service(db).list_claims(lab_id=current_user.lab_id, search=search)]


@router.post("/claims/{claim_id}/advance", response_model=ClaimResponse)
def advance_claim(
    claim_id: int,
    db: DbSession,
    request_id: Annotated[str | None, Header(alias="X-Request-ID")] = None,
    current_user=Depends(require_permission("payments:write")),
):
    try:
        claim = _service(db).advance_claim(
            claim_id=claim_id,
            lab_id=current_user.lab_id,
            actor_user_id=current_user.id,
            request_id=request_id,
        )
        _commit(db)
    except ValueError as exc:
        if "not found" in str(exc):
            raise HTTPException(status_code=404, detail="Claim not found") from exc
        raise HTTPException(status_code=400, detail="Claim cannot advance in its current state") from exc
    return _claim_response(claim)


@router.get("/coverages", response_model=list[CoverageResponse])
def list_coverages(
    db: DbSession,
    search: str | None = Query(default=None, max_length=128),
    current_user=Depends(require_permission("payments:read")),
):
    return _service(db).list_coverages(lab_id=current_user.lab_id, search=search)


@router.post("/coverages", response_model=CoverageResponse, status_code=status.HTTP_201_CREATED)
def create_coverage(
    payload: CoverageCreate,
    db: DbSession,
    request_id: Annotated[str | None, Header(alias="X-Request-ID")] = None,
    current_user=Depends(require_permission("payments:write")),
):
    try:
        coverage = _service(db).create_coverage(
            lab_id=current_user.lab_id,
            patient_id=payload.patient_id,
            payer=payload.payer,
            plan=payload.plan,
            member_id=payload.member_id,
            expires_on=payload.expires_on,
            actor_user_id=current_user.id,
            request_id=request_id,
        )
        _commit(db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid coverage request") from exc
    return coverage


@router.post("/coverages/{coverage_id}/verify-local", response_model=CoverageResponse)
def verify_coverage_local(
    coverage_id: int,
    db: DbSession,
    request_id: Annotated[str | None, Header(alias="X-Request-ID")] = None,
    current_user=Depends(require_permission("payments:write")),
):
    try:
        coverage = _service(db).verify_coverage(
            coverage_id=coverage_id,
            lab_id=current_user.lab_id,
            actor_user_id=current_user.id,
            request_id=request_id,
        )
        _commit(db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Coverage not found") from exc
    return coverage


@router.get("/payments", response_model=list[PaymentResponse])
def list_payments(
    db: DbSession,
    current_user=Depends(require_permission("payments:read")),
):
    return _service(db).list_payments(lab_id=current_user.lab_id)


@router.get("/alerts", response_model=list[AlertResponse])
def list_alerts(
    db: DbSession,
    current_user=Depends(require_permission("payments:read")),
):
    return _service(db).alerts(lab_id=current_user.lab_id)


@router.get("/audit-events", response_model=list[AuditEventResponse])
def list_audit_events(
    db: DbSession,
    current_user=Depends(require_permission("audit:read")),
    limit: int = Query(default=100, ge=1, le=500),
):
    return (
        db.query(BillingAuditEvent)
        .filter(BillingAuditEvent.lab_id == current_user.lab_id)
        .order_by(BillingAuditEvent.created_at.desc())
        .limit(limit)
        .all()
    )
