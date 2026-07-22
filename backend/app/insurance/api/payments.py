from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.database import get_db
from app.insurance.domain.enums import ClaimStatus, PaymentStatus, SettlementStatus
from app.insurance.domain.models import (
    InsuranceClaim,
    InsurancePayment,
    InsuranceProvider,
    Settlement,
)
from app.models.lab_user import LabUser
from app.security.dependencies import get_current_user
from app.services.audit_service import log_action

router = APIRouter(prefix="/payments", tags=["insurance-payments"])


class PaymentCreate(BaseModel):
    claim_id: int
    payer_id: int
    amount: Decimal
    currency: str = "IQD"
    payment_method: str | None = None
    payment_date: date | None = None
    reference_number: str | None = None
    adjustment_amount: Decimal | None = Decimal("0")
    adjustment_reason: str | None = None
    notes: str | None = None


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lab_id: int
    claim_id: int
    payer_id: int
    payment_number: str
    status: PaymentStatus
    amount: Decimal
    currency: str
    payment_method: str | None = None
    payment_date: date | None = None
    reference_number: str | None = None
    adjustment_amount: Decimal | None = None
    adjustment_reason: str | None = None
    notes: str | None = None
    created_at: str | None = None
    processed_at: str | None = None


class SettlementCreate(BaseModel):
    provider_id: int
    period_start: date
    period_end: date
    notes: str | None = None


class SettlementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lab_id: int
    provider_id: int
    period_start: date
    period_end: date
    status: SettlementStatus
    settlement_number: str
    total_claims: int
    total_billed: Decimal
    total_allowed: Decimal | None = None
    total_paid: Decimal | None = None
    total_adjustments: Decimal | None = None
    total_deductible: Decimal | None = None
    total_copay: Decimal | None = None
    net_amount: Decimal | None = None
    currency: str
    notes: str | None = None
    reconciled_at: str | None = None
    paid_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class BudgetCreate(BaseModel):
    provider_id: int
    fiscal_year: int
    total_budget: Decimal
    currency: str = "IQD"
    notes: str | None = None


class BudgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)


def _generate_payment_number() -> str:
    return f"PAY-{uuid4().hex[:12].upper()}"


def _generate_settlement_number() -> str:
    return f"SET-{uuid4().hex[:12].upper()}"


