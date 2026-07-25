from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.lab import Lab
from app.models.subscription import LabSubscription

logger = logging.getLogger("gula.bootstrap.subscriptions")

TIER_CONFIGS: dict[str, dict] = {
    "starter": {
        "tier": "starter",
        "deployment_mode": "single",
        "security_level": "standard",
        "max_patients": 500,
        "max_staff": 5,
        "max_branches": 1,
        "max_orders_per_day": 100,
        "max_ai_calls_per_day": 0,
    },
    "professional": {
        "tier": "professional",
        "deployment_mode": "multi_branch",
        "security_level": "standard",
        "max_patients": 5000,
        "max_staff": 50,
        "max_branches": 5,
        "max_orders_per_day": 1000,
        "max_ai_calls_per_day": 100,
    },
    "enterprise": {
        "tier": "enterprise",
        "deployment_mode": "multi_branch",
        "security_level": "high_security",
        "max_patients": 50000,
        "max_staff": 500,
        "max_branches": 50,
        "max_orders_per_day": 10000,
        "max_ai_calls_per_day": 1000,
    },
    "national": {
        "tier": "national",
        "deployment_mode": "government",
        "security_level": "high_security",
        "max_patients": 1000000,
        "max_staff": 5000,
        "max_branches": 500,
        "max_orders_per_day": 100000,
        "max_ai_calls_per_day": 10000,
    },
}


def seed_subscriptions(db: Session | None = None) -> int:
    if db is None:
        db = SessionLocal()
        own_session = True
    else:
        own_session = False

    created = 0
    try:
        labs = db.query(Lab).filter(Lab.is_active).all()
        for lab in labs:
            existing = (
                db.query(LabSubscription)
                .filter(
                    LabSubscription.lab_id == lab.id,
                )
                .first()
            )
            if existing:
                continue

            tier_config = TIER_CONFIGS.get("starter", {})
            sub = LabSubscription(
                lab_id=lab.id,
                tier=tier_config["tier"],
                deployment_mode=tier_config["deployment_mode"],
                security_level=tier_config["security_level"],
                max_patients=tier_config["max_patients"],
                max_staff=tier_config["max_staff"],
                max_branches=tier_config["max_branches"],
                max_orders_per_day=tier_config["max_orders_per_day"],
                max_ai_calls_per_day=tier_config["max_ai_calls_per_day"],
                is_active=True,
                billing_cycle="monthly",
                monthly_price_usd=0.0,
            )
            db.add(sub)
            created += 1

        if created:
            db.commit()
            logger.info("Seeded subscriptions for %d labs", created)
        else:
            logger.debug("All labs already have subscriptions")
    except Exception as exc:
        db.rollback()
        logger.error("Failed to seed subscriptions: %s", exc)
        raise
    finally:
        if own_session:
            db.close()

    return created


def upgrade_subscription(
    lab_id: int,
    tier: str,
    db: Session,
) -> LabSubscription | None:
    tier_config = TIER_CONFIGS.get(tier)
    if not tier_config:
        logger.error("Unknown tier: %s", tier)
        return None

    sub = (
        db.query(LabSubscription)
        .filter(
            LabSubscription.lab_id == lab_id,
        )
        .first()
    )

    if sub:
        existing_tier_level = list(TIER_CONFIGS.keys()).index(
            sub.tier if sub.tier in TIER_CONFIGS else "starter",
        )
        target_tier_level = list(TIER_CONFIGS.keys()).index(tier)
        if target_tier_level <= existing_tier_level:
            logger.info(
                "Lab %d already on tier '%s' (requested '%s') — no upgrade needed",
                lab_id,
                sub.tier,
                tier,
            )
            return sub

        for key, value in tier_config.items():
            setattr(sub, key, value)
        logger.info("Upgraded lab %d to tier '%s'", lab_id, tier)
    else:
        sub = LabSubscription(
            lab_id=lab_id,
            **tier_config,
            is_active=True,
            billing_cycle="monthly",
            monthly_price_usd=0.0,
        )
        db.add(sub)
        logger.info("Created %s subscription for lab %d", tier, lab_id)

    db.flush()
    return sub
