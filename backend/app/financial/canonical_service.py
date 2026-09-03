from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any, Protocol

from sqlalchemy.exc import IntegrityError

from app.clinical.appointments.authorization import AppointmentAuthorizationService
from app.clinical.appointments.service import AppointmentError, VersionConflictError
from app.clinical.encounters.models import CoreEncounter
from app.identity.api.workspaces import NiamActor
from app.identity.services.canonical_audit import AuditEventInput, SyncCanonicalAuditService

from .canonical_models import (
    FinancialBill,
    FinancialBillItem,
    FinancialClaim,
    FinancialClaimItem,
    FinancialCommandReceipt,
    FinancialCoverage,
    FinancialEligibilityCheck,
    FinancialLedgerAccount,
    FinancialLedgerEntry,
    FinancialOutboxEvent,
    FinancialPayer,
    FinancialPayment,
    FinancialPaymentEvent,
    FinancialPreauthorization,
    FinancialRefund,
    FinancialServiceCatalog,
    FinancialServicePrice,
)


class FinancialError(AppointmentError):
    status_code = 409


class FinancialNotFound(FinancialError):
    status_code = 404


class FinancialValidation(FinancialError):
    status_code = 422


class FinancialAuthorization(FinancialError):
    status_code = 403


class PaymentEventVerifier(Protocol):
    def verify(self, *, payment: FinancialPayment, event_id: str, nonce: str, now: datetime) -> bool:
        """Verify an event without accepting a client-provided boolean as proof."""


class SyntheticPaymentEventVerifier:
    """Test-only verifier; it never contacts a payment provider."""

    def verify(self, *, payment: FinancialPayment, event_id: str, nonce: str, now: datetime) -> bool:
        del now
        return payment.provider == "SYNTHETIC" and event_id.startswith("synthetic-event-") and nonce.startswith("synthetic-nonce-")


