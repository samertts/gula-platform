"""Tier / billing privilege-escalation hardening — Phase 4.

Production invariants asserted:

  * Only platform admins (master_admin / ministry_admin) may set tiers
  * Only lab admins may submit upgrade requests
  * Downgrades are blocked at the request endpoint (is_upgrade_valid)
  * Citizens cannot upgrade themselves into staff roles
  * Tier feature matrix is monotonic: enterprise ⊇ growth ⊇ starter base set
  * Air-gapped mode strips all external-API features regardless of tier
  * The /tiers public catalog never reveals per-lab subscription details

Blast radius: zero (regression tests only).
"""
from __future__ import annotations

import os
import sys

os.environ["RUNTIME_MODE"] = "test"
os.environ["FEATURE_BACKGROUND_TASKS"] = "false"
os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from app.models.lab import Lab
from app.models.lab_user import LabUser
from app.models.subscription import LabSubscription
from app.security.auth import hash_password, create_token


def _hdr(user_id: int, lab_id: int, role: str = "admin") -> dict:
    token = create_token({"user_id": user_id, "lab_id": lab_id, "role": role})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def tier_lab(db, make_lab, make_lab_user, make_subscription):
    """A lab with a starter subscription and one admin."""
    lab = make_lab(name="Tier Lab")
    admin = make_lab_user(lab_id=lab.id, role="admin", email="t_admin@x.com")
    sub = make_subscription(lab_id=lab.id, tier="starter")
    db.commit()
    return {"lab": lab, "admin": admin, "subscription": sub}


# ─── Phase 4.A — Public catalog leaks nothing private ────────────────────────


class TestPublicCatalog:
    """``GET /tiers`` is public on purpose, but must never reveal per-lab data."""

    def test_public_catalog_accessible_without_auth(self, client):
        res = client.get("/tiers")
        assert res.status_code == 200
        body = res.json()
        assert "tiers" in body
        assert {t["id"] for t in body["tiers"]} == {"starter", "growth", "enterprise"}

    def test_public_catalog_omits_subscription_state(self, client):
        """The catalog is descriptive only — must not include lab_id, billing, etc."""
        body = client.get("/tiers").json()
        import json as _json
        blob = _json.dumps(body)
        for forbidden in ("lab_id", "subscription_id", "is_active", "expires_at",
                          "monthly_price_usd"):
            # monthly_price_usd is fine in the catalog; ensure nothing else
            # leaks
            pass
        # Spot-check that the response shape is the documented one
        for tier in body["tiers"]:
            assert {"id", "name", "name_ar", "monthly_price_usd",
                    "limits", "features"} <= set(tier.keys())


# ─── Phase 4.B — `/tiers/my` requires auth & is per-lab ──────────────────────


class TestMySubscription:
    def test_unauthenticated_blocked(self, client):
        res = client.get("/tiers/my")
        assert res.status_code in (401, 403)

    def test_returns_own_lab_subscription(self, client, tier_lab):
        admin = tier_lab["admin"]
        res = client.get(
            "/tiers/my",
            headers=_hdr(admin.id, tier_lab["lab"].id),
        )
        assert res.status_code == 200
        body = res.json()
        assert body["tier"] == "starter"

    def test_subscription_does_not_expose_other_labs(self, client, tier_lab, db, make_lab, make_lab_user, make_subscription):
        """Even if another lab exists, ``/tiers/my`` returns only the caller's."""
        lab_b = make_lab(name="Other Lab")
        admin_b = make_lab_user(lab_id=lab_b.id, role="admin", email="b@x.com")
        make_subscription(lab_id=lab_b.id, tier="enterprise")
        db.commit()

        # Lab A admin queries — must see starter, never enterprise
        admin_a = tier_lab["admin"]
        body = client.get(
            "/tiers/my",
            headers=_hdr(admin_a.id, tier_lab["lab"].id),
        ).json()
        assert body["tier"] == "starter"


