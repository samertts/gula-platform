"""Claims Service — Insurance/Billing module.

All queries filter by lab_id to enforce the multi-tenant security invariant:
  "All patient data queries MUST filter by lab_id = current_user.lab_id"

Idempotency:
  create_claim() accepts an optional idempotency_key. If a claim with that key
  already exists for this lab, it is returned immediately without creating a
  duplicate. This prevents double-submission on network retries.
"""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app._compat import UTC

from ..models.claim import Claim, ClaimItem
from ..models.patient import Patient
from ..services.outbox_service import emit_to_outbox

logger = logging.getLogger("gula.claims")


# ─── Create ───────────────────────────────────────────────────────────────────


def create_claim(
    db: Session,
    lab_id: int,
    patient_id: int,
    items: list[dict],
    order_id: int | None = None,
    idempotency_key: str | None = None,
) -> Claim:
    """
    Create a new insurance claim in 'draft' status.

    If idempotency_key is provided and a claim already exists for that key
    within this lab, the existing claim is returned without side-effects.

    items: list of dicts with keys: test_code, description, quantity, unit_price, amount
    """
    # ── Idempotency check ─────────────────────────────────────────────────────
    if idempotency_key:
        existing = (
            db.query(Claim)
            .filter(
                Claim.idempotency_key == idempotency_key,
                Claim.lab_id == lab_id,
            )
            .first()
        )
        if existing:
            logger.info(
                "[CLAIMS] Idempotent return for key=%s claim_id=%d", idempotency_key, existing.id
            )
            return existing

    # ── Security: verify patient belongs to this lab ──────────────────────────
    patient = (
        db.query(Patient)
        .filter(
            Patient.id == patient_id,
            Patient.lab_id == lab_id,
        )
        .first()
    )
    if not patient:
        raise ValueError(f"Patient {patient_id} not found for lab {lab_id}")

    # ── Calculate total from items ────────────────────────────────────────────
    total = sum(Decimal(str(item["amount"])) for item in items)

    # ── Persist claim ─────────────────────────────────────────────────────────
    claim = Claim(
        lab_id=lab_id,
        patient_id=patient_id,
        order_id=order_id,
        status="draft",
        total_amount=total,
        currency="IQD",
        idempotency_key=idempotency_key,
    )
    db.add(claim)
    db.flush()  # get claim.id before adding items

    for item in items:
        db.add(
            ClaimItem(
                claim_id=claim.id,
                test_code=item["test_code"],
                description=item.get("description"),
                quantity=int(item.get("quantity", 1)),
                unit_price=Decimal(str(item["unit_price"])),
                amount=Decimal(str(item["amount"])),
            )
        )

    db.commit()
    db.refresh(claim)
    logger.info(
        "[CLAIMS] Created claim_id=%d lab_id=%d patient_id=%d total=%s",
        claim.id,
        lab_id,
        patient_id,
        total,
    )
    return claim


# ─── Validate ─────────────────────────────────────────────────────────────────


def validate_claim(db: Session, claim_id: int, lab_id: int) -> Claim:
    """
    Transition a claim from 'draft' → 'validated'.

    Checks:
      - Claim belongs to lab (security)
      - Status is 'draft'
      - At least one item exists
      - All item amounts are positive
    """
    claim = _get_claim_or_raise(db, claim_id, lab_id)

    if claim.status != "draft":
        raise ValueError(f"Claim {claim_id} is in status '{claim.status}', expected 'draft'")

    if not claim.items:
        raise ValueError(f"Claim {claim_id} has no items")

    for item in claim.items:
        if item.amount <= 0:
            raise ValueError(
                f"Claim item {item.id} (test_code={item.test_code}) has non-positive amount {item.amount}"
            )
        if item.unit_price <= 0:
            raise ValueError(
                f"Claim item {item.id} (test_code={item.test_code}) has non-positive unit_price {item.unit_price}"
            )

    claim.status = "validated"
    claim.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(claim)
    logger.info("[CLAIMS] Validated claim_id=%d lab_id=%d", claim_id, lab_id)
    return claim


# ─── Submit ───────────────────────────────────────────────────────────────────


def submit_claim(db: Session, claim_id: int, lab_id: int) -> Claim:
    """
    Transition a claim from 'validated' → 'submitted'.

    Emits a 'claim_submitted' outbox event for async delivery to the
    insurance gateway / government system.
    """
    claim = _get_claim_or_raise(db, claim_id, lab_id)

    if claim.status != "validated":
        raise ValueError(f"Claim {claim_id} is in status '{claim.status}', expected 'validated'")

    now = datetime.now(UTC)
    claim.status = "submitted"
    claim.submitted_at = now
    claim.updated_at = now

    # Build outbox payload
    items_payload = [
        {
            "id": item.id,
            "test_code": item.test_code,
            "description": item.description,
            "quantity": item.quantity,
            "unit_price": str(item.unit_price),
            "amount": str(item.amount),
        }
        for item in claim.items
    ]

    emit_to_outbox(
        db,
        event_type="claim_submitted",
        payload={
            "claim_id": claim.id,
            "lab_id": lab_id,
            "patient_id": claim.patient_id,
            "order_id": claim.order_id,
            "total_amount": str(claim.total_amount),
            "currency": claim.currency,
            "items": items_payload,
        },
        aggregate_type="claim",
        aggregate_id=claim.id,
    )

    db.commit()
    db.refresh(claim)
    logger.info(
        "[CLAIMS] Submitted claim_id=%d lab_id=%d total=%s", claim_id, lab_id, claim.total_amount
    )
    return claim


# ─── Get ──────────────────────────────────────────────────────────────────────


def get_claim(db: Session, claim_id: int, lab_id: int) -> Claim:
    """
    Retrieve a claim by ID, enforcing lab_id ownership.
    Raises ValueError if not found or wrong lab.
    """
    return _get_claim_or_raise(db, claim_id, lab_id)


# ─── Internal helpers ─────────────────────────────────────────────────────────


def _get_claim_or_raise(db: Session, claim_id: int, lab_id: int) -> Claim:
    """Load claim filtered by lab_id — enforces multi-tenant isolation."""
    claim = (
        db.query(Claim)
        .filter(
            Claim.id == claim_id,
            Claim.lab_id == lab_id,
        )
        .first()
    )
    if not claim:
        raise ValueError(f"Claim {claim_id} not found for lab {lab_id}")
    return claim
