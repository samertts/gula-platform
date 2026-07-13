"""Financial Engine — Pricing Service.
Calculates fees, applies discounts, enforces minimum billing.
"""

from __future__ import annotations

from decimal import Decimal

MINIMUM_BILL: Decimal = Decimal("5000")  # IQD
QUALITY_DISCOUNT_RATE: Decimal = Decimal("0.05")  # 5% discount for accredited labs
VOLUME_DISCOUNT_THRESHOLD: int = 100  # tests/month
VOLUME_DISCOUNT_RATE: Decimal = Decimal("0.10")  # 10% discount above threshold


def calculate_fee(
    base_price: Decimal,
    quantity: int = 1,
    quality_accredited: bool = False,
    monthly_volume: int = 0,
) -> Decimal:
    if base_price < 0:
        raise ValueError("base_price must be non-negative")
    if quantity < 1:
        raise ValueError("quantity must be >= 1")

    subtotal = base_price * quantity
    discount = Decimal("0")

    if quality_accredited:
        discount += subtotal * QUALITY_DISCOUNT_RATE

    if monthly_volume > VOLUME_DISCOUNT_THRESHOLD:
        discount += subtotal * VOLUME_DISCOUNT_RATE

    total = max(subtotal - discount, MINIMUM_BILL)
    return total.quantize(Decimal("1"))  # round to integer


def apply_quality_discount(fee: Decimal, quality_score: float) -> Decimal:
    if not 0.0 <= quality_score <= 1.0:
        raise ValueError("quality_score must be 0.0–1.0")
    discount = fee * Decimal(str(quality_score)) * QUALITY_DISCOUNT_RATE
    return max(fee - discount, MINIMUM_BILL).quantize(Decimal("1"))


def enforce_minimum_bill(fee: Decimal) -> Decimal:
    return max(fee, MINIMUM_BILL).quantize(Decimal("1"))
