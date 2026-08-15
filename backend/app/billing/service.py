"""Business rules for the demo-safe billing and insurance projection."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app._compat import UTC
from app.models.claim import Claim
from app.models.patient import Patient

from .models import BillingAuditEvent, BillingInvoice, BillingInvoiceLine, BillingPayment, InsuranceCoverage


class BillingService:
    def __init__(self, db: Session):
        self.db = db

    def _audit(self, *, lab_id: int, entity_type: str, entity_id: str, action: str, actor_user_id: int | None, request_id: str | None, safe_metadata: dict | None = None) -> BillingAuditEvent:
        event = BillingAuditEvent(
            lab_id=lab_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor_user_id=actor_user_id,
            request_id=request_id,
            safe_metadata=safe_metadata or {},
        )
        self.db.add(event)
        return event

    def _patient_or_raise(self, *, patient_id: int, lab_id: int) -> Patient:
        patient = self.db.query(Patient).filter(Patient.id == patient_id, Patient.lab_id == lab_id).first()
        if patient is None:
            raise ValueError("patient not found")
        return patient

    def list_invoices(self, *, lab_id: int, search: str | None = None) -> list[BillingInvoice]:
        query = (
            self.db.query(BillingInvoice)
            .options(joinedload(BillingInvoice.lines), joinedload(BillingInvoice.payments))
            .filter(BillingInvoice.lab_id == lab_id)
            .order_by(BillingInvoice.created_at.desc())
        )
        if search:
            term = f"%{search.strip()}%"
            query = query.filter(or_(BillingInvoice.invoice_number.ilike(term), BillingInvoice.encounter_ref.ilike(term)))
        return query.all()

    def create_invoice(
        self,
        *,
        lab_id: int,
        patient_id: int,
        encounter_ref: str,
        lines: list[dict],
        covered_amount: Decimal,
        due_at: date | None,
        idempotency_key: str | None,
        actor_user_id: int | None,
        request_id: str | None,
    ) -> BillingInvoice:
        self._patient_or_raise(patient_id=patient_id, lab_id=lab_id)
        if idempotency_key:
            previous = self.db.query(BillingInvoice).filter(
                BillingInvoice.lab_id == lab_id,
                BillingInvoice.idempotency_key == idempotency_key,
            ).first()
            if previous is not None:
                return previous
        if not lines:
            raise ValueError("at least one invoice line is required")

        normalized_lines: list[dict] = []
        gross = Decimal("0.00")
        for index, item in enumerate(lines, start=1):
            quantity = int(item.get("quantity", 1))
            unit_amount = Decimal(str(item["unit_amount"]))
            if quantity < 1 or unit_amount < 0:
                raise ValueError("invalid invoice line")
            line_amount = (unit_amount * quantity).quantize(Decimal("0.01"))
            gross += line_amount
            normalized_lines.append({
                "line_number": index,
                "service_code": str(item["service_code"]),
                "description": str(item["description"]),
                "quantity": quantity,
                "unit_amount": unit_amount,
                "line_amount": line_amount,
            })

        covered = Decimal(str(covered_amount)).quantize(Decimal("0.01"))
        if covered < 0 or covered > gross:
            raise ValueError("covered amount must be between zero and gross amount")
        invoice = BillingInvoice(
            lab_id=lab_id,
            patient_id=patient_id,
            encounter_ref=encounter_ref,
            invoice_number=f"GULA-BILL-{datetime.now(UTC):%y%m%d}-{uuid4().hex[:8].upper()}",
            status="draft",
            gross_amount=gross,
            covered_amount=covered,
            patient_due=gross - covered,
            idempotency_key=idempotency_key,
            due_at=due_at,
            issued_at=date.today(),
            created_by=actor_user_id,
        )
        invoice.lines = [BillingInvoiceLine(**line) for line in normalized_lines]
        self.db.add(invoice)
        self.db.flush()
        self._audit(
            lab_id=lab_id,
            entity_type="invoice",
            entity_id=str(invoice.id),
            action="created",
            actor_user_id=actor_user_id,
            request_id=request_id,
            safe_metadata={"gross_amount": str(gross), "covered_amount": str(covered), "synthetic": True},
        )
        return invoice

    def simulate_settlement(self, *, invoice_id: int, lab_id: int, actor_user_id: int | None, request_id: str | None) -> tuple[BillingInvoice, BillingPayment]:
        invoice = self.db.query(BillingInvoice).filter(BillingInvoice.id == invoice_id, BillingInvoice.lab_id == lab_id).first()
        if invoice is None:
            raise ValueError("invoice not found")
        if invoice.status == "paid":
            raise ValueError("invoice already paid")
        amount = Decimal(invoice.patient_due or 0).quantize(Decimal("0.01"))
        if amount <= 0:
            raise ValueError("invoice has no patient balance")
        payment = BillingPayment(
            lab_id=lab_id,
            invoice_id=invoice.id,
            patient_id=invoice.patient_id,
            amount=amount,
            currency=invoice.currency,
            method="synthetic_settlement",
            reference=f"GULA-PAY-{uuid4().hex[:10].upper()}",
            kind="patient_payment",
            created_by=actor_user_id,
        )
        invoice.status = "paid"
        self.db.add(payment)
        self.db.flush()
        self._audit(
            lab_id=lab_id,
            entity_type="invoice",
            entity_id=str(invoice.id),
            action="synthetic_settlement_recorded",
            actor_user_id=actor_user_id,
            request_id=request_id,
            safe_metadata={"amount": str(amount), "method": "synthetic_settlement", "external_call": False},
        )
        return invoice, payment

    def list_coverages(self, *, lab_id: int, search: str | None = None) -> list[InsuranceCoverage]:
        query = self.db.query(InsuranceCoverage).filter(InsuranceCoverage.lab_id == lab_id).order_by(InsuranceCoverage.expires_on.asc())
        if search:
            term = f"%{search.strip()}%"
            query = query.filter(or_(InsuranceCoverage.member_id.ilike(term), InsuranceCoverage.payer.ilike(term), InsuranceCoverage.plan.ilike(term)))
        return query.all()

    def create_coverage(self, *, lab_id: int, patient_id: int, payer: str, plan: str, member_id: str, expires_on: date, actor_user_id: int | None, request_id: str | None) -> InsuranceCoverage:
        self._patient_or_raise(patient_id=patient_id, lab_id=lab_id)
        coverage = InsuranceCoverage(
            lab_id=lab_id,
            patient_id=patient_id,
            payer=payer,
            plan=plan,
            member_id=member_id,
            expires_on=expires_on,
            state="needs_verification",
            verification="لم يُتحقق",
            created_by=actor_user_id,
        )
        self.db.add(coverage)
        self.db.flush()
        self._audit(
            lab_id=lab_id,
            entity_type="coverage",
            entity_id=str(coverage.id),
            action="created",
            actor_user_id=actor_user_id,
            request_id=request_id,
            safe_metadata={"synthetic": True},
        )
        return coverage

    def verify_coverage(self, *, coverage_id: int, lab_id: int, actor_user_id: int | None, request_id: str | None) -> InsuranceCoverage:
        coverage = self.db.query(InsuranceCoverage).filter(InsuranceCoverage.id == coverage_id, InsuranceCoverage.lab_id == lab_id).first()
        if coverage is None:
            raise ValueError("coverage not found")
        coverage.last_checked_at = datetime.now(UTC)
        coverage.verification = "تمت المطابقة في سجل تجريبي محلي"
        coverage.state = "expired" if coverage.expires_on < date.today() else "active"
        self._audit(
            lab_id=lab_id,
            entity_type="coverage",
            entity_id=str(coverage.id),
            action="local_verification_recorded",
            actor_user_id=actor_user_id,
            request_id=request_id,
            safe_metadata={"state": coverage.state, "external_call": False},
        )
        return coverage

    def list_claims(self, *, lab_id: int, search: str | None = None) -> list[Claim]:
        query = self.db.query(Claim).filter(Claim.lab_id == lab_id).order_by(Claim.created_at.desc())
        if search:
            term = f"%{search.strip()}%"
            query = query.filter(or_(Claim.external_ref.ilike(term), Claim.status.ilike(term)))
        return query.all()

    def advance_claim(self, *, claim_id: int, lab_id: int, actor_user_id: int | None, request_id: str | None) -> Claim:
        claim = self.db.query(Claim).filter(Claim.id == claim_id, Claim.lab_id == lab_id).first()
        if claim is None:
            raise ValueError("claim not found")
        transitions = {
            "draft": "validated",
            "validated": "submitted",
            "submitted": "accepted",
            "rejected": "submitted",
            "accepted": "paid",
        }
        previous_status = claim.status
        next_status = transitions.get(previous_status)
        if next_status is None:
            raise ValueError("claim is already in a final state")
        claim.status = next_status
        if next_status == "submitted":
            claim.submitted_at = datetime.now(UTC)
        self._audit(
            lab_id=lab_id,
            entity_type="claim",
            entity_id=str(claim.id),
            action="status_advanced",
            actor_user_id=actor_user_id,
            request_id=request_id,
            safe_metadata={"from": previous_status, "to": next_status, "external_call": False},
        )
        return claim

    def list_payments(self, *, lab_id: int) -> list[BillingPayment]:
        return self.db.query(BillingPayment).filter(BillingPayment.lab_id == lab_id).order_by(BillingPayment.created_at.desc()).all()

    def summary(self, *, lab_id: int) -> dict:
        today = date.today()
        open_invoices = self.db.query(BillingInvoice).filter(BillingInvoice.lab_id == lab_id, BillingInvoice.status != "paid").all()
        rejected_claims = self.db.query(Claim).filter(Claim.lab_id == lab_id, Claim.status == "rejected").count()
        pending_verification = self.db.query(InsuranceCoverage).filter(
            InsuranceCoverage.lab_id == lab_id,
            InsuranceCoverage.state.notin_(["active"]),
        ).count()
        return {
            "open_invoices": len(open_invoices),
            "outstanding": str(sum((Decimal(invoice.patient_due or 0) for invoice in open_invoices), Decimal("0.00"))),
            "rejected_claims": rejected_claims,
            "pending_verification": pending_verification,
            "synthetic": True,
            "external_integrations": False,
            "as_of": today.isoformat(),
        }

    def alerts(self, *, lab_id: int) -> list[dict]:
        soon = date.today() + timedelta(days=60)
        alerts: list[dict] = []
        for claim in self.db.query(Claim).filter(Claim.lab_id == lab_id, Claim.status == "rejected").all():
            alerts.append({"type": "claim_rejected", "severity": "high", "reference": str(claim.id), "message": "مطالبة مرفوضة تحتاج مراجعة"})
        for coverage in self.db.query(InsuranceCoverage).filter(
            InsuranceCoverage.lab_id == lab_id,
            InsuranceCoverage.expires_on <= soon,
            InsuranceCoverage.state != "active",
        ).all():
            alerts.append({"type": "coverage_expiring", "severity": "medium", "reference": str(coverage.id), "message": "بطاقة تأمين تحتاج تحققًا"})
        for invoice in self.db.query(BillingInvoice).filter(
            BillingInvoice.lab_id == lab_id,
            BillingInvoice.status != "paid",
            BillingInvoice.due_at.is_not(None),
            BillingInvoice.due_at < date.today(),
        ).all():
            alerts.append({"type": "invoice_overdue", "severity": "medium", "reference": str(invoice.id), "message": "فاتورة متأخرة"})
        return alerts