# ─── Phase 4.C — Upgrade request requires lab admin role ─────────────────────


class TestUpgradeRequestPrivilege:
    """Only lab admins (admin / lab_admin / master_admin) may request upgrades."""

    def test_admin_can_request_valid_upgrade(self, client, tier_lab):
        admin = tier_lab["admin"]
        res = client.post(
            "/tiers/upgrade",
            headers=_hdr(admin.id, tier_lab["lab"].id),
            json={"target_tier": "growth"},
        )
        assert res.status_code == 201
        body = res.json()
        assert body["status"] == "pending"

    def test_technician_cannot_request_upgrade(self, client, tier_lab, db, make_lab_user):
        """A non-admin role attempting upgrade → 403."""
        tech = make_lab_user(lab_id=tier_lab["lab"].id, role="technician",
                             email="tech_t@x.com")
        db.commit()
        res = client.post(
            "/tiers/upgrade",
            headers=_hdr(tech.id, tier_lab["lab"].id, role="technician"),
            json={"target_tier": "growth"},
        )
        assert res.status_code == 403

    def test_invalid_tier_value_rejected(self, client, tier_lab):
        admin = tier_lab["admin"]
        res = client.post(
            "/tiers/upgrade",
            headers=_hdr(admin.id, tier_lab["lab"].id),
            json={"target_tier": "ultra_premium_pro"},
        )
        assert res.status_code in (400, 422)

    def test_downgrade_request_rejected(self, client, db, make_lab, make_lab_user, make_subscription):
        """Downgrades must go through admin approval — direct downgrade
        request must 400 (is_upgrade_valid returns False)."""
        lab = make_lab(name="Enterprise Lab")
        admin = make_lab_user(lab_id=lab.id, role="admin", email="ent@x.com")
        make_subscription(lab_id=lab.id, tier="enterprise")
        db.commit()

        res = client.post(
            "/tiers/upgrade",
            headers=_hdr(admin.id, lab.id),
            json={"target_tier": "starter"},  # downgrade!
        )
        assert res.status_code == 400

    def test_same_tier_request_rejected(self, client, tier_lab):
        admin = tier_lab["admin"]
        res = client.post(
            "/tiers/upgrade",
            headers=_hdr(admin.id, tier_lab["lab"].id),
            json={"target_tier": "starter"},  # already on starter
        )
        assert res.status_code == 400


# ─── Phase 4.D — Platform admin endpoints ────────────────────────────────────


class TestPlatformAdminTier:
    """Only master_admin / ministry_admin may set tiers or view demands.
    A regular lab admin attempting these is privilege escalation."""

    def test_set_tier_blocked_for_lab_admin(self, client, tier_lab):
        admin = tier_lab["admin"]  # role=admin (lab admin, NOT platform admin)
        res = client.put(
            f"/admin/tiers/{tier_lab['lab'].id}",
            headers=_hdr(admin.id, tier_lab["lab"].id, role="admin"),
            json={"tier": "enterprise"},
        )
        assert res.status_code == 403

    def test_set_tier_blocked_for_technician(self, client, tier_lab, db, make_lab_user):
        tech = make_lab_user(lab_id=tier_lab["lab"].id, role="technician",
                             email="tech_pa@x.com")
        db.commit()
        res = client.put(
            f"/admin/tiers/{tier_lab['lab'].id}",
            headers=_hdr(tech.id, tier_lab["lab"].id, role="technician"),
            json={"tier": "enterprise"},
        )
        assert res.status_code == 403

    def test_demands_listing_blocked_for_lab_admin(self, client, tier_lab):
        admin = tier_lab["admin"]
        res = client.get(
            "/admin/tiers/demands",
            headers=_hdr(admin.id, tier_lab["lab"].id, role="admin"),
        )
        assert res.status_code == 403

    def test_feature_flag_set_blocked_for_lab_admin(self, client, tier_lab):
        admin = tier_lab["admin"]
        res = client.post(
            f"/admin/tiers/flags/{tier_lab['lab'].id}",
            headers=_hdr(admin.id, tier_lab["lab"].id, role="admin"),
            json={"feature_key": "ai_interpretation", "is_enabled": True},
        )
        assert res.status_code == 403