@router.get("", response_model=list[PaymentResponse])
def list_payments(
    claim_id: int | None = Query(None),
    payer_id: int | None = Query(None),
    status: PaymentStatus | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(InsurancePayment).filter(InsurancePayment.lab_id == current_user.lab_id)
    if claim_id:
        q = q.filter(InsurancePayment.claim_id == claim_id)
    if payer_id:
        q = q.filter(InsurancePayment.payer_id == payer_id)
    if status:
        q = q.filter(InsurancePayment.status == status)
    if date_from:
        q = q.filter(InsurancePayment.payment_date >= date_from)
    if date_to:
        q = q.filter(InsurancePayment.payment_date <= date_to)
    return q.order_by(InsurancePayment.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payment = db.query(InsurancePayment).filter(
        InsurancePayment.id == payment_id,
        InsurancePayment.lab_id == current_user.lab_id,
    ).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.post("", status_code=201, response_model=PaymentResponse)
def record_payment(
    data: PaymentCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    claim = db.query(InsuranceClaim).filter(
        InsuranceClaim.id == data.claim_id,
        InsuranceClaim.lab_id == current_user.lab_id,
    ).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    payer = db.query(InsuranceProvider).filter(
        InsuranceProvider.id == data.payer_id,
        InsuranceProvider.lab_id == current_user.lab_id,
    ).first()
    if not payer:
        raise HTTPException(status_code=404, detail="Payer not found")

    payment = InsurancePayment(
        lab_id=current_user.lab_id,
        payment_number=_generate_payment_number(),
        status=PaymentStatus.PENDING,
        **data.model_dump(),
    )
    db.add(payment)
    db.flush()

    claim.status = ClaimStatus.PAID
    claim.paid_date = data.payment_date or date.today()

    log_action(
        db=db,
        action="insurance.payment.create",
        resource_type="insurance_payment",
        resource_id=payment.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Recorded payment '{payment.payment_number}' for claim {claim.claim_number}, amount={data.amount}",
    )
    db.commit()
    db.refresh(payment)
    return payment


@router.post("/{payment_id}/reverse", response_model=PaymentResponse)
def reverse_payment(
    payment_id: int,
    reason: str = Query(..., min_length=1),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payment = db.query(InsurancePayment).filter(
        InsurancePayment.id == payment_id,
        InsurancePayment.lab_id == current_user.lab_id,
    ).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.status == PaymentStatus.REVERSED:
        raise HTTPException(status_code=400, detail="Payment is already reversed")

    payment.status = PaymentStatus.REVERSED
    payment.notes = (payment.notes or "") + f" | Reversed: {reason}"

    log_action(
        db=db,
        action="insurance.payment.reverse",
        resource_type="insurance_payment",
        resource_id=payment.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Reversed payment '{payment.payment_number}': {reason}",
    )
    db.commit()
    db.refresh(payment)
    return payment


@router.post("/{payment_id}/reconcile", response_model=PaymentResponse)
def reconcile_payment(
    payment_id: int,
    reference_number: str | None = Query(None),
    notes: str | None = Query(None),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payment = db.query(InsurancePayment).filter(
        InsurancePayment.id == payment_id,
        InsurancePayment.lab_id == current_user.lab_id,
    ).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.status == PaymentStatus.REVERSED:
        raise HTTPException(status_code=400, detail="Cannot reconcile a reversed payment")

    payment.status = PaymentStatus.COMPLETED
    payment.processed_at = datetime.utcnow()
    if reference_number:
        payment.reference_number = reference_number
    if notes:
        payment.notes = (payment.notes or "") + f" | Reconciled: {notes}"

    log_action(
        db=db,
        action="insurance.payment.reconcile",
        resource_type="insurance_payment",
        resource_id=payment.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Reconciled payment '{payment.payment_number}'",
    )
    db.commit()
    db.refresh(payment)
    return payment


@router.get("/settlements", response_model=list[SettlementResponse])
def list_settlements(
    provider_id: int | None = Query(None),
    status: SettlementStatus | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Settlement).filter(Settlement.lab_id == current_user.lab_id)
    if provider_id:
        q = q.filter(Settlement.provider_id == provider_id)
    if status:
        q = q.filter(Settlement.status == status)
    if date_from:
        q = q.filter(Settlement.period_start >= date_from)
    if date_to:
        q = q.filter(Settlement.period_end <= date_to)
    return q.order_by(Settlement.created_at.desc()).offset(skip).limit(limit).all()


@router.post("/settlements", status_code=201, response_model=SettlementResponse)
def create_settlement(
    data: SettlementCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    provider = db.query(InsuranceProvider).filter(
        InsuranceProvider.id == data.provider_id,
        InsuranceProvider.lab_id == current_user.lab_id,
    ).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    existing = db.query(Settlement).filter(
        Settlement.lab_id == current_user.lab_id,
        Settlement.provider_id == data.provider_id,
        Settlement.period_start == data.period_start,
        Settlement.period_end == data.period_end,
        Settlement.status != SettlementStatus.CANCELLED,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Settlement already exists for this period")

    claims = db.query(InsuranceClaim).filter(
        InsuranceClaim.lab_id == current_user.lab_id,
        InsuranceClaim.provider_id == data.provider_id,
        InsuranceClaim.status.in_(["paid", "partially_paid"]),
        InsuranceClaim.paid_date >= data.period_start,
        InsuranceClaim.paid_date <= data.period_end,
    ).all()

    total_billed = sum(c.total_billed for c in claims)
    total_paid = sum(c.total_paid or Decimal("0") for c in claims)
    total_allowed = sum(c.total_allowed or Decimal("0") for c in claims)

    settlement = Settlement(
        lab_id=current_user.lab_id,
        settlement_number=_generate_settlement_number(db, current_user.lab_id),
        status=SettlementStatus.PENDING,
        total_claims=len(claims),
        total_billed=total_billed,
        total_allowed=total_allowed,
        total_paid=total_paid,
        net_amount=total_paid,
        **data.model_dump(),
    )
    db.add(settlement)
    db.flush()

    log_action(
        db=db,
        action="insurance.settlement.create",
        resource_type="settlement",
        resource_id=settlement.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Created settlement '{settlement.settlement_number}' for provider {provider.name}",
    )
    db.commit()
    db.refresh(settlement)
    return settlement


@router.post("/settlements/{settlement_id}/calculate", response_model=SettlementResponse)
def calculate_settlement(
    settlement_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settlement = db.query(Settlement).filter(
        Settlement.id == settlement_id,
        Settlement.lab_id == current_user.lab_id,
    ).first()
    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")

    claims = db.query(InsuranceClaim).filter(
        InsuranceClaim.lab_id == current_user.lab_id,
        InsuranceClaim.provider_id == settlement.provider_id,
        InsuranceClaim.status.in_(["paid", "partially_paid"]),
        InsuranceClaim.paid_date >= settlement.period_start,
        InsuranceClaim.paid_date <= settlement.period_end,
    ).all()

    settlement.total_claims = len(claims)
    settlement.total_billed = sum(c.total_billed for c in claims)
    settlement.total_allowed = sum(c.total_allowed or Decimal("0") for c in claims)
    settlement.total_paid = sum(c.total_paid or Decimal("0") for c in claims)
    settlement.total_deductible = sum(c.total_deductible or Decimal("0") for c in claims)
    settlement.total_copay = sum(c.total_copay or Decimal("0") for c in claims)
    settlement.net_amount = settlement.total_paid

    log_action(
        db=db,
        action="insurance.settlement.calculate",
        resource_type="settlement",
        resource_id=settlement.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Calculated settlement '{settlement.settlement_number}', net={settlement.net_amount}",
    )
    db.commit()
    db.refresh(settlement)
    return settlement


@router.post("/settlements/{settlement_id}/reconcile", response_model=SettlementResponse)
def reconcile_settlement(
    settlement_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settlement = db.query(Settlement).filter(
        Settlement.id == settlement_id,
        Settlement.lab_id == current_user.lab_id,
    ).first()
    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")
    if settlement.status in (SettlementStatus.COMPLETED, SettlementStatus.CANCELLED):
        raise HTTPException(status_code=400, detail=f"Settlement is already {settlement.status.value}")

    settlement.status = SettlementStatus.RECONCILED
    settlement.reconciled_at = datetime.utcnow()

    log_action(
        db=db,
        action="insurance.settlement.reconcile",
        resource_type="settlement",
        resource_id=settlement.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Reconciled settlement '{settlement.settlement_number}'",
    )
    db.commit()
    db.refresh(settlement)
    return settlement


@router.post("/settlements/{settlement_id}/close", response_model=SettlementResponse)
def close_settlement(
    settlement_id: int,
    paid_at: date | None = Query(None),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settlement = db.query(Settlement).filter(
        Settlement.id == settlement_id,
        Settlement.lab_id == current_user.lab_id,
    ).first()
    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")
    if settlement.status == SettlementStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Settlement is already closed")

    settlement.status = SettlementStatus.COMPLETED
    settlement.paid_at = datetime.combine(paid_at or date.today(), datetime.min.time()) if paid_at else datetime.utcnow()

    log_action(
        db=db,
        action="insurance.settlement.close",
        resource_type="settlement",
        resource_id=settlement.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Closed settlement '{settlement.settlement_number}'",
    )
    db.commit()
    db.refresh(settlement)
    return settlement


@router.get("/settlements/{settlement_id}/report", response_model=dict)
def settlement_report(
    settlement_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settlement = db.query(Settlement).filter(
        Settlement.id == settlement_id,
        Settlement.lab_id == current_user.lab_id,
    ).first()
    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")

    claims = db.query(InsuranceClaim).filter(
        InsuranceClaim.lab_id == current_user.lab_id,
        InsuranceClaim.provider_id == settlement.provider_id,
        InsuranceClaim.status.in_(["paid", "partially_paid"]),
        InsuranceClaim.paid_date >= settlement.period_start,
        InsuranceClaim.paid_date <= settlement.period_end,
    ).all()

    return {
        "settlement_id": settlement.id,
        "settlement_number": settlement.settlement_number,
        "provider_id": settlement.provider_id,
        "period": {
            "start": settlement.period_start.isoformat(),
            "end": settlement.period_end.isoformat(),
        },
        "status": settlement.status.value,
        "totals": {
            "total_claims": settlement.total_claims,
            "total_billed": float(settlement.total_billed),
            "total_allowed": float(settlement.total_allowed or 0),
            "total_paid": float(settlement.total_paid or 0),
            "total_adjustments": float(settlement.total_adjustments or 0),
            "total_deductible": float(settlement.total_deductible or 0),
            "total_copay": float(settlement.total_copay or 0),
            "net_amount": float(settlement.net_amount or 0),
        },
        "claims": [
            {
                "id": c.id,
                "claim_number": c.claim_number,
                "status": c.status.value,
                "total_billed": float(c.total_billed),
                "total_paid": float(c.total_paid or 0),
                "paid_date": c.paid_date.isoformat() if c.paid_date else None,
            }
            for c in claims
        ],
        "created_at": settlement.created_at.isoformat() if settlement.created_at else None,
        "reconciled_at": settlement.reconciled_at.isoformat() if settlement.reconciled_at else None,
    }


@router.get("/budgets", response_model=list[dict])
def list_budgets(
    provider_id: int | None = Query(None),
    fiscal_year: int | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.models.audit_log import AuditLog

    db.query(AuditLog).filter(
        AuditLog.action == "insurance.budget",
        AuditLog.details.ilike(f"%provider_id={provider_id}%") if provider_id else True,
    ).order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all() if False else []

    stored = db.execute(
        f"SELECT id, provider_id, fiscal_year, total_budget, currency, spent, notes, created_at "
        f"FROM ins_budgets WHERE lab_id = :lab_id"
        f"{' AND provider_id = :pid' if provider_id else ''}"
        f"{' AND fiscal_year = :fy' if fiscal_year else ''}"
        f" ORDER BY fiscal_year DESC LIMIT :lim OFFSET :off",
        {
            "lab_id": current_user.lab_id,
            "pid": provider_id,
            "fy": fiscal_year,
            "lim": limit,
            "off": skip,
        },
    ).fetchall()

    return [
        {
            "id": row[0],
            "provider_id": row[1],
            "fiscal_year": row[2],
            "total_budget": float(row[3]),
            "currency": row[4],
            "spent": float(row[5] or 0),
            "remaining": float(row[3] - (row[5] or 0)),
            "notes": row[6],
            "created_at": row[7].isoformat() if row[7] else None,
        }
        for row in stored
    ]


@router.post("/budgets", status_code=201, response_model=dict)
def create_budget(
    data: BudgetCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    provider = db.query(InsuranceProvider).filter(
        InsuranceProvider.id == data.provider_id,
        InsuranceProvider.lab_id == current_user.lab_id,
    ).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    existing = db.execute(
        "SELECT id FROM ins_budgets WHERE lab_id = :lab_id AND provider_id = :pid AND fiscal_year = :fy",
        {"lab_id": current_user.lab_id, "pid": data.provider_id, "fy": data.fiscal_year},
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Budget already exists for provider {data.provider_id} in FY {data.fiscal_year}",
        )

    result = db.execute(
        "INSERT INTO ins_budgets (lab_id, provider_id, fiscal_year, total_budget, currency, notes, spent, created_at) "
        "VALUES (:lab_id, :pid, :fy, :total, :cur, :notes, 0, NOW()) "
        "RETURNING id",
        {
            "lab_id": current_user.lab_id,
            "pid": data.provider_id,
            "fy": data.fiscal_year,
            "total": float(data.total_budget),
            "cur": data.currency,
            "notes": data.notes or "",
        },
    )
    budget_id = result.first()[0]
    db.commit()

    log_action(
        db=db,
        action="insurance.budget.create",
        resource_type="insurance_budget",
        resource_id=budget_id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Created budget for provider {provider.name} FY {data.fiscal_year}, total={data.total_budget}",
    )
    db.commit()

    return {
        "id": budget_id,
        "provider_id": data.provider_id,
        "fiscal_year": data.fiscal_year,
        "total_budget": float(data.total_budget),
        "currency": data.currency,
        "spent": 0,
        "remaining": float(data.total_budget),
        "notes": data.notes,
    }


@router.get("/budgets/{budget_id}", response_model=dict)
def get_budget(
    budget_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.execute(
        "SELECT id, provider_id, fiscal_year, total_budget, currency, spent, notes, created_at "
        "FROM ins_budgets WHERE id = :id AND lab_id = :lab_id",
        {"id": budget_id, "lab_id": current_user.lab_id},
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Budget not found")

    return {
        "id": row[0],
        "provider_id": row[1],
        "fiscal_year": row[2],
        "total_budget": float(row[3]),
        "currency": row[4],
        "spent": float(row[5] or 0),
        "remaining": float(row[3] - (row[5] or 0)),
        "notes": row[6],
        "created_at": row[7].isoformat() if row[7] else None,
    }


@router.post("/budgets/{budget_id}/track", response_model=dict)
def track_budget_spend(
    budget_id: int,
    amount: Decimal = Query(..., gt=0),
    description: str | None = Query(None),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.execute(
        "SELECT id, total_budget, spent FROM ins_budgets WHERE id = :id AND lab_id = :lab_id",
        {"id": budget_id, "lab_id": current_user.lab_id},
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Budget not found")

    current_spent = float(row[2] or 0)
    new_spent = current_spent + float(amount)

    db.execute(
        "UPDATE ins_budgets SET spent = :spent WHERE id = :id",
        {"spent": new_spent, "id": budget_id},
    )
    db.commit()

    log_action(
        db=db,
        action="insurance.budget.track_spend",
        resource_type="insurance_budget",
        resource_id=budget_id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Tracked spend {amount} against budget {budget_id}: {description or ''}",
    )
    db.commit()

    total_budget = float(row[1])
    return {
        "budget_id": budget_id,
        "amount": float(amount),
        "total_spent": new_spent,
        "total_budget": total_budget,
        "remaining": total_budget - new_spent,
    }


@router.get("/reports/profit-loss", response_model=dict)
def profit_loss_report(
    date_from: date = Query(...),
    date_to: date = Query(...),
    provider_id: int | None = Query(None),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(InsuranceClaim).filter(
        InsuranceClaim.lab_id == current_user.lab_id,
        InsuranceClaim.status.in_(["paid", "partially_paid", "accepted"]),
        InsuranceClaim.paid_date >= date_from,
        InsuranceClaim.paid_date <= date_to,
    )
    if provider_id:
        q = q.filter(InsuranceClaim.provider_id == provider_id)

    claims = q.all()

    total_billed = sum(c.total_billed for c in claims)
    total_paid = sum(c.total_paid or Decimal("0") for c in claims)
    total_allowed = sum(c.total_allowed or Decimal("0") for c in claims)
    total_adjustments = total_billed - total_allowed

    return {
        "period": {
            "from": date_from.isoformat(),
            "to": date_to.isoformat(),
        },
        "revenue": {
            "total_billed": float(total_billed),
            "total_allowed": float(total_allowed),
            "total_paid": float(total_paid),
            "total_adjustments": float(total_adjustments),
            "total_outstanding": float(total_allowed - total_paid),
        },
        "summary": {
            "total_claims": len(claims),
            "net_revenue": float(total_paid),
        },
    }


@router.get("/reports/trial-balance", response_model=dict)
def trial_balance(
    as_of_date: date = Query(default_factory=date.today),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payments = db.query(InsurancePayment).filter(
        InsurancePayment.lab_id == current_user.lab_id,
        InsurancePayment.status == PaymentStatus.COMPLETED,
        InsurancePayment.payment_date <= as_of_date,
    ).all()

    settlements = db.query(Settlement).filter(
        Settlement.lab_id == current_user.lab_id,
        Settlement.status.in_([SettlementStatus.RECONCILED, SettlementStatus.COMPLETED]),
    ).all()

    total_payments = sum(p.amount for p in payments)
    total_adjustments = sum(p.adjustment_amount or Decimal("0") for p in payments)
    total_net_payments = total_payments - total_adjustments

    return {
        "as_of_date": as_of_date.isoformat(),
        "payments": {
            "total_received": float(total_payments),
            "total_adjustments": float(total_adjustments),
            "net_payments": float(total_net_payments),
            "payment_count": len(payments),
        },
        "settlements": {
            "total_settlements": len(settlements),
            "total_settlement_amount": float(sum(s.net_amount or Decimal("0") for s in settlements)),
        },
        "balance": float(total_net_payments),
    }


@router.get("/reports/aging", response_model=dict)
def aging_analysis(
    as_of_date: date = Query(default_factory=date.today),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    claims = db.query(InsuranceClaim).filter(
        InsuranceClaim.lab_id == current_user.lab_id,
        InsuranceClaim.status.in_(["submitted", "adjudicated", "accepted"]),
    ).all()

    buckets = {
        "0-30": [],
        "31-60": [],
        "61-90": [],
        "91+": [],
    }

    for claim in claims:
        ref_date = claim.submitted_date or claim.adjudicated_date or claim.created_at.date()
        days = (as_of_date - ref_date).days

        if days <= 30:
            bucket = "0-30"
        elif days <= 60:
            bucket = "31-60"
        elif days <= 90:
            bucket = "61-90"
        else:
            bucket = "91+"

        buckets[bucket].append({
            "claim_id": claim.id,
            "claim_number": claim.claim_number,
            "status": claim.status.value,
            "total_billed": float(claim.total_billed),
            "total_paid": float(claim.total_paid or 0),
            "outstanding": float((claim.total_allowed or claim.total_billed) - (claim.total_paid or 0)),
            "days_outstanding": days,
            "submitted_date": claim.submitted_date.isoformat() if claim.submitted_date else None,
        })

    return {
        "as_of_date": as_of_date.isoformat(),
        "aging_buckets": {
            bucket: {
                "count": len(items),
                "total_outstanding": sum(i["outstanding"] for i in items),
                "items": items,
            }
            for bucket, items in buckets.items()
        },
        "total_outstanding": sum(
            sum(i["outstanding"] for i in items) for items in buckets.values()
        ),
        "total_claims": len(claims),
    }
