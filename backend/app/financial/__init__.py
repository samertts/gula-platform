"""GULA Financial Engine — provider-billing, ranking, ads, fraud, governance.

This package is the home of the Financial Engine. It is gated by the two
feature flags `ENABLE_FINANCIAL_ENGINE` and `ENABLE_ADS` defined in
`app.config`, both of which default to OFF.

PHASE A (initial):
    Tables exist (see migration 20260506_0001_financial_engine_phase_a).
    pricing.py — calculate_fee, apply_quality_discount, enforce_minimum_bill
    ranking.py — score formula, anti_dominance_control, apply_ad_cap

PHASE B (this revision):
    models.py — ORM mappings for fin_providers, fin_subscriptions, fin_transactions
    routes.py — FastAPI router (gated by ENABLE_FINANCIAL_ENGINE, mounted in app.main)

PHASE C (future):
    ads.py         — create_campaign, record_click, record_conversion, budget enforcement
    governance.py  — detect_over_testing, apply_behavior_penalty
    fraud.py       — detect_click_fraud, penalize_campaign
    incentives.py  — grant_quality_bonus, grant_efficiency_bonus
    schemas.py     — Pydantic request/response models
    simulation.py  — simulate_market() — Phase J
"""

from app.config import ENABLE_ADS, ENABLE_FINANCIAL_ENGINE

__all__ = [
    "ENABLE_ADS", "ENABLE_FINANCIAL_ENGINE",
    "ads_enabled", "is_enabled", "register_routes",
]


def is_enabled() -> bool:
    """Master gate: True iff the engine is turned on in the running env."""
    return bool(ENABLE_FINANCIAL_ENGINE)


def ads_enabled() -> bool:
    """Sub-gate: True iff both the engine AND the ads sub-flag are on."""
    return bool(ENABLE_FINANCIAL_ENGINE and ENABLE_ADS)


def register_routes(app) -> None:
    """Register Financial Engine routes if the feature flag is enabled."""
    if not is_enabled():
        import logging
        logging.getLogger("gula.financial").info("Financial Engine disabled — routes not registered")
        return
    from .routes import router as financial_router
    app.include_router(financial_router)
    import logging
    logging.getLogger("gula.financial").info("Financial Engine routes registered")


def register_canonical_routes(app) -> None:
    """Mount the NIAM-scoped canonical finance core; legacy routes remain separate."""
    from .canonical_routes import router as canonical_financial_router
    app.include_router(canonical_financial_router)
