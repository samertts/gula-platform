"""Feature flags & tier enforcement tests.

Covers:
  - get_tier_features: correct feature sets for all 3 tiers
  - Deployment-mode bonuses (government, multi_branch)
  - Security-level bonuses (high_security, air_gapped)
  - Air-gapped blocking of external-API features
  - is_upgrade_valid: upgrade allowed, downgrade rejected
  - get_tier_limits: correct resource ceilings per tier
  - resolve_lab_features: no subscription → starter defaults
  - resolve_lab_features: subscription tier applied
  - resolve_lab_features: per-lab FeatureFlag add/remove override
  - resolve_lab_features: expired FeatureFlag is ignored
  - require_feature: raises 403 when feature unavailable
  - require_feature: passes when feature available
  - can_lab_access: non-raising version
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from app._compat import UTC

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")

import pytest
from app.core.feature_flags import (
    can_lab_access,
    get_tier_features,
    get_tier_limits,
    is_upgrade_valid,
    require_feature,
    resolve_lab_features,
)
from app.database import Base
from app.national.base import NationalBase
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ── Shared DB fixture (subscription model needed) ─────────────────────────────

@pytest.fixture()
def db():
    import app.models.lab
    import app.models.lab_user
    import app.models.subscription
    from app.services.mpi.models import Citizen, IdentityClaim
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    import app.national.domain
    NationalBase.metadata.create_all(engine)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    try:
        yield s
    finally:
        s.close()
        Base.metadata.drop_all(engine)


# ── get_tier_features ─────────────────────────────────────────────────────────

class TestGetTierFeatures:
    def test_starter_includes_basic_features(self):
        features = get_tier_features("starter")
        assert "patient_management" in features
        assert "basic_results" in features
        assert "sample_tracking" in features
        assert "pdf_reports" in features

    def test_starter_excludes_growth_features(self):
        features = get_tier_features("starter")
        assert "quality_control" not in features
        assert "batch_import" not in features
        assert "ehr_integration" not in features

    def test_growth_includes_starter_and_growth_features(self):
        features = get_tier_features("growth")
        # Growth inherits starter
        assert "patient_management" in features
        assert "basic_results" in features
        # Growth additions
        assert "quality_control" in features
        assert "batch_import" in features
        assert "ehr_integration" in features
        assert "advanced_analytics" in features

    def test_growth_excludes_enterprise_features(self):
        features = get_tier_features("growth")
        assert "multi_branch" not in features
        assert "ai_interpretation" not in features
        assert "government_reporting" not in features

    def test_enterprise_includes_all_tiers(self):
        features = get_tier_features("enterprise")
        # All of starter + growth
        assert "patient_management" in features
        assert "quality_control" in features
        # Enterprise only
        assert "multi_branch" in features
        assert "ai_interpretation" in features
        assert "ai_anomaly_detection" in features
        assert "government_reporting" in features

    def test_unknown_tier_falls_back_to_starter(self):
        features = get_tier_features("platinum")   # nonexistent tier
        assert "patient_management" in features
        assert "quality_control" not in features   # not in starter

    def test_government_deployment_adds_government_features(self):
        features = get_tier_features("starter", deployment_mode="government")
        assert "government_reporting" in features
        assert "ministry_integration" in features

    def test_multi_branch_deployment_adds_cross_branch_reports(self):
        features = get_tier_features("growth", deployment_mode="multi_branch")
        assert "multi_branch" in features
        assert "cross_branch_reports" in features

    def test_high_security_adds_2fa_and_audit_chain(self):
        features = get_tier_features("starter", security_level="high_security")
        assert "two_factor_required" in features
        assert "audit_chain" in features
        assert "session_timeout_short" in features

    def test_air_gapped_blocks_external_api_features(self):
        features = get_tier_features("enterprise", security_level="air_gapped")
        # Enterprise has ai_interpretation, but air_gapped blocks it
        assert "ai_interpretation" not in features
        assert "ehr_integration" not in features
        assert "insurance_integration" not in features
        assert "national_id_lookup" not in features
        assert "notifications" not in features

    def test_air_gapped_still_allows_local_features(self):
        features = get_tier_features("enterprise", security_level="air_gapped")
        assert "patient_management" in features
        assert "basic_results" in features
        assert "audit_chain" in features  # security bonus present


# ── is_upgrade_valid ──────────────────────────────────────────────────────────

class TestIsUpgradeValid:
    def test_starter_to_growth_is_valid(self):
        assert is_upgrade_valid("starter", "growth") is True

    def test_starter_to_enterprise_is_valid(self):
        assert is_upgrade_valid("starter", "enterprise") is True

    def test_growth_to_enterprise_is_valid(self):
        assert is_upgrade_valid("growth", "enterprise") is True

    def test_downgrade_growth_to_starter_is_invalid(self):
        assert is_upgrade_valid("growth", "starter") is False

    def test_downgrade_enterprise_to_growth_is_invalid(self):
        assert is_upgrade_valid("enterprise", "growth") is False

    def test_same_tier_is_invalid(self):
        assert is_upgrade_valid("growth", "growth") is False

    def test_unknown_source_tier_is_invalid(self):
        assert is_upgrade_valid("platinum", "enterprise") is False

    def test_unknown_target_tier_is_invalid(self):
        assert is_upgrade_valid("starter", "diamond") is False


# ── get_tier_limits ───────────────────────────────────────────────────────────

class TestGetTierLimits:
    def test_starter_limits(self):
        limits = get_tier_limits("starter")
        assert limits["max_patients"] == 500
        assert limits["max_staff"] == 5
        assert limits["max_branches"] == 1
        assert limits["max_orders_per_day"] == 100
        assert limits["max_ai_calls_per_day"] == 0

    def test_growth_limits_are_higher_than_starter(self):
        s = get_tier_limits("starter")
        g = get_tier_limits("growth")
        assert g["max_patients"] > s["max_patients"]
        assert g["max_staff"] > s["max_staff"]
        assert g["max_orders_per_day"] > s["max_orders_per_day"]

    def test_enterprise_limits_are_highest(self):
        g = get_tier_limits("growth")
        e = get_tier_limits("enterprise")
        assert e["max_patients"] > g["max_patients"]
        assert e["max_staff"] > g["max_staff"]
        assert e["max_branches"] > g["max_branches"]
        assert e["max_ai_calls_per_day"] > g["max_ai_calls_per_day"]

    def test_unknown_tier_returns_starter_limits(self):
        limits = get_tier_limits("nonexistent")
        assert limits == get_tier_limits("starter")


# ── resolve_lab_features ──────────────────────────────────────────────────────

class TestResolveLabFeatures:
    def test_no_subscription_defaults_to_starter(self, db):
        # Lab 999 has no subscription row
        features = resolve_lab_features(999, db)
        assert "patient_management" in features
        assert "quality_control" not in features

    def test_growth_subscription_gives_growth_features(self, db):
        from app.models.lab import Lab
        from app.models.subscription import LabSubscription

        lab = Lab(name="Growth Lab", is_active=True)
        db.add(lab)
        db.flush()
        sub = LabSubscription(lab_id=lab.id, tier="growth", is_active=True)
        db.add(sub)
        db.flush()

        features = resolve_lab_features(lab.id, db)
        assert "quality_control" in features
        assert "batch_import" in features
        assert "multi_branch" not in features

    def test_enterprise_subscription_gives_all_features(self, db):
        from app.models.lab import Lab
        from app.models.subscription import LabSubscription

        lab = Lab(name="Enterprise Lab", is_active=True)
        db.add(lab)
        db.flush()
        sub = LabSubscription(lab_id=lab.id, tier="enterprise", is_active=True)
        db.add(sub)
        db.flush()

        features = resolve_lab_features(lab.id, db)
        assert "ai_interpretation" in features
        assert "multi_branch" in features

    def test_inactive_subscription_is_ignored(self, db):
        from app.models.lab import Lab
        from app.models.subscription import LabSubscription

        lab = Lab(name="Inactive Sub Lab", is_active=True)
        db.add(lab)
        db.flush()
        sub = LabSubscription(lab_id=lab.id, tier="enterprise", is_active=False)
        db.add(sub)
        db.flush()

        # inactive → falls back to starter defaults
        features = resolve_lab_features(lab.id, db)
        assert "ai_interpretation" not in features
        assert "patient_management" in features

    def test_per_lab_flag_can_add_feature(self, db):
        from app.models.lab import Lab
        from app.models.subscription import FeatureFlag, LabSubscription

        lab = Lab(name="Flag Add Lab", is_active=True)
        db.add(lab)
        db.flush()
        sub = LabSubscription(lab_id=lab.id, tier="starter", is_active=True)
        db.add(sub)
        # Add enterprise feature to starter lab via flag override
        flag = FeatureFlag(lab_id=lab.id, feature_key="ai_interpretation", is_enabled=True)
        db.add(flag)
        db.flush()

        features = resolve_lab_features(lab.id, db)
        assert "ai_interpretation" in features

    def test_per_lab_flag_can_remove_feature(self, db):
        from app.models.lab import Lab
        from app.models.subscription import FeatureFlag, LabSubscription

        lab = Lab(name="Flag Remove Lab", is_active=True)
        db.add(lab)
        db.flush()
        sub = LabSubscription(lab_id=lab.id, tier="growth", is_active=True)
        db.add(sub)
        # Remove batch_import from a growth lab
        flag = FeatureFlag(lab_id=lab.id, feature_key="batch_import", is_enabled=False)
        db.add(flag)
        db.flush()

        features = resolve_lab_features(lab.id, db)
        assert "batch_import" not in features
        # Other growth features still intact
        assert "quality_control" in features

    def test_expired_flag_is_ignored(self, db):
        from app.models.lab import Lab
        from app.models.subscription import FeatureFlag, LabSubscription

        lab = Lab(name="Expired Flag Lab", is_active=True)
        db.add(lab)
        db.flush()
        sub = LabSubscription(lab_id=lab.id, tier="starter", is_active=True)
        db.add(sub)
        # Expired flag for a premium feature — should be ignored
        past = datetime.now(UTC) - timedelta(days=1)
        flag = FeatureFlag(
            lab_id=lab.id,
            feature_key="ai_interpretation",
            is_enabled=True,
            expires_at=past,
        )
        db.add(flag)
        db.flush()

        features = resolve_lab_features(lab.id, db)
        assert "ai_interpretation" not in features   # expired, ignored


# ── require_feature / can_lab_access ─────────────────────────────────────────

class TestRequireFeature:
    def test_raises_403_when_feature_not_in_tier(self, db):
        # Lab 999 has no subscription → starter → no quality_control
        with pytest.raises(HTTPException) as exc_info:
            require_feature("quality_control", 999, db)
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["error"] == "feature_not_available"
        assert "upgrade_hint" in exc_info.value.detail

    def test_does_not_raise_when_feature_present(self, db):
        from app.models.lab import Lab
        from app.models.subscription import LabSubscription

        lab = Lab(name="OK Lab", is_active=True)
        db.add(lab)
        db.flush()
        sub = LabSubscription(lab_id=lab.id, tier="growth", is_active=True)
        db.add(sub)
        db.flush()

        # Should not raise
        require_feature("quality_control", lab.id, db)

    def test_can_lab_access_returns_false_when_missing(self, db):
        assert can_lab_access("ai_interpretation", 999, db) is False

    def test_can_lab_access_returns_true_when_present(self, db):
        from app.models.lab import Lab
        from app.models.subscription import LabSubscription

        lab = Lab(name="Enterprise Lab2", is_active=True)
        db.add(lab)
        db.flush()
        sub = LabSubscription(lab_id=lab.id, tier="enterprise", is_active=True)
        db.add(sub)
        db.flush()

        assert can_lab_access("ai_interpretation", lab.id, db) is True

    def test_error_response_includes_arabic_message(self, db):
        with pytest.raises(HTTPException) as exc_info:
            require_feature("ai_interpretation", 999, db)
        detail = exc_info.value.detail
        assert "message_ar" in detail
        assert "upgrade_hint_ar" in detail