class CanonicalFinancialService:
    """Synthetic-first finance orchestration; legacy billing remains isolated."""

    def __init__(self, db, *, payment_event_verifier: PaymentEventVerifier | None = None):
        self.db = db
        self.authz = AppointmentAuthorizationService(db)
        self.audit = SyncCanonicalAuditService(db)
        self.payment_event_verifier = payment_event_verifier or SyntheticPaymentEventVerifier()

    def _scope(self, actor: NiamActor, workspace_id: str, permission: str):
        scope = self.authz.resolve_scope(actor, workspace_id)
        self.authz.require_permission(actor, scope, permission)
        return scope

    def _require_patient_context(self, actor, scope, patient_person_id: str, encounter_id: str | None = None) -> None:
        """Allow only self context or an existing in-scope encounter.

        This intentionally fails closed for arbitrary member/patient IDs. A future
        staff workflow must prove the same patient/encounter/scope relationship
        through the canonical encounter/access owners before it can be widened.
        """
        if not patient_person_id:
            raise FinancialValidation("A patient context is required", code="PATIENT_CONTEXT_REQUIRED")
        if encounter_id:
            encounter = (
                self.db.query(CoreEncounter)
                .filter(
                    CoreEncounter.id == encounter_id,
                    CoreEncounter.patient_person_id == patient_person_id,
                    CoreEncounter.organization_id == scope.organization_id,
                    CoreEncounter.facility_id == scope.facility_id,
                    CoreEncounter.workspace_id == scope.workspace_id,
                    CoreEncounter.status != "CANCELLED",
                )
                .first()
            )
            if encounter is None:
                raise FinancialAuthorization("The patient encounter is not authorized", code="PATIENT_CONTEXT_DENIED")
            return
        if scope.actor_person_id != patient_person_id:
            raise FinancialAuthorization("The patient context is not authorized", code="PATIENT_CONTEXT_DENIED")

    def _claim(self, actor, operation: str, key: str, payload: dict[str, Any]):
        if not key or len(key) > 128:
            raise FinancialValidation("Idempotency-Key is required")
        fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
        existing = self.db.query(FinancialCommandReceipt).filter_by(actor_account_id=actor.account.id, operation=operation, idempotency_key=key).first()
        if existing:
            if existing.request_fingerprint != fingerprint:
                raise FinancialError("Idempotency key was reused with a different request", code="FINANCIAL_IDEMPOTENCY_CONFLICT")
            return existing.response_body
        receipt = FinancialCommandReceipt(actor_account_id=actor.account.id, operation=operation, idempotency_key=key, request_fingerprint=fingerprint, status="CLAIMED")
        self.db.add(receipt)
        try:
            self.db.flush()
        except IntegrityError as exc:
            self.db.rollback()
            raise FinancialError("This financial command is already in progress", code="FINANCIAL_IDEMPOTENCY_CONFLICT") from exc
        return None

    def _complete(self, actor, operation: str, key: str, resource_id: str, response: dict[str, Any]):
        receipt = self.db.query(FinancialCommandReceipt).filter_by(actor_account_id=actor.account.id, operation=operation, idempotency_key=key).with_for_update().first()
        if receipt:
            receipt.status = "COMPLETED"
            receipt.resource_id = resource_id
            receipt.response_body = response
            receipt.completed_at = datetime.now(UTC)
            self.db.flush()

    def _audit(self, actor, event_type: str, target_type: str, target_id: str, scope, correlation_id: str, request_id: str | None, changes: dict[str, Any]):
        self.audit.record(AuditEventInput(event_type=event_type, category="financial", action=event_type.lower(), actor_id=actor.account.id, actor_identity_id=actor.account.identity_id, actor_type="account", organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id, target_type=target_type, target_id=target_id, decision="allow", request_id=request_id, correlation_id=correlation_id, session_id=actor.session.uuid, source="api", data_classification="FINANCIAL", changes=changes))

    @staticmethod
    def _new_id():
        return uuid.uuid4().hex.upper()[:26]

    def create_payer(self, actor, *, workspace_id, name, payer_type, jurisdiction, key, correlation_id, request_id):
        scope = self._scope(actor, workspace_id, "financial.payer.manage")
        payload = {"workspace_id": scope.workspace_id, "name": name.strip(), "payer_type": payer_type, "jurisdiction": jurisdiction}
        cached = self._claim(actor, "finance.payer.create", key, payload)
        if cached is not None:
            return cached
        row = FinancialPayer(organization_id=scope.organization_id, name=name.strip(), payer_type=payer_type, jurisdiction=jurisdiction, status="ACTIVE", version=1)
        self.db.add(row)
        self.db.flush()
        response = self._payer_response(row, correlation_id)
        self._complete(actor, "finance.payer.create", key, row.id, response)
        self._audit(actor, "PAYER_CREATED", "financial_payer", row.id, scope, correlation_id, request_id, {"payer_type": payer_type})
        return response

    def create_coverage(self, actor, *, workspace_id, member_id, payer_id, plan_code, valid_from, valid_to, key, correlation_id, request_id):
        scope = self._scope(actor, workspace_id, "financial.coverage.write")
        self._require_patient_context(actor, scope, member_id)
        payer = self.db.query(FinancialPayer).filter_by(id=payer_id, organization_id=scope.organization_id).first()
        if payer is None:
            raise FinancialNotFound("Payer was not found", code="PAYER_NOT_FOUND")
        payload = {"workspace_id": scope.workspace_id, "member_id": member_id, "payer_id": payer.id, "plan_code": plan_code, "valid_from": valid_from.isoformat(), "valid_to": valid_to.isoformat() if valid_to else None}
        cached = self._claim(actor, "finance.coverage.create", key, payload)
        if cached is not None:
            return cached
        row = FinancialCoverage(member_id=member_id, payer_id=payer.id, plan_code=plan_code, valid_from=valid_from, valid_to=valid_to, status="ACTIVE", limits={}, network={}, benefits={}, version=1)
        self.db.add(row)
        self.db.flush()
        response = self._coverage_response(row, correlation_id)
        self._complete(actor, "finance.coverage.create", key, row.id, response)
        self._audit(actor, "COVERAGE_CREATED", "financial_coverage", row.id, scope, correlation_id, request_id, {"status": row.status})
        return response

    def check_eligibility(self, actor, *, workspace_id, coverage_id, service_id, synthetic_outcome, key, correlation_id, request_id):
        scope = self._scope(actor, workspace_id, "financial.eligibility.check")
        coverage = self.db.query(FinancialCoverage).filter_by(id=coverage_id).with_for_update().first()
        if coverage is None or coverage.payer_id not in {payer.id for payer in self.db.query(FinancialPayer).filter_by(organization_id=scope.organization_id).all()}:
            raise FinancialNotFound("Coverage was not found", code="COVERAGE_NOT_FOUND")
        self._require_patient_context(actor, scope, coverage.member_id)
        if synthetic_outcome != "UNKNOWN":
            raise FinancialError("Insurance provider evidence is unavailable; eligibility remains UNKNOWN", code="FINANCIAL_PROVIDER_UNAVAILABLE")
        now = datetime.now(UTC)
        payload = {"workspace_id": scope.workspace_id, "coverage_id": coverage.id, "service_id": service_id, "outcome": "UNKNOWN"}
        cached = self._claim(actor, "finance.eligibility.check", key, payload)
        if cached is not None:
            return cached
        status = synthetic_outcome if coverage.status == "ACTIVE" and (coverage.valid_to is None or coverage.valid_to >= now) else "UNKNOWN"
        row = FinancialEligibilityCheck(coverage_id=coverage.id, member_id=coverage.member_id, service_id=service_id, provider_account_id=actor.account.id, facility_id=scope.facility_id, status=status, response_payload={"source": "SYNTHETIC"}, version=1, idempotency_key=key)
        self.db.add(row)
        self.db.flush()
        response = self._eligibility_response(row, correlation_id)
        self._complete(actor, "finance.eligibility.check", key, row.id, response)
        self._audit(actor, "ELIGIBILITY_CHECKED", "financial_eligibility", row.id, scope, correlation_id, request_id, {"status": status, "synthetic": True})
        return response

    def create_preauthorization(self, actor, *, workspace_id, member_id, payer_id, service_id, encounter_id, clinical_indication, estimated_amount_minor, currency, key, correlation_id, request_id):
        scope = self._scope(actor, workspace_id, "financial.preauth.write")
        self._require_patient_context(actor, scope, member_id, encounter_id)
        payer = self.db.query(FinancialPayer).filter_by(id=payer_id, organization_id=scope.organization_id, status="ACTIVE").first()
        service = self.db.query(FinancialServiceCatalog).filter_by(id=service_id, organization_id=scope.organization_id, facility_id=scope.facility_id, active=True).first()
        if payer is None:
            raise FinancialNotFound("Payer was not found", code="PAYER_NOT_FOUND")
        if service is None:
            raise FinancialNotFound("Service was not found", code="SERVICE_NOT_FOUND")
        if service.currency != currency:
            raise FinancialValidation("Preauthorization currency does not match service currency", code="CURRENCY_MISMATCH")
        payload = {"workspace_id": scope.workspace_id, "member_id": member_id, "payer_id": payer_id, "service_id": service_id, "encounter_id": encounter_id, "clinical_indication": clinical_indication.strip(), "estimated_amount_minor": estimated_amount_minor, "currency": currency}
        cached = self._claim(actor, "finance.preauth.create", key, payload)
        if cached is not None:
            return cached
        row = FinancialPreauthorization(member_id=member_id, payer_id=payer.id, provider_account_id=actor.account.id, facility_id=scope.facility_id, service_id=service.id, encounter_id=encounter_id, clinical_indication=clinical_indication.strip(), estimated_amount_minor=estimated_amount_minor, currency=currency, status="REQUESTED", version=1, idempotency_key=key)
        self.db.add(row)
        self.db.flush()
        response = self._preauth_response(row, correlation_id)
        self._complete(actor, "finance.preauth.create", key, row.id, response)
        self._audit(actor, "PREAUTHORIZATION_REQUESTED", "financial_preauthorization", row.id, scope, correlation_id, request_id, {"status": row.status, "amount_minor": estimated_amount_minor, "provider_contacted": False})
        return response

    def create_service(self, actor, *, workspace_id, code, name, specialty, currency, key, correlation_id, request_id):
        scope = self._scope(actor, workspace_id, "financial.service.manage")
        payload = {"workspace_id": scope.workspace_id, "code": code, "name": name, "specialty": specialty, "currency": currency}
        cached = self._claim(actor, "finance.service.create", key, payload)
        if cached is not None:
            return cached
        row = FinancialServiceCatalog(organization_id=scope.organization_id, facility_id=scope.facility_id, code=code, name=name, specialty=specialty, provider_account_id=actor.account.id, currency=currency, active=True, version=1)
        self.db.add(row)
        self.db.flush()
        response = self._service_response(row, correlation_id)
        self._complete(actor, "finance.service.create", key, row.id, response)
        self._audit(actor, "FINANCIAL_SERVICE_CREATED", "financial_service", row.id, scope, correlation_id, request_id, {"code": code})
        return response

    def create_price(self, actor, *, workspace_id, service_id, amount_minor, currency, valid_from, valid_to, key, correlation_id, request_id):
        scope = self._scope(actor, workspace_id, "financial.service.manage")
        service = self.db.query(FinancialServiceCatalog).filter_by(id=service_id, organization_id=scope.organization_id, facility_id=scope.facility_id).with_for_update().first()
        if service is None:
            raise FinancialNotFound("Service was not found", code="SERVICE_NOT_FOUND")
        if service.currency != currency:
            raise FinancialValidation("Price currency does not match service currency", code="CURRENCY_MISMATCH")
        payload = {"workspace_id": scope.workspace_id, "service_id": service_id, "amount_minor": amount_minor, "currency": currency, "valid_from": valid_from.isoformat(), "valid_to": valid_to.isoformat() if valid_to else None}
        cached = self._claim(actor, "finance.price.create", key, payload)
        if cached is not None:
            return cached
        row = FinancialServicePrice(service_id=service.id, amount_minor=amount_minor, currency=currency, valid_from=valid_from, valid_to=valid_to, source="SYNTHETIC", version=1)
        self.db.add(row)
        self.db.flush()
        response = self._price_response(row, correlation_id)
        self._complete(actor, "finance.price.create", key, row.id, response)
        self._audit(actor, "PRICE_VERSION_CREATED", "financial_service_price", row.id, scope, correlation_id, request_id, {"amount_minor": amount_minor, "currency": currency})
        return response

    def create_bill(self, actor, *, workspace_id, patient_person_id, encounter_id, currency, items, coverage_id, discount_minor, key, correlation_id, request_id):
        scope = self._scope(actor, workspace_id, "financial.bill.create")
        self._require_patient_context(actor, scope, patient_person_id, encounter_id)
        coverage = None
        if coverage_id:
            coverage = self.db.query(FinancialCoverage).join(FinancialPayer, FinancialPayer.id == FinancialCoverage.payer_id).filter(FinancialCoverage.id == coverage_id, FinancialCoverage.member_id == patient_person_id, FinancialPayer.organization_id == scope.organization_id).with_for_update().first()
            if coverage is None:
                raise FinancialAuthorization("The coverage is not authorized for this patient and organization", code="COVERAGE_CONTEXT_DENIED")
        payload = {"workspace_id": scope.workspace_id, "patient_person_id": patient_person_id, "encounter_id": encounter_id, "currency": currency, "items": [item.model_dump() if hasattr(item, "model_dump") else item for item in items], "coverage_id": coverage.id if coverage else None, "discount_minor": discount_minor}
        cached = self._claim(actor, "finance.bill.create", key, payload)
        if cached is not None:
            return cached
        if discount_minor < 0:
            raise FinancialValidation("Discount cannot be negative", code="DISCOUNT_INVALID")
        priced_items = []
        gross = 0
        now = datetime.now(UTC)
        for item in items:
            service_id = item.service_id if hasattr(item, "service_id") else item["service_id"]
            quantity = item.quantity if hasattr(item, "quantity") else item["quantity"]
            service = self.db.query(FinancialServiceCatalog).filter_by(id=service_id, organization_id=scope.organization_id, facility_id=scope.facility_id, active=True).first()
            if service is None:
                raise FinancialNotFound("Service was not found", code="SERVICE_NOT_FOUND")
            price = self.db.query(FinancialServicePrice).filter(FinancialServicePrice.service_id == service.id, FinancialServicePrice.currency == currency, FinancialServicePrice.valid_from <= now, (FinancialServicePrice.valid_to.is_(None) | (FinancialServicePrice.valid_to >= now))).order_by(FinancialServicePrice.version.desc()).first()
            if price is None:
                raise FinancialValidation("An active price is required", code="PRICE_NOT_FOUND")
            total = price.amount_minor * quantity
            gross += total
            priced_items.append((service, price, quantity, total))
        if discount_minor > gross:
            raise FinancialValidation("Discount exceeds bill gross", code="DISCOUNT_EXCEEDS_GROSS")
        bill = FinancialBill(patient_person_id=patient_person_id, provider_account_id=actor.account.id, organization_id=scope.organization_id, facility_id=scope.facility_id, encounter_id=encounter_id, coverage_id=coverage.id if coverage else None, currency=currency, gross_minor=gross, discount_minor=discount_minor, covered_minor=0, copay_minor=gross - discount_minor, deductible_minor=0, noncovered_minor=0, net_minor=gross - discount_minor, status="ISSUED", version=1)
        self.db.add(bill)
        self.db.flush()
        for service, price, quantity, total in priced_items:
            self.db.add(FinancialBillItem(bill_id=bill.id, service_id=service.id, description=service.name, quantity=quantity, unit_price_minor=price.amount_minor, total_minor=total))
        self.db.flush()
        response = self._bill_response(bill, correlation_id)
        self._complete(actor, "finance.bill.create", key, bill.id, response)
        self._audit(actor, "BILL_CREATED", "financial_bill", bill.id, scope, correlation_id, request_id, {"gross_minor": gross, "net_minor": bill.net_minor, "currency": currency})
        return response

    def create_claim(self, actor, *, workspace_id, bill_id, payer_id, key, correlation_id, request_id):
        scope = self._scope(actor, workspace_id, "financial.claim.write")
        bill = self.db.query(FinancialBill).filter_by(id=bill_id, organization_id=scope.organization_id, facility_id=scope.facility_id).with_for_update().first()
        payer = self.db.query(FinancialPayer).filter_by(id=payer_id, organization_id=scope.organization_id).first()
        if bill is None:
            raise FinancialNotFound("Bill was not found", code="BILL_NOT_FOUND")
        self._require_patient_context(actor, scope, bill.patient_person_id, bill.encounter_id)
        if payer is None:
            raise FinancialNotFound("Payer was not found", code="PAYER_NOT_FOUND")
        if bill.coverage_id:
            coverage = self.db.query(FinancialCoverage).filter_by(id=bill.coverage_id, payer_id=payer.id, member_id=bill.patient_person_id).first()
            if coverage is None:
                raise FinancialAuthorization("Claim payer does not match bill coverage", code="CLAIM_PAYER_MISMATCH")
        payload = {"workspace_id": scope.workspace_id, "bill_id": bill.id, "payer_id": payer.id}
        cached = self._claim(actor, "finance.claim.create", key, payload)
        if cached is not None:
            return cached
        row = FinancialClaim(bill_id=bill.id, patient_person_id=bill.patient_person_id, provider_account_id=actor.account.id, payer_id=payer.id, amount_minor=bill.net_minor, currency=bill.currency, status="DRAFT", version=1, idempotency_key=key)
        self.db.add(row)
        self.db.flush()
        for item in self.db.query(FinancialBillItem).filter_by(bill_id=bill.id).all():
            self.db.add(FinancialClaimItem(claim_id=row.id, service_id=item.service_id, amount_minor=item.total_minor))
        self.db.flush()
        response = self._claim_response(row, correlation_id)
        self._complete(actor, "finance.claim.create", key, row.id, response)
        self._audit(actor, "CLAIM_CREATED", "financial_claim", row.id, scope, correlation_id, request_id, {"amount_minor": row.amount_minor})
        return response

    def transition_claim(self, actor, *, workspace_id, claim_id, target_status, expected_version, key, correlation_id, request_id):
        scope = self._scope(actor, workspace_id, "financial.claim.review")
        row = (
            self.db.query(FinancialClaim)
            .join(FinancialBill, FinancialBill.id == FinancialClaim.bill_id)
            .filter(
                FinancialClaim.id == claim_id,
                FinancialBill.organization_id == scope.organization_id,
                FinancialBill.facility_id == scope.facility_id,
            )
            .with_for_update()
            .first()
        )
        if row is None:
            raise FinancialNotFound("Claim was not found", code="CLAIM_NOT_FOUND")
        if row.version != expected_version:
            raise VersionConflictError("The claim changed before this operation")
        if target_status == "SUBMITTED" and row.provider_account_id != actor.account.id:
            raise FinancialAuthorization("Only the claim creator may submit it", code="CLAIM_SUBMITTER_REQUIRED")
        if target_status != "SUBMITTED" and row.provider_account_id == actor.account.id:
            raise FinancialAuthorization("A claim creator cannot review or settle the same claim", code="CLAIM_SOD_REQUIRED")
        allowed = {"DRAFT": {"SUBMITTED"}, "SUBMITTED": {"RECEIVED", "REJECTED", "UNDER_REVIEW"}, "RECEIVED": {"UNDER_REVIEW"}, "UNDER_REVIEW": {"APPROVED", "PARTIALLY_APPROVED", "DENIED"}, "APPROVED": {"PAID"}, "PARTIALLY_APPROVED": {"PAID"}, "DENIED": {"APPEALED"}}
        if target_status not in allowed.get(row.status, set()):
            raise FinancialError("Claim transition is not allowed", code="INVALID_FINANCIAL_TRANSITION")
        payload = {"workspace_id": scope.workspace_id, "claim_id": row.id, "target_status": target_status, "expected_version": expected_version}
        cached = self._claim(actor, "finance.claim.transition", key, payload)
        if cached is not None:
            return cached
        before = row.status
        row.status = target_status
        row.version += 1
        if target_status == "SUBMITTED":
            row.submitted_at = datetime.now(UTC)
        self.db.flush()
        response = self._claim_response(row, correlation_id)
        self._complete(actor, "finance.claim.transition", key, row.id, response)
        self._audit(actor, "CLAIM_" + target_status, "financial_claim", row.id, scope, correlation_id, request_id, {"state_before": before, "state_after": target_status, "version_after": row.version})
        return response

    def create_payment(self, actor, *, workspace_id, bill_id, amount_minor, currency, provider, provider_available, key, correlation_id, request_id):
        scope = self._scope(actor, workspace_id, "financial.payment.write")
        bill = self.db.query(FinancialBill).filter_by(id=bill_id, organization_id=scope.organization_id, facility_id=scope.facility_id).with_for_update().first()
        if bill is None:
            raise FinancialNotFound("Bill was not found", code="BILL_NOT_FOUND")
        self._require_patient_context(actor, scope, bill.patient_person_id, bill.encounter_id)
        if bill.currency != currency:
            raise FinancialValidation("Payment currency does not match bill currency", code="CURRENCY_MISMATCH")
        payload = {"workspace_id": scope.workspace_id, "bill_id": bill.id, "amount_minor": amount_minor, "currency": currency, "provider": provider, "provider_available": provider_available}
        cached = self._claim(actor, "finance.payment.create", key, payload)
        if cached is not None:
            return cached
        captured = sum((p.amount_minor for p in self.db.query(FinancialPayment).filter_by(bill_id=bill.id).filter(FinancialPayment.status.in_(["CAPTURED", "SETTLED", "PENDING"])).with_for_update().all()), 0)
        if amount_minor > bill.net_minor - captured:
            raise FinancialError("Payment exceeds outstanding balance", code="PAYMENT_EXCEEDS_BALANCE")
        status = "INITIATED" if provider_available else "PENDING"
        row = FinancialPayment(bill_id=bill.id, payee_organization_id=scope.organization_id, amount_minor=amount_minor, currency=currency, reference="SYN-PAY-" + uuid.uuid4().hex[:20].upper(), provider=provider, status=status, version=1, idempotency_key=key)
        self.db.add(row)
        self.db.flush()
        if not provider_available:
            self.db.add(FinancialOutboxEvent(event_key="payment-pending:" + row.id, event_type="PAYMENT_PROVIDER_RETRY", aggregate_type="payment", aggregate_id=row.id, payload={"payment_id": row.id, "status": "PENDING"}, status="PENDING", attempts=0))
        response = self._payment_response(row, correlation_id)
        self._complete(actor, "finance.payment.create", key, row.id, response)
        self._audit(actor, "PAYMENT_INITIATED", "financial_payment", row.id, scope, correlation_id, request_id, {"status": status, "amount_minor": amount_minor})
        return response

    def capture_payment(self, actor, *, workspace_id, payment_id, event_id, nonce, occurred_at, expected_version, key, correlation_id, request_id):
        scope = self._scope(actor, workspace_id, "financial.payment.capture")
        row = self.db.query(FinancialPayment).filter_by(id=payment_id, payee_organization_id=scope.organization_id).with_for_update().first()
        if row is None:
            raise FinancialNotFound("Payment was not found", code="PAYMENT_NOT_FOUND")
        bill = self.db.query(FinancialBill).filter_by(id=row.bill_id, organization_id=scope.organization_id, facility_id=scope.facility_id).with_for_update().first()
        if bill is None:
            raise FinancialNotFound("Payment was not found", code="PAYMENT_NOT_FOUND")
        self._require_patient_context(actor, scope, bill.patient_person_id, bill.encounter_id)
        payload = {"workspace_id": scope.workspace_id, "payment_id": row.id, "event_id": event_id, "nonce": nonce, "occurred_at": occurred_at.isoformat() if occurred_at else None, "expected_version": expected_version}
        cached = self._claim(actor, "finance.payment.capture", key, payload)
        if cached is not None:
            return cached
        if row.version != expected_version:
            raise VersionConflictError("The payment changed before capture")
        now = datetime.now(UTC)
        event_time = occurred_at.replace(tzinfo=UTC) if occurred_at is not None and occurred_at.tzinfo is None else (occurred_at.astimezone(UTC) if occurred_at is not None else now)
        if event_time > now or (now - event_time).total_seconds() > 10 * 60:
            raise FinancialError("Payment event is outside the accepted time window", code="PAYMENT_EVENT_STALE")
        if self.db.query(FinancialPaymentEvent).filter_by(event_id=event_id).first() is not None or self.db.query(FinancialPaymentEvent).filter_by(nonce=nonce).first() is not None:
            raise FinancialError("Payment event replay was rejected", code="PAYMENT_REPLAY")
        if not self.payment_event_verifier.verify(payment=row, event_id=event_id, nonce=nonce, now=event_time):
            raise FinancialError("Payment provider signature was not verified", code="PAYMENT_SIGNATURE_INVALID")
        if row.status not in {"INITIATED", "AUTHORIZED", "PENDING"}:
            raise FinancialError("Payment cannot be captured in its current state", code="PAYMENT_STATE_CONFLICT")
        row.status = "CAPTURED"
        row.captured_at = now
        row.version += 1
        self.db.add(FinancialPaymentEvent(payment_id=row.id, event_id=event_id, event_type="CAPTURED", occurred_at=event_time, signature_valid=True, nonce=nonce, payload_hash=hashlib.sha256((event_id + nonce + event_time.isoformat()).encode()).hexdigest()))
        cash = self._ledger_account(scope.organization_id, "CASH", row.currency)
        revenue = self._ledger_account(scope.organization_id, "HEALTHCARE_REVENUE", row.currency)
        self.db.add_all([FinancialLedgerEntry(transaction_id=row.id, account_id=cash.id, debit_minor=row.amount_minor, credit_minor=0, currency=row.currency, reference_type="payment", reference_id=row.id), FinancialLedgerEntry(transaction_id=row.id, account_id=revenue.id, debit_minor=0, credit_minor=row.amount_minor, currency=row.currency, reference_type="payment", reference_id=row.id)])
        self.db.flush()
        self._assert_ledger_balanced(row.id)
        captured_total = sum((p.amount_minor for p in self.db.query(FinancialPayment).filter_by(bill_id=bill.id).filter(FinancialPayment.status.in_(["CAPTURED", "SETTLED"])).all()), 0)
        bill.status = "PAID" if captured_total >= bill.net_minor else "PARTIALLY_PAID"
        bill.version += 1
        self.db.flush()
        response = self._payment_response(row, correlation_id)
        self._complete(actor, "finance.payment.capture", key, row.id, response)
        self._audit(actor, "PAYMENT_CAPTURED", "financial_payment", row.id, scope, correlation_id, request_id, {"status": row.status, "version_after": row.version})
        return response

    def create_refund(self, actor, *, workspace_id, payment_id, amount_minor, currency, reason, expected_version, key, correlation_id, request_id):
        scope = self._scope(actor, workspace_id, "financial.refund.write")
        payment = self.db.query(FinancialPayment).filter_by(id=payment_id, payee_organization_id=scope.organization_id).with_for_update().first()
        if payment is None:
            raise FinancialNotFound("Payment was not found", code="PAYMENT_NOT_FOUND")
        bill = self.db.query(FinancialBill).filter_by(id=payment.bill_id, organization_id=scope.organization_id, facility_id=scope.facility_id).with_for_update().first()
        if bill is None:
            raise FinancialNotFound("Payment was not found", code="PAYMENT_NOT_FOUND")
        self._require_patient_context(actor, scope, bill.patient_person_id, bill.encounter_id)
        payload = {"workspace_id": scope.workspace_id, "payment_id": payment.id, "amount_minor": amount_minor, "currency": currency, "reason": reason, "expected_version": expected_version}
        cached = self._claim(actor, "finance.refund.create", key, payload)
        if cached is not None:
            return cached
        if payment.version != expected_version:
            raise VersionConflictError("The payment changed before refund")
        if payment.currency != currency or payment.status not in {"CAPTURED", "SETTLED", "PARTIALLY_REFUNDED"}:
            raise FinancialError("Payment is not refundable", code="PAYMENT_NOT_REFUNDABLE")
        refunded = sum((r.amount_minor for r in self.db.query(FinancialRefund).filter_by(payment_id=payment.id, status="COMPLETED").with_for_update().all()), 0)
        if amount_minor > payment.amount_minor - refunded:
            raise FinancialError("Refund exceeds captured payment", code="REFUND_EXCEEDS_PAYMENT")
        row = FinancialRefund(payment_id=payment.id, amount_minor=amount_minor, currency=currency, reason=reason.strip(), reference="SYN-REF-" + uuid.uuid4().hex[:20].upper(), status="COMPLETED", version=1, idempotency_key=key)
        self.db.add(row)
        payment.status = "REFUNDED" if amount_minor + refunded == payment.amount_minor else "PARTIALLY_REFUNDED"
        payment.version += 1
        self.db.flush()
        cash = self._ledger_account(scope.organization_id, "CASH", currency)
        revenue = self._ledger_account(scope.organization_id, "HEALTHCARE_REVENUE", currency)
        transaction_id = row.id
        self.db.add_all([FinancialLedgerEntry(transaction_id=transaction_id, account_id=revenue.id, debit_minor=amount_minor, credit_minor=0, currency=currency, reference_type="refund", reference_id=row.id), FinancialLedgerEntry(transaction_id=transaction_id, account_id=cash.id, debit_minor=0, credit_minor=amount_minor, currency=currency, reference_type="refund", reference_id=row.id)])
        self.db.flush()
        self._assert_ledger_balanced(transaction_id)
        bill.status = "REFUNDED" if payment.status == "REFUNDED" else "PARTIALLY_PAID"
        bill.version += 1
        self.db.flush()
        response = self._refund_response(row, correlation_id)
        self._complete(actor, "finance.refund.create", key, row.id, response)
        self._audit(actor, "REFUND_COMPLETED", "financial_refund", row.id, scope, correlation_id, request_id, {"amount_minor": amount_minor, "payment_id": payment.id})
        return response

    def _assert_ledger_balanced(self, transaction_id: str) -> None:
        entries = self.db.query(FinancialLedgerEntry).filter_by(transaction_id=transaction_id).all()
        debit = sum(entry.debit_minor for entry in entries)
        credit = sum(entry.credit_minor for entry in entries)
        if not entries or debit != credit:
            raise FinancialError("Ledger transaction is not balanced", code="LEDGER_IMBALANCE")

    def _ledger_account(self, organization_id, code, currency):
        row = self.db.query(FinancialLedgerAccount).filter_by(organization_id=organization_id, code=code, currency=currency).with_for_update().first()
        if row is None:
            row = FinancialLedgerAccount(organization_id=organization_id, code=code, name=code.replace("_", " "), currency=currency, active=True)
            self.db.add(row)
            self.db.flush()
        return row

    @staticmethod
    def _payer_response(r, c): return {"id": r.id, "organization_id": r.organization_id, "name": r.name, "payer_type": r.payer_type, "jurisdiction": r.jurisdiction, "status": r.status, "version": r.version, "correlation_id": c}
    @staticmethod
    def _coverage_response(r, c): return {"id": r.id, "member_id": r.member_id, "payer_id": r.payer_id, "plan_code": r.plan_code, "status": r.status, "valid_from": r.valid_from.isoformat(), "valid_to": r.valid_to.isoformat() if r.valid_to else None, "version": r.version, "correlation_id": c}
    @staticmethod
    def _eligibility_response(r, c): return {"id": r.id, "coverage_id": r.coverage_id, "member_id": r.member_id, "status": r.status, "version": r.version, "correlation_id": c}
    @staticmethod
    def _preauth_response(r, c): return {"id": r.id, "member_id": r.member_id, "payer_id": r.payer_id, "service_id": r.service_id, "encounter_id": r.encounter_id, "estimated_amount_minor": r.estimated_amount_minor, "currency": r.currency, "status": r.status, "version": r.version, "correlation_id": c}
    @staticmethod
    def _service_response(r, c): return {"id": r.id, "organization_id": r.organization_id, "facility_id": r.facility_id, "code": r.code, "name": r.name, "specialty": r.specialty, "currency": r.currency, "version": r.version, "correlation_id": c}
    @staticmethod
    def _price_response(r, c): return {"id": r.id, "service_id": r.service_id, "amount_minor": r.amount_minor, "currency": r.currency, "version": r.version, "correlation_id": c}
    @staticmethod
    def _bill_response(r, c): return {"id": r.id, "patient_person_id": r.patient_person_id, "coverage_id": r.coverage_id, "gross_minor": r.gross_minor, "discount_minor": r.discount_minor, "covered_minor": r.covered_minor, "copay_minor": r.copay_minor, "net_minor": r.net_minor, "currency": r.currency, "status": r.status, "version": r.version, "correlation_id": c}
    @staticmethod
    def _claim_response(r, c): return {"id": r.id, "bill_id": r.bill_id, "patient_person_id": r.patient_person_id, "payer_id": r.payer_id, "amount_minor": r.amount_minor, "currency": r.currency, "status": r.status, "version": r.version, "correlation_id": c}
    @staticmethod
    def _payment_response(r, c): return {"id": r.id, "bill_id": r.bill_id, "amount_minor": r.amount_minor, "currency": r.currency, "reference": r.reference, "provider": r.provider, "status": r.status, "version": r.version, "correlation_id": c}
    @staticmethod
    def _refund_response(r, c): return {"id": r.id, "payment_id": r.payment_id, "amount_minor": r.amount_minor, "currency": r.currency, "reference": r.reference, "status": r.status, "version": r.version, "correlation_id": c}
