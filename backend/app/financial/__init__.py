"""GULA Financial Engine — provider-billing, ranking, ads, fraud, governance.

This package is the home of the Financial Engine. It is gated by the two
feature flags `ENABLE_FINANCIAL_ENGINE` and `ENABLE_ADS` defined in
`app.config`, both of which default to OFF.

PHASE A (this commit):
    Only the tables exist (see migration 20260505_0001_financial_engine_phase_a).
    No services, no routes, no models — importing this package is a no-op.

PHASE B+ (subsequent commits):
    pricing.py     — calculate_fee, apply_quality_discount, enforce_minimum_bill
    ranking.py     — score formula, anti_dominance_control, apply_ad_cap
    ads.py         — create_campaign, record_click, record_conversion, budget enforcement
    governance.py  — detect_over_testing, apply_behavior_penalty
    fraud.py       — detect_click_fraud, penalize_campaign
    incentives.py  — grant_quality_bonus, grant_efficiency_bonus
    routes.py      — FastAPI router (mounted in app.main only when the flag is ON)
    schemas.py     — Pydantic request/response models
    models.py      — SQLAlchemy ORM mappings for fin_* tables
    simulation.py  — simulate_market() — Phase J

Until those modules exist, NOTHING imports this package, and the engine has
zero runtime impact on the production monolith.
"""

from app.config import ENABLE_ADS, ENABLE_FINANCIAL_ENGINE

__all__ = ["ENABLE_ADS", "ENABLE_FINANCIAL_ENGINE", "ads_enabled", "is_enabled"]


def is_enabled() -> bool:
    """Master gate: True iff the engine is turned on in the running env."""
    return bool(ENABLE_FINANCIAL_ENGINE)


def ads_enabled() -> bool:
    """Sub-gate: True iff both the engine AND the ads sub-flag are on."""
    return bool(ENABLE_FINANCIAL_ENGINE and ENABLE_ADS)
