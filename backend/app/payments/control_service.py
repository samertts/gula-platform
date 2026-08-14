from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.exceptions import ConflictError, NotFoundError, ServiceError

from .models import (
    CashShift,
    FinancialControlRequest,
    PaymentAuditEvent,
    PaymentInvoice,
    ReconciliationCase,
)

UTC = timezone.utc

ALLOWED_CONTROL_TYPES = {
    "provider_approval",
    "rail_activation",
    "routing_rule_activation",
    "refund_approval",
    "fee_policy_change",
    "live_operations_enable",
    "kill_switch_change",
}


def now_utc() -> datetime:
    return datetime.now(UTC)


def normalize_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class FinancialControlService:
    def __init__(self, db: Session):
        self.db = db

    def _audit(self, request: FinancialControlRequest, action: str, actor_user_id: int, metadata: dict[str, Any] | None = None) -> None:
        self.db.add(
            PaymentAuditEvent(
                institution_id=request.institution_id,
                entity_type="financial_control_request",
                entity_id=request.id,
                action=action,
                actor_user_id=actor_user_id,
                request_id=request.request_id,
                safe_metadata={"control_type": request.control_type, **(metadata or {})},
            )
        )

    def _get(self, request_id: str, institution_id: int) -> FinancialControlRequest:
        request = (
            self.db.query(FinancialControlRequest)
            .filter(
                FinancialControlRequest.id == request_id,
                FinancialControlRequest.institution_id == institution_id,
            )
            .first()
        )
        if request is None:
            raise NotFoundError("Financial control request not found")
        if request.status == "REQUESTED" and request.expires_at and normalize_utc(request.expires_at) <= now_utc():
            request.status = "EXPIRED"
            self._audit(request, "EXPIRED", request.requested_by, {"reason": "approval_window_elapsed"})
            self.db.flush()
        return request

    def create_request(
        self,
        *,
        institution_id: int,
        control_type: str,
        resource_type: str,
        resource_id: str,
        requested_action: str,
        idempotency_key: str,
        reason: str,
        requested_by: int,
        request_id: str | None,
        expires_at: datetime | None,
        safe_metadata: dict[str, Any] | None = None,
    ) -> FinancialControlRequest:
        if control_type not in ALLOWED_CONTROL_TYPES:
            raise ServiceError("Unsupported financial control type", status_code=422)
        key = idempotency_key.strip()
        if not key or len(key) > 128:
            raise ServiceError("A valid Idempotency-Key is required", status_code=400)
        if not reason.strip() or len(reason) > 1024:
            raise ServiceError("A concise control reason is required", status_code=422)
        if expires_at is not None and normalize_utc(expires_at) <= now_utc():
            raise ServiceError("Control approval expiry must be in the future", status_code=422)

        existing = (
            self.db.query(FinancialControlRequest)
            .filter(
                FinancialControlRequest.institution_id == institution_id,
                FinancialControlRequest.idempotency_key == key,
            )
            .first()
        )
        if existing is not None:
            same_request = (
                existing.control_type == control_type
                and existing.resource_type == resource_type
                and existing.resource_id == resource_id
                and existing.requested_action == requested_action
            )
            if not same_request:
                raise ConflictError("Idempotency key has already been used for a different control request")
            return existing

        request = FinancialControlRequest(
            institution_id=institution_id,
            control_type=control_type,
            resource_type=resource_type,
            resource_id=resource_id,
            requested_action=requested_action,
            status="REQUESTED",
            idempotency_key=key,
            reason=reason.strip(),
            requested_by=requested_by,
            request_id=request_id,
            expires_at=expires_at,
            safe_metadata={"external_operation": False, **(safe_metadata or {})},
        )
        self.db.add(request)
        self.db.flush()
        self._audit(request, "CONTROL_REQUESTED", requested_by, {"requested_action": requested_action})
        return request

    def approve(self, *, request_id: str, institution_id: int, actor_user_id: int) -> FinancialControlRequest:
        request = self._get(request_id, institution_id)
        if request.status != "REQUESTED":
            raise ConflictError("Only requested controls can be approved")
        if request.requested_by == actor_user_id:
            raise ServiceError("A different authorized user must approve the control request", status_code=403)
        request.status = "APPROVED"
        request.approved_by = actor_user_id
        request.approved_at = now_utc()
        self._audit(request, "CONTROL_APPROVED", actor_user_id, {"external_operation": False})
        self.db.flush()
        return request

    def reject(self, *, request_id: str, institution_id: int, actor_user_id: int, rejection_reason: str) -> FinancialControlRequest:
        request = self._get(request_id, institution_id)
        if request.status != "REQUESTED":
            raise ConflictError("Only requested controls can be rejected")
        if request.requested_by == actor_user_id:
            raise ServiceError("A different authorized user must reject the control request", status_code=403)
        if not rejection_reason.strip():
            raise ServiceError("A rejection reason is required", status_code=422)
        request.status = "REJECTED"
        request.rejection_reason = rejection_reason.strip()
        self._audit(request, "CONTROL_REJECTED", actor_user_id, {"reason": request.rejection_reason})
        self.db.flush()
        return request

    def apply(self, *, request_id: str, institution_id: int, actor_user_id: int) -> FinancialControlRequest:
        request = self._get(request_id, institution_id)
        if request.status != "APPROVED":
            raise ConflictError("Only approved controls can be marked applied")
        if request.approved_by == actor_user_id or request.requested_by == actor_user_id:
            raise ServiceError("Control application requires an independent operator", status_code=403)
        request.status = "APPLIED"
        request.applied_by = actor_user_id
        request.applied_at = now_utc()
        request.safe_metadata = {**(request.safe_metadata or {}), "external_operation": False, "application_recorded": True}
        self._audit(request, "CONTROL_APPLIED", actor_user_id, {"external_operation": False})
        self.db.flush()
        return request

    def list_requests(self, *, institution_id: int, status: str | None = None, limit: int = 100) -> list[FinancialControlRequest]:
        query = (
            self.db.query(FinancialControlRequest)
            .filter(FinancialControlRequest.institution_id == institution_id)
            .order_by(FinancialControlRequest.requested_at.desc())
            .limit(limit)
        )
        if status:
            query = query.filter(FinancialControlRequest.status == status)
        return query.all()

    def summary(self, *, institution_id: int) -> dict[str, Any]:
        invoice_totals = self.db.query(
            func.coalesce(func.sum(PaymentInvoice.total_amount), 0),
            func.coalesce(func.sum(PaymentInvoice.paid_amount), 0),
            func.coalesce(func.sum(PaymentInvoice.refunded_amount), 0),
            func.count(PaymentInvoice.id),
        ).filter(PaymentInvoice.institution_id == institution_id).one()
        statuses = dict(
            self.db.query(FinancialControlRequest.status, func.count(FinancialControlRequest.id))
            .filter(FinancialControlRequest.institution_id == institution_id)
            .group_by(FinancialControlRequest.status)
            .all()
        )
        open_reconciliations = (
            self.db.query(func.count(ReconciliationCase.id))
            .filter(
                ReconciliationCase.institution_id == institution_id,
                ReconciliationCase.status.notin_({"RESOLVED", "CLOSED"}),
            )
            .scalar()
            or 0
        )
        cash_variances = (
            self.db.query(func.count(CashShift.id))
            .filter(CashShift.institution_id == institution_id, CashShift.status == "CLOSED_VARIANCE")
            .scalar()
            or 0
        )
        billed, collected, refunded, invoice_count = invoice_totals
        billed = billed or 0
        collected = collected or 0
        refunded = refunded or 0
        return {
            "institution_id": institution_id,
            "as_of": now_utc(),
            "currency": "IQD",
            "billed_amount": billed,
            "collected_amount": collected,
            "outstanding_amount": billed - collected,
            "refunded_amount": refunded,
            "invoice_count": invoice_count,
            "control_requests": statuses,
            "open_reconciliation_cases": open_reconciliations,
            "cash_variance_cases": cash_variances,
            "live_operation_enabled": False,
            "external_provider_calls": 0,
            "data_basis": "PaymentInvoice facts, cash reconciliation, and append-only control requests",
            "limitations": [
                "No forecast, valuation, ROI, or investment return is calculated",
                "External payment providers remain disabled in this control-plane summary",
                "Legacy financial engine metrics are excluded until consolidation is complete",
            ],
        }
