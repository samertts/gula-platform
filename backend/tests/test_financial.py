"""Financial Platform - Pricing & Ranking Tests"""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.financial.pricing import (
    MINIMUM_BILL,
    VOLUME_DISCOUNT_THRESHOLD,
    apply_quality_discount,
    calculate_fee,
    enforce_minimum_bill,
)
from app.financial.ranking import (
    LabRanking,
    anti_dominance_control,
    compute_score,
    rank_labs,
)


class TestPricing:
    def test_basic_fee(self):
        fee = calculate_fee(Decimal("10000"))
        assert fee == Decimal("10000")

    def test_fee_with_quantity(self):
        fee = calculate_fee(Decimal("5000"), quantity=3)
        assert fee == Decimal("15000")

    def test_fee_enforces_minimum(self):
        fee = calculate_fee(Decimal("1000"))
        assert fee >= MINIMUM_BILL

    def test_fee_with_quality_discount(self):
        fee = calculate_fee(Decimal("100000"), quality_accredited=True)
        assert fee < Decimal("100000")

    def test_fee_with_volume_discount(self):
        fee = calculate_fee(Decimal("10000"), monthly_volume=200)
        assert fee < Decimal("10000")

    def test_negative_price_raises(self):
        with pytest.raises(ValueError):
            calculate_fee(Decimal("-100"))

    def test_zero_quantity_raises(self):
        with pytest.raises(ValueError):
            calculate_fee(Decimal("1000"), quantity=0)

    def test_apply_quality_discount(self):
        result = apply_quality_discount(Decimal("100000"), 0.8)
        assert result < Decimal("100000")
        assert result >= MINIMUM_BILL

    def test_apply_quality_discount_invalid_score(self):
        with pytest.raises(ValueError):
            apply_quality_discount(Decimal("100000"), 1.5)

    def test_enforce_minimum_bill(self):
        assert enforce_minimum_bill(Decimal("1000")) == MINIMUM_BILL
        assert enforce_minimum_bill(Decimal("50000")) == Decimal("50000")

    def test_volume_discount_threshold_constant(self):
        assert VOLUME_DISCOUNT_THRESHOLD == 100


class TestRanking:
    def test_compute_score_perfect_lab(self):
        ranking = LabRanking(
            lab_id=1,
            quality_score=1.0,
            avg_rating=5.0,
            review_count=100,
            distance_km=1.0,
            price_level=1,
            monthly_volume=1000,
            accredited=True,
        )
        score = compute_score(ranking)
        assert 0.9 <= score <= 1.0

    def test_compute_score_poor_lab(self):
        ranking = LabRanking(
            lab_id=2,
            quality_score=0.0,
            avg_rating=0.0,
            review_count=0,
            distance_km=50.0,
            price_level=3,
            monthly_volume=0,
        )
        score = compute_score(ranking)
        assert score < 0.5

    def test_compute_score_mid_range(self):
        ranking = LabRanking(
            lab_id=3,
            quality_score=0.5,
            avg_rating=3.0,
            review_count=10,
            distance_km=10.0,
            price_level=2,
            monthly_volume=50,
        )
        score = compute_score(ranking)
        assert 0.3 <= score <= 0.8

    def test_rank_labs_orders_by_score(self):
        labs = [
            LabRanking(lab_id=1, quality_score=0.9, avg_rating=4.5, monthly_volume=500),
            LabRanking(lab_id=2, quality_score=0.3, avg_rating=2.0, monthly_volume=10),
            LabRanking(lab_id=3, quality_score=0.6, avg_rating=3.5, monthly_volume=100),
        ]
        ranked = rank_labs(labs)
        assert ranked[0].score >= ranked[1].score >= ranked[2].score
        assert ranked[0].rank == 1
        assert ranked[2].rank == 3

    def test_rank_labs_assigns_ranks(self):
        labs = [
            LabRanking(lab_id=1, quality_score=0.5, avg_rating=3.0, monthly_volume=50),
            LabRanking(lab_id=2, quality_score=0.8, avg_rating=4.0, monthly_volume=200),
        ]
        ranked = rank_labs(labs)
        assert ranked[0].lab_id == 2
        assert ranked[1].lab_id == 1

    def test_anti_dominance_limits_per_owner(self):
        labs = [
            LabRanking(lab_id=1001, quality_score=0.9, avg_rating=4.5, monthly_volume=100),
            LabRanking(lab_id=1002, quality_score=0.8, avg_rating=4.0, monthly_volume=100),
            LabRanking(lab_id=1003, quality_score=0.7, avg_rating=3.5, monthly_volume=100),
            LabRanking(lab_id=1004, quality_score=0.6, avg_rating=3.0, monthly_volume=100),
            LabRanking(lab_id=2001, quality_score=0.9, avg_rating=4.5, monthly_volume=100),
        ]
        filtered = anti_dominance_control(labs, max_per_owner=3)
        assert len(filtered) == 4  # 3 from owner 1 + 1 from owner 2
        assert 1004 not in [lab.lab_id for lab in filtered]  # 4th from owner 1 excluded

    def test_distance_normalization(self):
        close_lab = LabRanking(
            lab_id=1, quality_score=0.5, avg_rating=3.0, distance_km=1.0, monthly_volume=50
        )
        far_lab = LabRanking(
            lab_id=2, quality_score=0.5, avg_rating=3.0, distance_km=40.0, monthly_volume=50
        )
        assert compute_score(close_lab) > compute_score(far_lab)