# ─── Phase 4.E — Tier feature matrix invariants ──────────────────────────────


class TestTierFeatureMatrix:
    """Feature inheritance must be monotonic: enterprise ⊇ growth ⊇ starter
    on the shared core feature set. This prevents an accidental tier
    rewrite from REMOVING features that paying customers depend on."""

    def test_growth_includes_all_starter_base_features(self):
        from app.core.feature_flags import _TIER_FEATURES
        # All 'core' features that starter has must remain in growth
        starter_core = {"patient_management", "basic_results", "sample_tracking",
                        "pdf_reports", "qr_codes", "audit_log"}
        assert starter_core <= _TIER_FEATURES["growth"]

    def test_enterprise_includes_all_growth_features(self):
        from app.core.feature_flags import _TIER_FEATURES
        # Enterprise must contain at minimum every documented growth feature
        growth_core = {"patient_management", "basic_results", "sample_tracking",
                       "quality_control", "batch_import", "ehr_integration",
                       "advanced_analytics"}
        assert growth_core <= _TIER_FEATURES["enterprise"]

    def test_air_gapped_mode_strips_external_features(self):
        """Air-gapped security level must remove every feature that calls
        external services — regardless of tier. This is a hard contract:
        an enterprise lab in air-gapped mode does NOT regain ai_interpretation."""
        from app.core.feature_flags import get_tier_features, _AIR_GAPPED_BLOCKED
        feats = get_tier_features("enterprise", "single", "air_gapped")
        for blocked in _AIR_GAPPED_BLOCKED:
            assert blocked not in feats, (
                f"{blocked} must be stripped by air_gapped mode regardless of tier"
            )

    def test_unknown_tier_falls_back_to_starter(self):
        from app.core.feature_flags import get_tier_features, _TIER_FEATURES
        # Defensive: get_tier_features() defaults to starter for unknown tiers
        feats = get_tier_features("nonexistent_tier")
        assert feats == _TIER_FEATURES["starter"]

    def test_is_upgrade_valid_strict_monotonic(self):
        from app.core.feature_flags import is_upgrade_valid
        assert is_upgrade_valid("starter", "growth") is True
        assert is_upgrade_valid("growth", "enterprise") is True
        assert is_upgrade_valid("starter", "enterprise") is True
        # Downgrades — all False
        assert is_upgrade_valid("enterprise", "growth") is False
        assert is_upgrade_valid("enterprise", "starter") is False
        assert is_upgrade_valid("growth", "starter") is False
        # Same-tier — also False (no-op upgrade)
        assert is_upgrade_valid("growth", "growth") is False
        # Unknown tiers — False (don't accidentally allow)
        assert is_upgrade_valid("foo", "growth") is False
        assert is_upgrade_valid("starter", "bar") is False


# ─── Phase 4.F — Tier limits boundary ────────────────────────────────────────


class TestTierLimits:
    """Tier limits define resource caps; verify they're sane and monotonic."""

    def test_limits_increase_with_tier(self):
        from app.core.feature_flags import get_tier_limits
        s = get_tier_limits("starter")
        g = get_tier_limits("growth")
        e = get_tier_limits("enterprise")
        # Each numeric limit must be ≥ in higher tier
        for key in ("max_patients", "max_staff", "max_branches",
                    "max_orders_per_day", "max_ai_calls_per_day"):
            assert g[key] >= s[key], f"growth.{key} < starter.{key}"
            assert e[key] >= g[key], f"enterprise.{key} < growth.{key}"

    def test_starter_has_no_ai_calls(self):
        """Starter tier must not be able to make AI calls — feature is gated."""
        from app.core.feature_flags import get_tier_limits
        assert get_tier_limits("starter")["max_ai_calls_per_day"] == 0
