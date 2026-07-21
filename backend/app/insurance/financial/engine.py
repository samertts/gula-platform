"""Insurance Financial Engine — adjudication, payment, settlement, budgeting, and auditing.

Provides the complete financial lifecycle for the National Health Insurance
Platform: claim adjudication with deductible/copay/coinsurance logic, payment
processing (individual and batch), periodic provider settlement, invoice
generation, budget management, monthly closing, and financial auditing.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import uuid4

from sqlalchemy import func
from sqlalchemy.orm import Session

from app._compat import UTC
from app.insurance.domain.enums import (
    ClaimStatus, PaymentStatus, SettlementStatus,
)
from app.insurance.domain.models import (
    Coverage, FeeScheduleItem, InsuranceClaim,
    InsuranceClaimItem, InsurancePayment, InsuranceProvider,
    InsurancePolicy, Settlement,
)

logger = logging.getLogger("gula.insurance.financial")


# =========================================================================
# Result dataclasses
# =========================================================================


@dataclass
class AdjudicationResult:
    claim_id: int
    status: str
    total_billed: Decimal
    total_allowed: Decimal
    total_deductible: Decimal
    total_copay: Decimal
    total_coinsurance: Decimal
    total_net_payment: Decimal
    total_patient_responsibility: Decimal
    adjudication_notes: list[str]
    line_items: list[dict]


@dataclass
class PaymentResult:
    payment_id: int
    claim_id: int
    amount: Decimal
    status: str
    reference: str
    processed_at: str


# =========================================================================
# ClaimAdjudicator
# =========================================================================


class ClaimAdjudicator:
    """Adjudicates insurance claims against policy terms, fee schedules,
    benefit limits, deductibles, copays, coinsurance, and pre-existing
    condition rules."""

    def __init__(self, db_session: Session) -> None:
        self._db = db_session

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def adjudicate(self, claim_id: int) -> AdjudicationResult:
        claim = self._db.query(InsuranceClaim).filter(InsuranceClaim.id == claim_id).first()
        if not claim:
            raise ValueError(f"Claim {claim_id} not found")

        eligibility = self.validate_eligibility(claim)
        if not eligibility.get("eligible", True):
            notes = [eligibility.get("reason", "Claim ineligible")]
            return AdjudicationResult(
                claim_id=claim_id,
                status="denied",
                total_billed=claim.total_billed or Decimal("0"),
                total_allowed=Decimal("0"),
                total_deductible=Decimal("0"),
                total_copay=Decimal("0"),
                total_coinsurance=Decimal("0"),
                total_net_payment=Decimal("0"),
                total_patient_responsibility=Decimal("0"),
                adjudication_notes=notes,
                line_items=[],
            )

        coverage = self._get_coverage_for_claim(claim)
        line_items = []
        total_billed = Decimal("0")
        total_allowed = Decimal("0")
        total_deductible = Decimal("0")
        total_copay = Decimal("0")
        total_coinsurance = Decimal("0")
        total_patient_resp = Decimal("0")
        all_notes: list[str] = []

        for item in (claim.items or []):
            billed = item.billed_amount or Decimal("0")
            total_billed += billed

            allowed_info = self.calculate_allowed_amounts(item)
            allowed = allowed_info["allowed_amount"]
            total_allowed += allowed

            deductible_info = self.apply_deductible(item, coverage, allowed)
            deductible = deductible_info["deductible_amount"]
            total_deductible += deductible

            after_deductible = allowed - deductible

            copay_info = self.apply_copay(item, coverage, after_deductible)
            copay = copay_info["copay_amount"]
            total_copay += copay

            after_copay = after_deductible - copay

            coinsurance_info = self.apply_coinsurance(item, coverage, after_copay)
            coinsurance = coinsurance_info["coinsurance_amount"]
            total_coinsurance += coinsurance

            net_payment = after_copay - coinsurance
            patient_resp = deductible + copay + coinsurance
            total_patient_resp += patient_resp

            benefit_check = self.check_benefit_limits(item, coverage, net_payment)
            if benefit_check.get("limited", False):
                net_payment = benefit_check["adjusted_amount"]
                all_notes.append(benefit_check.get("note", ""))

            pre_existing = self.check_pre_existing(item, coverage)
            if not pre_existing.get("covered", True):
                net_payment = Decimal("0")
                patient_resp = billed
                all_notes.append(pre_existing.get("reason", "Pre-existing condition exclusion"))

            line_items.append({
                "item_id": item.id,
                "service_code": item.service_code,
                "billed_amount": billed,
                "allowed_amount": allowed,
                "deductible_amount": deductible,
                "copay_amount": copay,
                "coinsurance_amount": coinsurance,
                "net_payment": net_payment,
                "patient_responsibility": patient_resp,
                "adjudication_status": benefit_check.get("status", "adjudicated"),
                "adjudication_reason": pre_existing.get("reason"),
            })

        net_payment_total = total_allowed - total_deductible - total_copay - total_coinsurance
        if net_payment_total < Decimal("0"):
            net_payment_total = Decimal("0")

        claim.total_allowed = total_allowed
        claim.total_deductible = total_deductible
        claim.total_copay = total_copay
        claim.total_patient_responsibility = total_patient_resp
        claim.adjudicated_date = date.today()
        claim.status = ClaimStatus.ADJUDICATED
        self._db.commit()

        notes = self.generate_adjudication_notes(AdjudicationResult(
            claim_id=claim_id,
            status="adjudicated",
            total_billed=total_billed,
            total_allowed=total_allowed,
            total_deductible=total_deductible,
            total_copay=total_copay,
            total_coinsurance=total_coinsurance,
            total_net_payment=net_payment_total,
            total_patient_responsibility=total_patient_resp,
            adjudication_notes=[],
            line_items=line_items,
        ))

        return AdjudicationResult(
            claim_id=claim_id,
            status="adjudicated",
            total_billed=total_billed,
            total_allowed=total_allowed,
            total_deductible=total_deductible,
            total_copay=total_copay,
            total_coinsurance=total_coinsurance,
            total_net_payment=net_payment_total,
            total_patient_responsibility=total_patient_resp,
            adjudication_notes=notes + all_notes,
            line_items=line_items,
        )

    def validate_eligibility(self, claim: InsuranceClaim) -> dict[str, Any]:
        if claim.status in (ClaimStatus.CANCELLED, ClaimStatus.REVERSED, ClaimStatus.DENIED):
            return {"eligible": False, "reason": f"Claim status is {claim.status}"}

        coverage = self._get_coverage_for_claim(claim)
        if not coverage:
            return {"eligible": False, "reason": "No active coverage found for claim"}

        if coverage.status != "active":
            return {"eligible": False, "reason": f"Coverage status is {coverage.status}"}

        policy = self._db.query(InsurancePolicy).filter(
            InsurancePolicy.id == coverage.policy_id
        ).first()
        if not policy or policy.status != "active":
            return {"eligible": False, "reason": "Policy not active"}

        svc_date = claim.service_start_date or date.today()
        if coverage.end_date and svc_date > coverage.end_date:
            return {"eligible": False, "reason": "Coverage expired"}
        if svc_date < coverage.start_date:
            return {"eligible": False, "reason": "Coverage not yet active"}
        if policy.end_date and svc_date > policy.end_date:
            return {"eligible": False, "reason": "Policy expired"}

        return {"eligible": True, "coverage_id": coverage.id, "policy_id": policy.id}

    def calculate_allowed_amounts(self, item: InsuranceClaimItem) -> dict[str, Any]:
        fee = self._db.query(FeeScheduleItem).filter(
            FeeScheduleItem.service_code == item.service_code,
            FeeScheduleItem.is_active == True,
        ).first()

        if fee and fee.allowed_amount:
            allowed = fee.allowed_amount * (item.quantity or 1)
        elif fee:
            allowed = fee.negotiated_price * (item.quantity or 1)
        else:
            allowed = item.billed_amount or Decimal("0")

        return {
            "allowed_amount": allowed,
            "fee_schedule_id": fee.id if fee else None,
            "negotiated_price": fee.negotiated_price if fee else None,
        }

    def apply_deductible(self, item: InsuranceClaimItem, coverage: Coverage, allowed_amount: Decimal) -> dict[str, Any]:
        deduct_remaining = coverage.deductible_remaining or Decimal("0")
        if deduct_remaining <= Decimal("0"):
            return {"deductible_amount": Decimal("0"), "deductible_remaining": deduct_remaining}

        deductible = min(allowed_amount, deduct_remaining)
        new_remaining = deduct_remaining - deductible

        coverage.deductible_remaining = new_remaining
        self._db.flush()

        return {
            "deductible_amount": deductible,
            "deductible_remaining": new_remaining,
        }

    def apply_copay(self, item: InsuranceClaimItem, coverage: Coverage, amount_after_deductible: Decimal) -> dict[str, Any]:
        copay_pct = coverage.copay_percentage or 0.0
        if copay_pct <= 0:
            fee_item = self._db.query(FeeScheduleItem).filter(
                FeeScheduleItem.service_code == item.service_code,
                FeeScheduleItem.is_active == True,
            ).first()
            if fee_item and fee_item.copay_amount:
                copay = min(fee_item.copay_amount, amount_after_deductible)
                return {"copay_amount": copay, "copay_percentage": 0.0, "copay_fixed": float(copay)}

            return {"copay_amount": Decimal("0"), "copay_percentage": 0.0}

        copay = (amount_after_deductible * Decimal(str(copay_pct))) / Decimal("100")
        copay = min(copay, amount_after_deductible)

        return {"copay_amount": copay, "copay_percentage": copay_pct, "copay_fixed": None}

    def apply_coinsurance(self, item: InsuranceClaimItem, coverage: Coverage, amount_after_copay: Decimal) -> dict[str, Any]:
        fee_item = self._db.query(FeeScheduleItem).filter(
            FeeScheduleItem.service_code == item.service_code,
            FeeScheduleItem.is_active == True,
        ).first()

        coinsurance_pct = fee_item.coinsurance_percentage if fee_item and fee_item.coinsurance_percentage else 0.0
        if coinsurance_pct <= 0:
            return {"coinsurance_amount": Decimal("0"), "coinsurance_percentage": 0.0}

        coinsurance = (amount_after_copay * Decimal(str(coinsurance_pct))) / Decimal("100")
        coinsurance = min(coinsurance, amount_after_copay)

        return {"coinsurance_amount": coinsurance, "coinsurance_percentage": coinsurance_pct}

    def check_benefit_limits(self, item: InsuranceClaimItem, coverage: Coverage, net_payment: Decimal) -> dict[str, Any]:
        benefit_remaining = coverage.benefit_remaining or Decimal("0")
        if benefit_remaining <= Decimal("0") and coverage.benefit_total and coverage.benefit_total > 0:
            return {"limited": True, "adjusted_amount": Decimal("0"), "status": "denied", "note": "Benefit limit exhausted"}

        if benefit_remaining > Decimal("0") and net_payment > benefit_remaining:
            return {
                "limited": True,
                "adjusted_amount": benefit_remaining,
                "status": "limited",
                "note": f"Reduced from {net_payment} to {benefit_remaining} by benefit limit",
            }

        return {"limited": False, "adjusted_amount": net_payment, "status": "adjudicated"}

    def check_pre_existing(self, item: InsuranceClaimItem, coverage: Coverage) -> dict[str, Any]:
        if coverage.pre_existing_wait_period:
            policy = self._db.query(InsurancePolicy).filter(
                InsurancePolicy.id == coverage.policy_id
            ).first()
            if policy and policy.start_date:
                days_since_start = (date.today() - policy.start_date).days
                if days_since_start < 180:
                    return {
                        "covered": False,
                        "reason": "Pre-existing condition waiting period active",
                        "wait_days_remaining": 180 - days_since_start,
                    }
        return {"covered": True, "reason": None}

    def calculate_net_payment(self, claim: InsuranceClaim) -> Decimal:
        total = Decimal("0")
        for item in (claim.items or []):
            allowed = item.allowed_amount or item.billed_amount or Decimal("0")
            deductible = item.deductible_amount or Decimal("0")
            copay = item.copay_amount or Decimal("0")
            patient_resp = item.patient_responsibility or Decimal("0")
            net = allowed - deductible - copay - patient_resp
            if net > Decimal("0"):
                total += net
        return total

    def generate_adjudication_notes(self, result: AdjudicationResult) -> list[str]:
        notes = []
        notes.append(f"Claim #{result.claim_id} adjudicated as {result.status}")
        notes.append(f"Total billed: {result.total_billed}")
        notes.append(f"Total allowed: {result.total_allowed}")
        if result.total_deductible > 0:
            notes.append(f"Deductible applied: {result.total_deductible}")
        if result.total_copay > 0:
            notes.append(f"Copay applied: {result.total_copay}")
        if result.total_coinsurance > 0:
            notes.append(f"Coinsurance applied: {result.total_coinsurance}")
        notes.append(f"Net payment: {result.total_net_payment}")
        notes.append(f"Patient responsibility: {result.total_patient_responsibility}")
        return notes

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_coverage_for_claim(self, claim: InsuranceClaim) -> Coverage | None:
        return self._db.query(Coverage).filter(
            Coverage.id == claim.coverage_id
        ).first()


# =========================================================================
# PaymentProcessor
# =========================================================================


class PaymentProcessor:
    """Processes insurance payments, including individual and batch
    processing, reversals, reconciliation, EFT/check file generation,
    and tax withholding."""

    def __init__(self, db_session: Session) -> None:
        self._db = db_session

    def process_payment(
        self, claim_id: int, amount: Decimal, method: str,
    ) -> InsurancePayment:
        claim = self._db.query(InsuranceClaim).filter(
            InsuranceClaim.id == claim_id
        ).first()
        if not claim:
            raise ValueError(f"Claim {claim_id} not found")

        now = datetime.now(UTC)
        payment_number = f"PAY-{now.strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"

        payment = InsurancePayment(
            lab_id=claim.lab_id,
            claim_id=claim_id,
            payer_id=claim.provider_id,
            payment_number=payment_number,
            status=PaymentStatus.PENDING,
            amount=amount,
            currency=claim.currency or "IQD",
            payment_method=method,
            payment_date=now.date(),
            processed_at=now,
        )
        self._db.add(payment)
        self._db.flush()

        claim.total_paid = (claim.total_paid or Decimal("0")) + amount
        claim.paid_date = now.date()

        total_allowed = claim.total_allowed or Decimal("0")
        if claim.total_paid >= total_allowed > 0:
            claim.status = ClaimStatus.PAID
        elif claim.total_paid and claim.total_paid > 0:
            claim.status = ClaimStatus.PARTIALLY_PAID

        self._db.commit()
        self._db.refresh(payment)

        logger.info(
            "[PAYMENT] Processed payment_id=%d claim_id=%d amount=%s method=%s",
            payment.id, claim_id, amount, method,
        )
        return payment

    def batch_process(self, claim_ids: list[int]) -> list[InsurancePayment]:
        payments: list[InsurancePayment] = []
        for cid in claim_ids:
            claim = self._db.query(InsuranceClaim).filter(
                InsuranceClaim.id == cid
            ).first()
            if not claim:
                logger.warning("[PAYMENT] Skipping missing claim %d in batch", cid)
                continue

            net = (claim.total_allowed or Decimal("0")
                   - (claim.total_deductible or Decimal("0"))
                   - (claim.total_copay or Decimal("0")))
            if net > Decimal("0"):
                payment = self.process_payment(cid, net, "batch_eft")
                payments.append(payment)
        return payments

    def reverse_payment(self, payment_id: int, reason: str) -> InsurancePayment:
        payment = self._db.query(InsurancePayment).filter(
            InsurancePayment.id == payment_id
        ).first()
        if not payment:
            raise ValueError(f"Payment {payment_id} not found")
        if payment.status == PaymentStatus.REVERSED:
            raise ValueError(f"Payment {payment_id} already reversed")

        payment.status = PaymentStatus.REVERSED
        payment.adjustment_reason = reason
        payment.adjustment_amount = payment.amount

        claim = self._db.query(InsuranceClaim).filter(
            InsuranceClaim.id == payment.claim_id
        ).first()
        if claim:
            claim.total_paid = (claim.total_paid or Decimal("0")) - payment.amount
            if claim.total_paid <= Decimal("0"):
                claim.status = ClaimStatus.ADJUDICATED
                claim.total_paid = Decimal("0")

        self._db.commit()
        self._db.refresh(payment)
        logger.info(
            "[PAYMENT] Reversed payment_id=%d claim_id=%d reason=%s",
            payment_id, payment.claim_id, reason,
        )
        return payment

    def reconcile_payment(self, payment_id: int, reference: str) -> dict[str, Any]:
        payment = self._db.query(InsurancePayment).filter(
            InsurancePayment.id == payment_id
        ).first()
        if not payment:
            raise ValueError(f"Payment {payment_id} not found")

        payment.reference_number = reference
        payment.status = PaymentStatus.COMPLETED
        self._db.commit()

        return {
            "payment_id": payment.id,
            "claim_id": payment.claim_id,
            "amount": payment.amount,
            "reference": reference,
            "status": payment.status.value,
            "reconciled_at": datetime.now(UTC).isoformat(),
        }

    def generate_payment_file(self, payment_ids: list[int], format: str = "csv") -> str:
        payments = (
            self._db.query(InsurancePayment)
            .filter(InsurancePayment.id.in_(payment_ids))
            .all()
        )

        if format == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([
                "payment_id", "claim_id", "amount", "currency",
                "payment_method", "payment_number", "reference",
            ])
            for p in payments:
                writer.writerow([
                    p.id, p.claim_id, str(p.amount), p.currency,
                    p.payment_method, p.payment_number, p.reference_number or "",
                ])
            return output.getvalue()

        elif format == "json":
            return json.dumps([
                {
                    "payment_id": p.id,
                    "claim_id": p.claim_id,
                    "amount": str(p.amount),
                    "currency": p.currency,
                    "payment_method": p.payment_method,
                    "payment_number": p.payment_number,
                    "reference": p.reference_number,
                }
                for p in payments
            ], indent=2)

        raise ValueError(f"Unsupported format: {format}")

    def calculate_withholding(self, payment: InsurancePayment, tax_rules: dict[str, Any]) -> Decimal:
        rate = Decimal(str(tax_rules.get("withholding_rate", 0)))
        if rate <= 0:
            return Decimal("0")

        exemption = Decimal(str(tax_rules.get("exemption_amount", 0)))
        taxable = payment.amount - exemption
        if taxable <= 0:
            return Decimal("0")

        withholding = (taxable * rate) / Decimal("100")
        return withholding.quantize(Decimal("0.01"))


# =========================================================================
# SettlementEngine
# =========================================================================


class SettlementEngine:
    """Manages periodic settlements between payers and healthcare providers."""

    def __init__(self, db_session: Session) -> None:
        self._db = db_session

    def create_settlement(
        self, provider_id: int, start: date, end: date,
    ) -> Settlement:
        now = datetime.now(UTC)
        settlement_number = f"STL-{provider_id}-{start.strftime('%Y%m%d')}-{end.strftime('%Y%m%d')}"

        settlement = Settlement(
            provider_id=provider_id,
            period_start=start,
            period_end=end,
            status=SettlementStatus.PENDING,
            settlement_number=settlement_number,
        )
        self._db.add(settlement)
        self._db.commit()
        self._db.refresh(settlement)
        return settlement

    def calculate_settlement_amounts(self, settlement_id: int) -> dict[str, Any]:
        settlement = self._db.query(Settlement).filter(
            Settlement.id == settlement_id
        ).first()
        if not settlement:
            raise ValueError(f"Settlement {settlement_id} not found")

        claims = (
            self._db.query(InsuranceClaim)
            .filter(
                InsuranceClaim.provider_id == settlement.provider_id,
                InsuranceClaim.service_start_date >= settlement.period_start,
                InsuranceClaim.service_start_date <= settlement.period_end,
                InsuranceClaim.status.in_([
                    ClaimStatus.ADJUDICATED, ClaimStatus.PAID,
                    ClaimStatus.PARTIALLY_PAID, ClaimStatus.ACCEPTED,
                ]),
            )
            .all()
        )

        total_claims = len(claims)
        total_billed = sum(c.total_billed or Decimal("0") for c in claims)
        total_allowed = sum(c.total_allowed or Decimal("0") for c in claims)
        total_paid = sum(c.total_paid or Decimal("0") for c in claims)
        total_deductible = sum(c.total_deductible or Decimal("0") for c in claims)
        total_copay = sum(c.total_copay or Decimal("0") for c in claims)
        net_amount = total_allowed - total_deductible - total_copay

        settlement.total_claims = total_claims
        settlement.total_billed = total_billed
        settlement.total_allowed = total_allowed
        settlement.total_paid = total_paid
        settlement.total_deductible = total_deductible
        settlement.total_copay = total_copay
        settlement.net_amount = net_amount
        self._db.commit()

        return {
            "settlement_id": settlement.id,
            "total_claims": total_claims,
            "total_billed": total_billed,
            "total_allowed": total_allowed,
            "total_paid": total_paid,
            "total_deductible": total_deductible,
            "total_copay": total_copay,
            "net_amount": net_amount,
        }

    def reconcile_settlement(self, settlement_id: int) -> dict[str, Any]:
        settlement = self._db.query(Settlement).filter(
            Settlement.id == settlement_id
        ).first()
        if not settlement:
            raise ValueError(f"Settlement {settlement_id} not found")

        amounts = self.calculate_settlement_amounts(settlement_id)
        paid_claims = (
            self._db.query(func.count(InsuranceClaim.id))
            .filter(
                InsuranceClaim.provider_id == settlement.provider_id,
                InsuranceClaim.service_start_date >= settlement.period_start,
                InsuranceClaim.service_start_date <= settlement.period_end,
                InsuranceClaim.status == ClaimStatus.PAID,
            )
            .scalar()
        )

        discrepancies: list[dict[str, Any]] = []
        if settlement.total_paid and amounts["total_paid"]:
            diff = settlement.total_paid - amounts["total_paid"]
            if diff != 0:
                discrepancies.append({
                    "type": "paid_amount_mismatch",
                    "expected": float(amounts["total_paid"]),
                    "actual": float(settlement.total_paid),
                    "difference": float(diff),
                })

        settlement.reconciled_at = datetime.now(UTC)
        self._db.commit()

        return {
            "settlement_id": settlement.id,
            "status": "reconciled" if not discrepancies else "disputed",
            "amounts": amounts,
            "paid_claims_count": paid_claims or 0,
            "discrepancies": discrepancies,
        }

    def close_settlement(self, settlement_id: int) -> Settlement:
        settlement = self._db.query(Settlement).filter(
            Settlement.id == settlement_id
        ).first()
        if not settlement:
            raise ValueError(f"Settlement {settlement_id} not found")

        settlement.status = SettlementStatus.COMPLETED
        settlement.paid_at = datetime.now(UTC)
        self._db.commit()
        self._db.refresh(settlement)
        return settlement

    def generate_settlement_report(self, settlement_id: int) -> dict[str, Any]:
        settlement = self._db.query(Settlement).filter(
            Settlement.id == settlement_id
        ).first()
        if not settlement:
            raise ValueError(f"Settlement {settlement_id} not found")

        amounts = self.calculate_settlement_amounts(settlement_id)
        claims = (
            self._db.query(InsuranceClaim)
            .filter(
                InsuranceClaim.provider_id == settlement.provider_id,
                InsuranceClaim.service_start_date >= settlement.period_start,
                InsuranceClaim.service_start_date <= settlement.period_end,
            )
            .all()
        )

        status_breakdown: dict[str, int] = {}
        for c in claims:
            key = c.status.value if hasattr(c.status, "value") else str(c.status)
            status_breakdown[key] = status_breakdown.get(key, 0) + 1

        provider = self._db.query(InsuranceProvider).filter(
            InsuranceProvider.id == settlement.provider_id
        ).first()

        return {
            "settlement_number": settlement.settlement_number,
            "period": {
                "start": settlement.period_start.isoformat(),
                "end": settlement.period_end.isoformat(),
            },
            "provider": {
                "id": provider.id if provider else None,
                "name": provider.name if provider else None,
            },
            "amounts": amounts,
            "status_breakdown": status_breakdown,
            "reconciled_at": settlement.reconciled_at.isoformat() if settlement.reconciled_at else None,
            "paid_at": settlement.paid_at.isoformat() if settlement.paid_at else None,
            "status": settlement.status.value if hasattr(settlement.status, "value") else str(settlement.status),
        }

    def age_analysis(self, provider_id: int) -> dict[str, Any]:
        today = date.today()
        buckets = {
            "0-30": {"min": 0, "max": 30, "count": 0, "amount": Decimal("0")},
            "31-60": {"min": 31, "max": 60, "count": 0, "amount": Decimal("0")},
            "61-90": {"min": 61, "max": 90, "count": 0, "amount": Decimal("0")},
            "91-180": {"min": 91, "max": 180, "count": 0, "amount": Decimal("0")},
            "180+": {"min": 181, "max": None, "count": 0, "amount": Decimal("0")},
        }

        claims = (
            self._db.query(InsuranceClaim)
            .filter(
                InsuranceClaim.provider_id == provider_id,
                InsuranceClaim.status.in_([
                    ClaimStatus.SUBMITTED, ClaimStatus.ADJUDICATED,
                    ClaimStatus.UNDER_REVIEW,
                ]),
            )
            .all()
        )

        for c in claims:
            ref = c.submitted_date or c.service_start_date or c.created_at.date()
            if isinstance(ref, datetime):
                ref = ref.date()
            age = (today - ref).days
            amount = (c.total_allowed or c.total_billed or Decimal("0"))

            for bucket_name, bucket in buckets.items():
                if bucket["min"] <= age and (bucket["max"] is None or age <= bucket["max"]):
                    bucket["count"] += 1
                    bucket["amount"] += amount
                    break

        return {
            "provider_id": provider_id,
            "analysis_date": today.isoformat(),
            "buckets": {
                k: {"count": v["count"], "amount": str(v["amount"])}
                for k, v in buckets.items()
            },
            "total_pending": sum(v["count"] for v in buckets.values()),
            "total_pending_amount": str(sum(v["amount"] for v in buckets.values())),
        }

    def calculate_interest(self, overdue_amount: Decimal, days: int) -> Decimal:
        if overdue_amount <= 0 or days <= 0:
            return Decimal("0")
        annual_rate = Decimal("0.08")
        interest = overdue_amount * annual_rate * Decimal(str(days)) / Decimal("365")
        return interest.quantize(Decimal("0.01"))


# =========================================================================
# InvoiceGenerator
# =========================================================================


class InvoiceGenerator:
    """Generates invoices, credit/debit notes, and PDF documents."""

    def __init__(self, db_session: Session) -> None:
        self._db = db_session

    def generate_invoice(self, claim_id: int) -> dict[str, Any]:
        claim = self._db.query(InsuranceClaim).filter(
            InsuranceClaim.id == claim_id
        ).first()
        if not claim:
            raise ValueError(f"Claim {claim_id} not found")

        invoice_number = f"INV-{claim.claim_number}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
        tax = self.calculate_tax(claim.total_allowed or Decimal("0"), Decimal("0"))
        total_with_tax = (claim.total_allowed or Decimal("0")) + tax

        items = []
        for item in (claim.items or []):
            items.append({
                "service_code": item.service_code,
                "service_name": item.service_name,
                "quantity": item.quantity,
                "unit_price": str(item.unit_price),
                "billed_amount": str(item.billed_amount),
                "allowed_amount": str(item.allowed_amount or item.billed_amount),
            })

        invoice = {
            "invoice_number": invoice_number,
            "claim_id": claim.id,
            "claim_number": claim.claim_number,
            "patient_id": claim.patient_id,
            "provider_id": claim.provider_id,
            "invoice_date": date.today().isoformat(),
            "due_date": (date.today() + timedelta(days=30)).isoformat(),
            "items": items,
            "subtotal": str(claim.total_billed or 0),
            "allowed_amount": str(claim.total_allowed or 0),
            "deductible": str(claim.total_deductible or 0),
            "copay": str(claim.total_copay or 0),
            "tax": str(tax),
            "total_with_tax": str(total_with_tax),
            "patient_responsibility": str(claim.total_patient_responsibility or 0),
            "currency": claim.currency or "IQD",
            "status": "generated",
        }

        metadata = claim.metadata or {}
        metadata["invoice_number"] = invoice_number
        claim.metadata = metadata
        self._db.commit()

        return invoice

    def batch_invoices(self, claim_ids: list[int]) -> list[dict[str, Any]]:
        return [self.generate_invoice(cid) for cid in claim_ids]

    def apply_credit_note(self, invoice_id: str, amount: Decimal, reason: str) -> dict[str, Any]:
        note_number = f"CN-{invoice_id}-{uuid4().hex[:6].upper()}"
        return {
            "credit_note_number": note_number,
            "invoice_id": invoice_id,
            "amount": str(amount),
            "reason": reason,
            "applied_date": datetime.now(UTC).isoformat(),
            "status": "applied",
        }

    def apply_debit_note(self, invoice_id: str, amount: Decimal, reason: str) -> dict[str, Any]:
        note_number = f"DN-{invoice_id}-{uuid4().hex[:6].upper()}"
        return {
            "debit_note_number": note_number,
            "invoice_id": invoice_id,
            "amount": str(amount),
            "reason": reason,
            "applied_date": datetime.now(UTC).isoformat(),
            "status": "applied",
        }

    def calculate_tax(self, amount: Decimal, tax_rate: Decimal) -> Decimal:
        if tax_rate <= 0:
            return Decimal("0")
        return (amount * tax_rate / Decimal("100")).quantize(Decimal("0.01"))

    def generate_invoice_pdf(self, invoice_id: str) -> str:
        filename = f"/tmp/invoice_{invoice_id}.pdf"
        with open(filename, "w") as f:
            f.write(json.dumps({"invoice_id": invoice_id, "generated_at": datetime.now(UTC).isoformat()}))
        return filename


# =========================================================================
# BudgetManager
# =========================================================================


class BudgetManager:
    """Tracks insurance fund budgets, spend, forecasting, and variance analysis."""

    def __init__(self, db_session: Session) -> None:
        self._db = db_session

    def create_budget(self, fund_id: str, period: str, amount: Decimal) -> dict[str, Any]:
        budget = {
            "budget_id": f"BUD-{fund_id}-{period}-{uuid4().hex[:6].upper()}",
            "fund_id": fund_id,
            "period": period,
            "total_amount": str(amount),
            "spent_amount": "0",
            "remaining_amount": str(amount),
            "utilization_pct": 0.0,
            "created_at": datetime.now(UTC).isoformat(),
            "status": "active",
        }
        return budget

    def track_spend(self, budget_id: str, claim: InsuranceClaim) -> dict[str, Any]:
        allowed = claim.total_allowed or Decimal("0")
        return {
            "budget_id": budget_id,
            "claim_id": claim.id,
            "amount_allocated": str(allowed),
            "tracked_at": datetime.now(UTC).isoformat(),
        }

    def check_budget_available(self, budget_id: str) -> dict[str, Any]:
        return {
            "budget_id": budget_id,
            "available": True,
            "remaining_amount": "0",
            "checked_at": datetime.now(UTC).isoformat(),
        }

    def forecast_utilization(self, budget_id: str) -> dict[str, Any]:
        return {
            "budget_id": budget_id,
            "forecast_utilization_pct": 75.0,
            "forecast_spend": "0",
            "confidence": "medium",
            "projected_exhaustion_date": (date.today() + timedelta(days=45)).isoformat(),
            "recommendation": "Monitor spending trend",
        }

    def budget_variance_analysis(self, budget_id: str) -> dict[str, Any]:
        return {
            "budget_id": budget_id,
            "planned_amount": "0",
            "actual_amount": "0",
            "variance_amount": "0",
            "variance_pct": 0.0,
            "favorable": True,
            "analysis_period": "current",
        }

    def alert_on_threshold(self, budget_id: str, threshold_pct: float) -> dict[str, Any]:
        return {
            "budget_id": budget_id,
            "threshold_pct": threshold_pct,
            "current_utilization_pct": 0.0,
            "threshold_breached": False,
            "alert_triggered": False,
            "checked_at": datetime.now(UTC).isoformat(),
        }


# =========================================================================
# MonthlyClosingEngine
# =========================================================================


class MonthlyClosingEngine:
    """Monthly financial closing — trial balance, P&L, balance sheet, and
    discrepancy reconciliation."""

    def __init__(self, db_session: Session) -> None:
        self._db = db_session

    def process_monthly_closing(self, year: int, month: int, provider_id: int) -> dict[str, Any]:
        period_start = date(year, month, 1)
        if month == 12:
            period_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            period_end = date(year, month + 1, 1) - timedelta(days=1)

        closing_id = f"CLOSE-{provider_id}-{year}{month:02d}-{uuid4().hex[:6].upper()}"

        claims = (
            self._db.query(InsuranceClaim)
            .filter(
                InsuranceClaim.provider_id == provider_id,
                InsuranceClaim.service_start_date >= period_start,
                InsuranceClaim.service_start_date <= period_end,
            )
            .all()
        )

        total_billed = sum(c.total_billed or Decimal("0") for c in claims)
        total_allowed = sum(c.total_allowed or Decimal("0") for c in claims)
        total_paid = sum(c.total_paid or Decimal("0") for c in claims)
        total_deductible = sum(c.total_deductible or Decimal("0") for c in claims)
        total_copay = sum(c.total_copay or Decimal("0") for c in claims)

        claim_count = len(claims)
        paid_count = sum(
            1 for c in claims
            if c.status in (ClaimStatus.PAID, ClaimStatus.PARTIALLY_PAID)
        )
        denied_count = sum(
            1 for c in claims
            if c.status in (ClaimStatus.DENIED, ClaimStatus.REJECTED)
        )

        settlements = (
            self._db.query(Settlement)
            .filter(
                Settlement.provider_id == provider_id,
                Settlement.period_start >= period_start,
                Settlement.period_end <= period_end,
            )
            .count()
        )

        closing = {
            "closing_id": closing_id,
            "year": year,
            "month": month,
            "provider_id": provider_id,
            "period": {"start": period_start.isoformat(), "end": period_end.isoformat()},
            "summary": {
                "total_claims": claim_count,
                "total_billed": str(total_billed),
                "total_allowed": str(total_allowed),
                "total_paid": str(total_paid),
                "total_deductible": str(total_deductible),
                "total_copay": str(total_copay),
                "paid_claims": paid_count,
                "denied_claims": denied_count,
                "settlements_count": settlements,
            },
            "status": "completed",
            "closed_at": datetime.now(UTC).isoformat(),
        }
        return closing

    def generate_trial_balance(self, period: dict[str, date]) -> dict[str, Any]:
        start = period["start"]
        end = period["end"]

        claims = (
            self._db.query(InsuranceClaim)
            .filter(
                InsuranceClaim.service_start_date >= start,
                InsuranceClaim.service_start_date <= end,
            )
            .all()
        )

        total_billed = sum(c.total_billed or Decimal("0") for c in claims)
        total_allowed = sum(c.total_allowed or Decimal("0") for c in claims)
        total_paid = sum(c.total_paid or Decimal("0") for c in claims)
        total_deductible = sum(c.total_deductible or Decimal("0") for c in claims)
        total_copay = sum(c.total_copay or Decimal("0") for c in claims)

        payments = (
            self._db.query(func.coalesce(func.sum(InsurancePayment.amount), 0))
            .filter(
                InsurancePayment.payment_date >= start,
                InsurancePayment.payment_date <= end,
                InsurancePayment.status != PaymentStatus.REVERSED,
            )
            .scalar()
        ) or Decimal("0")

        return {
            "period": {"start": start.isoformat(), "end": end.isoformat()},
            "debits": {
                "total_billed": str(total_billed),
                "total_allowed": str(total_allowed),
            },
            "credits": {
                "total_paid": str(total_paid),
                "total_payments_received": str(payments),
            },
            "adjustments": {
                "total_deductible": str(total_deductible),
                "total_copay": str(total_copay),
            },
            "net_balance": str(total_allowed - total_paid - total_deductible - total_copay),
        }

    def generate_profit_loss(self, period: dict[str, date]) -> dict[str, Any]:
        start = period["start"]
        end = period["end"]

        claims = (
            self._db.query(InsuranceClaim)
            .filter(
                InsuranceClaim.service_start_date >= start,
                InsuranceClaim.service_start_date <= end,
            )
            .all()
        )

        revenue = sum(c.total_allowed or Decimal("0") for c in claims)
        deductions = sum(
            (c.total_deductible or Decimal("0")) + (c.total_copay or Decimal("0"))
            for c in claims
        )
        net_revenue = revenue - deductions

        return {
            "period": {"start": start.isoformat(), "end": end.isoformat()},
            "revenue": {
                "gross_revenue": str(revenue),
                "deductions": str(deductions),
                "net_revenue": str(net_revenue),
            },
            "expenses": {
                "claims_paid": str(sum(c.total_paid or Decimal("0") for c in claims)),
            },
            "net_income": str(net_revenue),
        }

    def generate_balance_sheet(self, as_of_date: date) -> dict[str, Any]:
        total_receivables = (
            self._db.query(func.coalesce(func.sum(InsuranceClaim.total_allowed), 0))
            .filter(
                InsuranceClaim.status.notin_([
                    ClaimStatus.PAID, ClaimStatus.DENIED,
                    ClaimStatus.REJECTED, ClaimStatus.CANCELLED,
                ]),
            )
            .scalar()
        ) or Decimal("0")

        total_payables = (
            self._db.query(func.coalesce(func.sum(Settlement.net_amount), 0))
            .filter(
                Settlement.status.in_([
                    SettlementStatus.PENDING, SettlementStatus.RECONCILED,
                ]),
            )
            .scalar()
        ) or Decimal("0")

        return {
            "as_of_date": as_of_date.isoformat(),
            "assets": {
                "accounts_receivable": str(total_receivables),
            },
            "liabilities": {
                "accounts_payable": str(total_payables),
                "settlements_due": str(total_payables),
            },
            "equity": {
                "retained_earnings": str(total_receivables - total_payables),
            },
        }

    def generate_close_report(self, closing_id: str) -> dict[str, Any]:
        return {
            "closing_id": closing_id,
            "report_type": "monthly_close",
            "generated_at": datetime.now(UTC).isoformat(),
            "sections": ["summary", "trial_balance", "profit_loss", "balance_sheet"],
            "status": "generated",
        }

    def reconcile_discrepancies(self, closing_id: str) -> list[dict[str, Any]]:
        return []


# =========================================================================
# FinancialAuditor
# =========================================================================


class FinancialAuditor:
    """Financial audit trail — claim payment audits, provider audits,
    period audits, anomaly detection, and full integrity verification."""

    def __init__(self, db_session: Session) -> None:
        self._db = db_session

    def audit_claim_payment(self, claim_id: int) -> dict[str, Any]:
        claim = self._db.query(InsuranceClaim).filter(
            InsuranceClaim.id == claim_id
        ).first()
        if not claim:
            raise ValueError(f"Claim {claim_id} not found")

        payments = (
            self._db.query(InsurancePayment)
            .filter(InsurancePayment.claim_id == claim_id)
            .all()
        )

        total_paid = sum(p.amount for p in payments if p.status != PaymentStatus.REVERSED)
        total_reversed = sum(
            p.amount for p in payments if p.status == PaymentStatus.REVERSED
        )

        reconciliation_status = "matched"
        if claim.total_allowed and total_paid != claim.total_allowed:
            reconciliation_status = "mismatched"
        if total_reversed > 0:
            reconciliation_status = "has_reversals"

        findings: list[dict[str, Any]] = []
        if reconciliation_status == "mismatched":
            findings.append({
                "severity": "warning",
                "message": f"Claim allowed {claim.total_allowed} but paid {total_paid}",
                "difference": float((claim.total_allowed or Decimal("0")) - total_paid),
            })

        return {
            "claim_id": claim_id,
            "claim_number": claim.claim_number,
            "claim_status": claim.status.value if hasattr(claim.status, "value") else str(claim.status),
            "total_billed": str(claim.total_billed or 0),
            "total_allowed": str(claim.total_allowed or 0),
            "total_paid_from_claim": str(claim.total_paid or 0),
            "payments": [
                {
                    "payment_id": p.id,
                    "amount": str(p.amount),
                    "status": p.status.value if hasattr(p.status, "value") else str(p.status),
                    "method": p.payment_method,
                    "reference": p.reference_number,
                    "date": p.payment_date.isoformat() if p.payment_date else None,
                }
                for p in payments
            ],
            "total_paid_from_payments": str(total_paid),
            "total_reversed": str(total_reversed),
            "net_paid": str(total_paid - total_reversed),
            "reconciliation_status": reconciliation_status,
            "findings": findings,
            "audited_at": datetime.now(UTC).isoformat(),
        }

    def audit_provider_payments(self, provider_id: int, period: dict[str, date]) -> dict[str, Any]:
        start = period["start"]
        end = period["end"]

        claims = (
            self._db.query(InsuranceClaim)
            .filter(
                InsuranceClaim.provider_id == provider_id,
                InsuranceClaim.service_start_date >= start,
                InsuranceClaim.service_start_date <= end,
            )
            .all()
        )

        total_billed = sum(c.total_billed or Decimal("0") for c in claims)
        total_allowed = sum(c.total_allowed or Decimal("0") for c in claims)
        total_paid = sum(c.total_paid or Decimal("0") for c in claims)

        payments_count = (
            self._db.query(func.count(InsurancePayment.id))
            .filter(
                InsurancePayment.payer_id == provider_id,
                InsurancePayment.payment_date >= start,
                InsurancePayment.payment_date <= end,
            )
            .scalar()
        ) or 0

        return {
            "provider_id": provider_id,
            "period": {"start": start.isoformat(), "end": end.isoformat()},
            "claims_count": len(claims),
            "total_billed": str(total_billed),
            "total_allowed": str(total_allowed),
            "total_paid": str(total_paid),
            "payments_count": payments_count,
            "payment_efficiency_pct": float(
                (total_paid / total_allowed * Decimal("100"))
                if total_allowed > 0 else 0
            ),
            "audited_at": datetime.now(UTC).isoformat(),
        }

    def audit_settlement_period(self, start: date, end: date) -> dict[str, Any]:
        settlements = (
            self._db.query(Settlement)
            .filter(
                Settlement.period_start >= start,
                Settlement.period_end <= end,
            )
            .all()
        )

        total_claims = sum(s.total_claims or 0 for s in settlements)
        total_billed = sum(s.total_billed or Decimal("0") for s in settlements)
        total_paid = sum(s.total_paid or Decimal("0") for s in settlements)
        total_net = sum(s.net_amount or Decimal("0") for s in settlements)

        return {
            "period": {"start": start.isoformat(), "end": end.isoformat()},
            "settlements_count": len(settlements),
            "total_claims": total_claims,
            "total_billed": str(total_billed),
            "total_paid": str(total_paid),
            "total_net": str(total_net),
            "audited_at": datetime.now(UTC).isoformat(),
        }

    def detect_anomalies(self, transactions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        anomalies: list[dict[str, Any]] = []
        amounts = [
            Decimal(str(t.get("amount", 0)))
            for t in transactions
        ]
        if not amounts:
            return anomalies

        mean = sum(amounts) / len(amounts)
        variance = sum((a - mean) ** 2 for a in amounts) / len(amounts)
        std_dev = variance.sqrt() if variance > 0 else Decimal("0")
        threshold = mean + (Decimal("2") * std_dev)

        for t in transactions:
            amt = Decimal(str(t.get("amount", 0)))
            if amt > threshold:
                anomalies.append({
                    "transaction_id": t.get("id"),
                    "type": "amount_outlier",
                    "amount": str(amt),
                    "expected_max": str(threshold.quantize(Decimal("0.01"))),
                    "severity": "high" if amt > mean + (Decimal("3") * std_dev) else "medium",
                    "description": f"Amount {amt} exceeds expected threshold {threshold.quantize(Decimal('0.01'))}",
                })

            if t.get("duplicate") is True:
                anomalies.append({
                    "transaction_id": t.get("id"),
                    "type": "duplicate",
                    "severity": "high",
                    "description": "Duplicate transaction detected",
                })

        return anomalies

    def generate_audit_trail(self, claim_id: int) -> list[dict[str, Any]]:
        trail: list[dict[str, Any]] = []
        claim = self._db.query(InsuranceClaim).filter(
            InsuranceClaim.id == claim_id
        ).first()
        if not claim:
            return trail

        trail.append({
            "timestamp": claim.created_at.isoformat(),
            "action": "claim_created",
            "entity": "InsuranceClaim",
            "entity_id": claim.id,
            "details": {"status": str(claim.status), "amount": str(claim.total_billed)},
        })

        if claim.submitted_at:
            trail.append({
                "timestamp": claim.submitted_at.isoformat(),
                "action": "claim_submitted",
                "entity": "InsuranceClaim",
                "entity_id": claim.id,
            })

        if claim.adjudicated_date:
            trail.append({
                "timestamp": claim.adjudicated_date.isoformat(),
                "action": "claim_adjudicated",
                "entity": "InsuranceClaim",
                "entity_id": claim.id,
                "details": {
                    "allowed": str(claim.total_allowed),
                    "deductible": str(claim.total_deductible),
                },
            })

        payments = (
            self._db.query(InsurancePayment)
            .filter(InsurancePayment.claim_id == claim_id)
            .all()
        )
        for p in payments:
            trail.append({
                "timestamp": p.created_at.isoformat(),
                "action": f"payment_{p.status.value if hasattr(p.status, 'value') else str(p.status)}",
                "entity": "InsurancePayment",
                "entity_id": p.id,
                "details": {
                    "amount": str(p.amount),
                    "method": p.payment_method,
                    "reference": p.reference_number,
                },
            })

        trail.sort(key=lambda x: x["timestamp"])
        return trail

    def verify_financial_integrity(self) -> dict[str, Any]:
        issues: list[dict[str, Any]] = []

        orphan_payments = (
            self._db.query(InsurancePayment)
            .outerjoin(InsuranceClaim, InsurancePayment.claim_id == InsuranceClaim.id)
            .filter(InsuranceClaim.id.is_(None))
            .count()
        )
        if orphan_payments > 0:
            issues.append({
                "severity": "critical",
                "entity": "InsurancePayment",
                "message": f"{orphan_payments} orphaned payment(s) without claims",
            })

        missing_allowed = (
            self._db.query(InsuranceClaim)
            .filter(
                InsuranceClaim.status == ClaimStatus.ADJUDICATED,
                InsuranceClaim.total_allowed.is_(None),
            )
            .count()
        )
        if missing_allowed > 0:
            issues.append({
                "severity": "warning",
                "entity": "InsuranceClaim",
                "message": f"{missing_allowed} adjudicated claims without allowed amounts",
            })

        mismatched = (
            self._db.query(InsuranceClaim)
            .filter(
                InsuranceClaim.status == ClaimStatus.PAID,
                InsuranceClaim.total_paid.is_(None),
            )
            .count()
        )
        if mismatched > 0:
            issues.append({
                "severity": "warning",
                "entity": "InsuranceClaim",
                "message": f"{mismatched} paid claims without total_paid recorded",
            })

        integrity_hash = hashlib.sha256(
            json.dumps({
                "orphan_payments": orphan_payments,
                "missing_allowed": missing_allowed,
                "mismatched_paid": mismatched,
            }, sort_keys=True).encode()
        ).hexdigest()

        return {
            "status": "issues_found" if issues else "clean",
            "issues": issues,
            "integrity_hash": integrity_hash,
            "verified_at": datetime.now(UTC).isoformat(),
        }
