from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from backend.app._compat import UTC

logger = logging.getLogger("gula.subscriptions")


class SubscriptionPlan:
    def __init__(
        self, name: str, tier: str, price_monthly: float = 0.0, price_yearly: float = 0.0,
        max_labs: int = 1, max_users: int = 5, features: list[str] | None = None,
    ) -> None:
        self.name = name
        self.tier = tier
        self.price_monthly = price_monthly
        self.price_yearly = price_yearly
        self.max_labs = max_labs
        self.max_users = max_users
        self.features = features or []

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name, "tier": self.tier,
            "price_monthly": self.price_monthly, "price_yearly": self.price_yearly,
            "max_labs": self.max_labs, "max_users": self.max_users, "features": self.features,
        }


PLANS = {
    "free": SubscriptionPlan("Free", "free", max_labs=1, max_users=1,
        features=["basic_orders", "basic_results"]),
    "basic": SubscriptionPlan("Basic", "basic", price_monthly=49.99, max_labs=1, max_users=5,
        features=["basic_orders", "basic_results", "qr_cards", "email_reports"]),
    "professional": SubscriptionPlan("Professional", "professional", price_monthly=149.99,
        max_labs=5, max_users=25,
        features=["basic_orders", "basic_results", "qr_cards", "email_reports",
                  "api_access", "ai_interpretation", "batch_processing"]),
    "enterprise": SubscriptionPlan("Enterprise", "enterprise", price_monthly=499.99,
        max_labs=999, max_users=9999,
        features=["basic_orders", "basic_results", "qr_cards", "email_reports",
                  "api_access", "ai_interpretation", "batch_processing",
                  "dedicated_support", "custom_integrations", "on_premise"]),
}


class Subscription:
    def __init__(self, lab_id: int, plan_name: str = "free", sub_id: str | None = None) -> None:
        self.id = sub_id or str(uuid4())
        self.lab_id = lab_id
        self.plan = PLANS.get(plan_name, PLANS["free"])
        self.active = True
        self.billing_period_start = datetime.now(UTC)
        self.billing_period_end = datetime.now(UTC) + timedelta(days=30)
        self.created_at = datetime.now(UTC)

    @property
    def feature_set(self) -> list[str]:
        return self.plan.features

    def has_feature(self, feature: str) -> bool:
        return self.active and feature in self.plan.features

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "lab_id": self.lab_id, "plan": self.plan.name,
            "tier": self.plan.tier, "active": self.active, "features": self.plan.features,
            "period_start": self.billing_period_start.isoformat(),
            "period_end": self.billing_period_end.isoformat(),
        }


__all__ = ["PLANS", "Subscription", "SubscriptionPlan"]
