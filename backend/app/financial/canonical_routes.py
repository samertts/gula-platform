from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.orm import Session

from app.clinical.appointments.routes import (
    _actor_rate_limit,
    _correlation_id,
    _handle_error,
    _require_idempotency_key,
    _require_if_match,
)
from app.database import get_db
from app.identity.api.workspaces import NiamActor, get_current_niam_actor_sync

from .canonical_schemas import (
    BillCreateRequest,
    ClaimCreateRequest,
    CoverageCreateRequest,
    EligibilityCreateRequest,
    PayerCreateRequest,
    PaymentCaptureRequest,
    PaymentCreateRequest,
    PreauthorizationCreateRequest,
    PriceCreateRequest,
    RefundCreateRequest,
    ServiceCreateRequest,
    WorkflowRequest,
)
from .canonical_service import CanonicalFinancialService

router = APIRouter(tags=["Canonical Financial Core"])


def _run(request: Request, actor: NiamActor, db: Session, operation: str, target_type: str, target_id: str | None, workspace_id: str, callback: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    _actor_rate_limit(request, actor)
    try:
        result = callback()
        db.commit()
        return result
    except Exception as exc:
        _handle_error(exc, db=db, actor=actor, request=request, operation=operation, target_type=target_type, target_id=target_id, workspace_id=workspace_id)
        raise AssertionError("unreachable") from exc


def _key(value: str | None) -> str:
    return _require_idempotency_key(value)


def _service(db):
    return CanonicalFinancialService(db)


@router.post("/api/v1/finance/payers", status_code=status.HTTP_201_CREATED)
def create_payer(body: PayerCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    key = _key(idempotency_key)
    return _run(request, actor, db, "finance.payer.create", "financial_payer", None, body.workspace_id, lambda: _service(db).create_payer(actor, workspace_id=body.workspace_id, name=body.name, payer_type=body.payer_type, jurisdiction=body.jurisdiction, key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/finance/coverages", status_code=status.HTTP_201_CREATED)
def create_coverage(body: CoverageCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    key = _key(idempotency_key)
    return _run(request, actor, db, "finance.coverage.create", "financial_coverage", None, body.workspace_id, lambda: _service(db).create_coverage(actor, workspace_id=body.workspace_id, member_id=body.member_id, payer_id=body.payer_id, plan_code=body.plan_code, valid_from=body.valid_from, valid_to=body.valid_to, key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/finance/eligibility/check", status_code=status.HTTP_201_CREATED)
def check_eligibility(body: EligibilityCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    key = _key(idempotency_key)
    return _run(request, actor, db, "finance.eligibility.check", "financial_eligibility", None, body.workspace_id, lambda: _service(db).check_eligibility(actor, workspace_id=body.workspace_id, coverage_id=body.coverage_id, service_id=body.service_id, synthetic_outcome=body.synthetic_outcome, key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/finance/preauthorizations", status_code=status.HTTP_201_CREATED)
def create_preauthorization(body: PreauthorizationCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    key = _key(idempotency_key)
    return _run(request, actor, db, "finance.preauth.create", "financial_preauthorization", None, body.workspace_id, lambda: _service(db).create_preauthorization(actor, workspace_id=body.workspace_id, member_id=body.member_id, payer_id=body.payer_id, service_id=body.service_id, encounter_id=body.encounter_id, clinical_indication=body.clinical_indication, estimated_amount_minor=body.estimated_amount_minor, currency=body.currency, key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/finance/services", status_code=status.HTTP_201_CREATED)
def create_service(body: ServiceCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    key = _key(idempotency_key)
    return _run(request, actor, db, "finance.service.create", "financial_service", None, body.workspace_id, lambda: _service(db).create_service(actor, workspace_id=body.workspace_id, code=body.code, name=body.name, specialty=body.specialty, currency=body.currency, key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/finance/prices", status_code=status.HTTP_201_CREATED)
def create_price(body: PriceCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    key = _key(idempotency_key)
    return _run(request, actor, db, "finance.price.create", "financial_service_price", None, body.workspace_id, lambda: _service(db).create_price(actor, workspace_id=body.workspace_id, service_id=body.service_id, amount_minor=body.amount_minor, currency=body.currency, valid_from=body.valid_from, valid_to=body.valid_to, key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/finance/bills", status_code=status.HTTP_201_CREATED)
def create_bill(body: BillCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    key = _key(idempotency_key)
    return _run(request, actor, db, "finance.bill.create", "financial_bill", None, body.workspace_id, lambda: _service(db).create_bill(actor, workspace_id=body.workspace_id, patient_person_id=body.patient_person_id, encounter_id=body.encounter_id, currency=body.currency, items=body.items, coverage_id=body.coverage_id, discount_minor=body.discount_minor, key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/finance/claims", status_code=status.HTTP_201_CREATED)
def create_claim(body: ClaimCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    key = _key(idempotency_key)
    return _run(request, actor, db, "finance.claim.create", "financial_claim", None, body.workspace_id, lambda: _service(db).create_claim(actor, workspace_id=body.workspace_id, bill_id=body.bill_id, payer_id=body.payer_id, key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/finance/claims/{claim_id}/transition")
def transition_claim(claim_id: str, body: WorkflowRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")):
    key = _key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "finance.claim.transition", "financial_claim", claim_id, body.workspace_id, lambda: _service(db).transition_claim(actor, workspace_id=body.workspace_id, claim_id=claim_id, target_status=body.target_status, expected_version=expected, key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/finance/payments", status_code=status.HTTP_201_CREATED)
def create_payment(body: PaymentCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    key = _key(idempotency_key)
    return _run(request, actor, db, "finance.payment.create", "financial_payment", None, body.workspace_id, lambda: _service(db).create_payment(actor, workspace_id=body.workspace_id, bill_id=body.bill_id, amount_minor=body.amount_minor, currency=body.currency, provider=body.provider, provider_available=body.provider_available, key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/finance/payments/{payment_id}/capture")
def capture_payment(payment_id: str, body: PaymentCaptureRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")):
    key = _key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "finance.payment.capture", "financial_payment", payment_id, body.workspace_id, lambda: _service(db).capture_payment(actor, workspace_id=body.workspace_id, payment_id=payment_id, event_id=body.event_id, nonce=body.nonce, occurred_at=body.occurred_at, expected_version=expected, key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/finance/refunds", status_code=status.HTTP_201_CREATED)
def create_refund(body: RefundCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")):
    key = _key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "finance.refund.create", "financial_refund", None, body.workspace_id, lambda: _service(db).create_refund(actor, workspace_id=body.workspace_id, payment_id=body.payment_id, amount_minor=body.amount_minor, currency=body.currency, reason=body.reason, expected_version=expected, key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))
