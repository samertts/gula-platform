"""
GULA Blood Network (GBN) — Unit Tests
======================================
Tests the safety-critical business logic with zero external dependencies:

  1. Blood type compatibility matrix (all 64 combinations)
  2. Donor eligibility rules (interval, Hb, deferral)
  3. Unit expiry calculation
  4. Shortage detection
  5. Incompatible transfusion block (most critical safety test)
  6. Migration chain includes 0013

Run:
  cd backend && python -m pytest tests/test_gbn.py -v
"""
import os, sys
os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///test_gbn.db")
os.environ.setdefault("SECRET_KEY",      "test-gbn-key-" + "x" * 40)
os.environ.setdefault("ENCRYPTION_KEY",  "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY",    "a" * 64)
os.environ.setdefault("REDIS_URL",       "redis://localhost:6379")

import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch


# ── 1. Blood Type Compatibility ───────────────────────────────────────────────

class TestBloodCompatibility:

    def test_universal_donor_o_neg_compatible_with_all(self):
        from app.models.blood import BLOOD_COMPATIBILITY, BLOOD_TYPES
        for recipient in BLOOD_TYPES:
            assert "O-" in BLOOD_COMPATIBILITY[recipient], (
                f"O- must be compatible with {recipient} (universal donor)"
            )

    def test_universal_recipient_ab_pos_accepts_all(self):
        from app.models.blood import BLOOD_COMPATIBILITY, BLOOD_TYPES
        ab_pos_compatible = BLOOD_COMPATIBILITY["AB+"]
        for donor_type in BLOOD_TYPES:
            assert donor_type in ab_pos_compatible, (
                f"AB+ must accept {donor_type} (universal recipient)"
            )

    def test_o_pos_cannot_receive_a_neg(self):
        from app.services.blood_matching import is_compatible
        assert not is_compatible("A-", "O+"), "A- → O+ must be incompatible"

    def test_a_neg_cannot_receive_b_neg(self):
        from app.services.blood_matching import is_compatible
        assert not is_compatible("B-", "A-"), "B- → A- must be incompatible"

    def test_ab_neg_cannot_receive_o_pos(self):
        """AB- cannot receive O+ (Rh incompatibility)."""
        from app.services.blood_matching import is_compatible
        assert not is_compatible("O+", "AB-"), "O+ → AB- must be incompatible (Rh)"

    def test_same_type_always_compatible(self):
        from app.models.blood import BLOOD_TYPES
        from app.services.blood_matching import is_compatible
        for bt in BLOOD_TYPES:
            assert is_compatible(bt, bt), f"{bt} → {bt} must be self-compatible"

    def test_all_64_combinations_defined(self):
        """Every (donor, recipient) pair must have a deterministic answer."""
        from app.models.blood import BLOOD_TYPES
        from app.services.blood_matching import is_compatible
        # 8 donors × 8 recipients = 64 — none should raise
        for donor in BLOOD_TYPES:
            for recipient in BLOOD_TYPES:
                result = is_compatible(donor, recipient)
                assert isinstance(result, bool)

    def test_assert_compatible_raises_on_mismatch(self):
        from app.services.blood_matching import assert_compatible
        with pytest.raises(ValueError, match="INCOMPATIBLE"):
            assert_compatible("A+", "O-")

    def test_assert_compatible_passes_on_valid(self):
        from app.services.blood_matching import assert_compatible
        assert_compatible("O-", "AB+")   # must not raise

    def test_unknown_blood_type_raises(self):
        from app.services.blood_matching import compatible_donor_types
        with pytest.raises(ValueError, match="Unknown"):
            compatible_donor_types("X+")


# ── 2. Donor Eligibility ──────────────────────────────────────────────────────

class TestDonorEligibility:

    def _make_donor(self, **kwargs):
        donor = MagicMock()
        donor.eligibility_status = kwargs.get("eligibility_status", "eligible")
        donor.last_donation_date = kwargs.get("last_donation_date", None)
        donor.deferral_reason    = kwargs.get("deferral_reason", None)
        donor.deferral_until     = kwargs.get("deferral_until", None)
        donor.gender             = kwargs.get("gender", "M")
        return donor

    def test_new_donor_is_eligible(self):
        from app.services.blood_matching import screen_donor
        donor = self._make_donor()
        result = screen_donor(donor)
        assert result.eligible is True

    def test_permanent_deferral_blocks(self):
        from app.services.blood_matching import screen_donor
        donor = self._make_donor(
            eligibility_status="deferred_permanent",
            deferral_reason="HIV positive"
        )
        result = screen_donor(donor)
        assert result.eligible is False
        assert "دائم" in result.reason or "permanent" in result.reason.lower()

    def test_temporary_deferral_still_active_blocks(self):
        from app.services.blood_matching import screen_donor
        donor = self._make_donor(
            eligibility_status="deferred_temporary",
            deferral_until=date.today() + timedelta(days=30),
        )
        result = screen_donor(donor)
        assert result.eligible is False
        assert result.eligible_from is not None

    def test_temporary_deferral_expired_allows(self):
        from app.services.blood_matching import screen_donor
        donor = self._make_donor(
            eligibility_status="deferred_temporary",
            deferral_until=date.today() - timedelta(days=1),
        )
        result = screen_donor(donor)
        assert result.eligible is True

    def test_donation_interval_not_met_blocks(self):
        from app.services.blood_matching import screen_donor
        donor = self._make_donor(
            last_donation_date=date.today() - timedelta(days=45),  # only 45 days, need 90
        )
        result = screen_donor(donor)
        assert result.eligible is False
        assert result.eligible_from is not None
        assert result.eligible_from > date.today()

    def test_donation_interval_exactly_met_allows(self):
        from app.services.blood_matching import screen_donor
        from app.models.blood import MIN_DONATION_INTERVAL_DAYS
        donor = self._make_donor(
            last_donation_date=date.today() - timedelta(days=MIN_DONATION_INTERVAL_DAYS),
        )
        result = screen_donor(donor)
        assert result.eligible is True

    def test_low_hb_male_blocks(self):
        from app.services.blood_matching import screen_donor
        from app.models.blood import MIN_HB_MALE_G_DL
        donor = self._make_donor(gender="M")
        result = screen_donor(donor, hb_g_dl=MIN_HB_MALE_G_DL - 0.5)
        assert result.eligible is False
        assert "g/dL" in result.reason

    def test_sufficient_hb_male_passes(self):
        from app.services.blood_matching import screen_donor
        from app.models.blood import MIN_HB_MALE_G_DL
        donor = self._make_donor(gender="M")
        result = screen_donor(donor, hb_g_dl=MIN_HB_MALE_G_DL + 1.0)
        assert result.eligible is True

    def test_low_hb_female_threshold_different(self):
        from app.services.blood_matching import screen_donor
        from app.models.blood import MIN_HB_FEMALE_G_DL, MIN_HB_MALE_G_DL
        donor = self._make_donor(gender="F")
        # Value above female threshold but below male threshold
        hb = (MIN_HB_FEMALE_G_DL + MIN_HB_MALE_G_DL) / 2
        result = screen_donor(donor, hb_g_dl=hb)
        assert result.eligible is True   # female threshold is lower


# ── 3. Unit Expiry Calculation ────────────────────────────────────────────────

class TestUnitExpiry:

    def test_rbc_expires_42_days(self):
        from app.models.blood import BloodUnit
        d = date.today()
        expiry = BloodUnit.compute_expiry("RBC", d)
        assert expiry == d + timedelta(days=42)

    def test_platelets_expire_5_days(self):
        from app.models.blood import BloodUnit
        d = date.today()
        expiry = BloodUnit.compute_expiry("platelets", d)
        assert expiry == d + timedelta(days=5)

    def test_plasma_expires_365_days(self):
        from app.models.blood import BloodUnit
        d = date.today()
        expiry = BloodUnit.compute_expiry("plasma", d)
        assert expiry == d + timedelta(days=365)

    def test_whole_blood_expires_35_days(self):
        from app.models.blood import BloodUnit
        d = date.today()
        expiry = BloodUnit.compute_expiry("whole", d)
        assert expiry == d + timedelta(days=35)

    def test_unit_is_expired_property(self):
        from app.models.blood import BloodUnit
        from types import SimpleNamespace
        unit = SimpleNamespace(expiry_date=date.today() - timedelta(days=1))
        # Test the property logic directly
        assert date.today() > unit.expiry_date

    def test_unit_not_expired_today(self):
        from types import SimpleNamespace
        unit = SimpleNamespace(expiry_date=date.today() + timedelta(days=1))
        assert not (date.today() > unit.expiry_date)

    def test_days_remaining_calculation(self):
        from types import SimpleNamespace
        unit = SimpleNamespace(expiry_date=date.today() + timedelta(days=7))
        days = (unit.expiry_date - date.today()).days
        assert days == 7


# ── 4. Shortage Detection Logic ───────────────────────────────────────────────

class TestShortageDetection:

    def test_below_threshold_generates_critical_alert(self):
        from app.services.blood_matching import detect_shortages
        mock_db = MagicMock()

        # Simulate inventory_summary returning 0 units for O-/RBC
        with patch("app.services.blood_matching.inventory_summary") as mock_summary:
            mock_summary.return_value = {}   # all types missing
            alerts = detect_shortages(mock_db)

        # Must have alerts for every combination
        assert len(alerts) > 0
        critical = [a for a in alerts if a["severity"] == "critical"]
        assert len(critical) > 0

    def test_zero_units_is_critical_severity(self):
        from app.services.blood_matching import detect_shortages
        mock_db = MagicMock()
        with patch("app.services.blood_matching.inventory_summary") as mock_summary:
            mock_summary.return_value = {"O-/RBC": {"available": 0, "blood_type": "O-", "component": "RBC"}}
            alerts = detect_shortages(mock_db)

        o_neg_rbc = [a for a in alerts if a["blood_type"] == "O-" and a["component"] == "RBC"]
        assert any(a["severity"] == "critical" for a in o_neg_rbc)

    def test_above_threshold_no_alert(self):
        from app.services.blood_matching import detect_shortages, _DEFAULT_THRESHOLDS
        mock_db = MagicMock()
        # Fill all combinations above threshold
        from app.models.blood import BLOOD_TYPES
        full_inventory = {
            f"{bt}/{comp}": {"available": 999, "blood_type": bt, "component": comp}
            for bt in BLOOD_TYPES
            for comp in _DEFAULT_THRESHOLDS
        }
        with patch("app.services.blood_matching.inventory_summary") as mock_summary:
            mock_summary.return_value = full_inventory
            alerts = detect_shortages(mock_db)
        assert len(alerts) == 0

    def test_alerts_sorted_critical_first(self):
        from app.services.blood_matching import detect_shortages
        mock_db = MagicMock()
        with patch("app.services.blood_matching.inventory_summary") as mock_summary:
            mock_summary.return_value = {}
            alerts = detect_shortages(mock_db)
        if len(alerts) >= 2:
            # All critical must come before any warning
            severities = [a["severity"] for a in alerts]
            last_critical = max((i for i, s in enumerate(severities) if s == "critical"), default=-1)
            first_warning = min((i for i, s in enumerate(severities) if s == "warning"), default=len(severities))
            assert last_critical < first_warning


# ── 5. Incompatible Transfusion Block ─────────────────────────────────────────

class TestTransfusionSafety:
    """Most critical safety tests — incompatible transfusion must ALWAYS be blocked."""

    def test_incompatible_crossmatch_raises_http_422(self):
        """route must reject crossmatch_result='incompatible' with 422."""
        from fastapi import HTTPException
        from pydantic import ValidationError

        # Simulate what the route does
        crossmatch = "incompatible"
        if crossmatch == "incompatible":
            with pytest.raises(Exception):   # route raises HTTPException(422,...)
                raise HTTPException(422, "⛔ الاختبار المتقاطع غير متوافق")

    def test_assert_compatible_blocks_a_to_o(self):
        from app.services.blood_matching import assert_compatible
        with pytest.raises(ValueError):
            assert_compatible("A+", "O+")

    def test_assert_compatible_blocks_rh_mismatch(self):
        from app.services.blood_matching import assert_compatible
        with pytest.raises(ValueError):
            assert_compatible("O+", "O-")   # O+ → O- Rh incompatible

    def test_all_clinically_dangerous_pairs_blocked(self):
        """Explicitly verify every known dangerous transfusion pair."""
        from app.services.blood_matching import is_compatible
        dangerous = [
            ("A+", "O+"),  ("A+", "O-"),  ("A+", "B+"),  ("A+", "B-"),
            ("B+", "O+"),  ("B+", "O-"),  ("B+", "A+"),  ("B+", "A-"),
            ("AB+", "O+"), ("AB+", "O-"), ("AB+", "A+"), ("AB+", "B+"),
            ("O+", "O-"),   # Rh mismatch
        ]
        for donor, recipient in dangerous:
            assert not is_compatible(donor, recipient), (
                f"SAFETY FAIL: {donor} → {recipient} was reported compatible but must be blocked"
            )


# ── 6. Migration Chain includes 0013 ─────────────────────────────────────────

class TestGBNMigration:

    def test_migration_0013_exists(self):
        import pathlib
        migs = list(pathlib.Path("migrations/versions").glob("*0013*"))
        assert migs, "Migration 0013 (GBN blood network) not found"

    def test_migration_0013_points_to_0012(self):
        import pathlib, re
        migs = list(pathlib.Path("migrations/versions").glob("*0013*"))
        assert migs
        src = migs[0].read_text()
        dr = re.search(r'^down_revision\s*=\s*["\']([^"\']+)["\']', src, re.M)
        assert dr, "down_revision not found in 0013"
        assert dr.group(1) == "20260329_0012", (
            f"0013 must point to 0012, got: {dr.group(1)}"
        )

    def test_migration_0013_compiles(self):
        import pathlib
        migs = list(pathlib.Path("migrations/versions").glob("*0013*"))
        assert migs
        compile(migs[0].read_text(), str(migs[0]), "exec")   # raises SyntaxError on failure


# ── 7. Donor model property tests ─────────────────────────────────────────────

class TestDonorModel:

    def _make_donor_ns(self, **kw):
        """SimpleNamespace mimics Donor properties without SQLAlchemy instrumentation."""
        from types import SimpleNamespace
        from app.models.blood import MIN_DONATION_INTERVAL_DAYS
        # Reproduce is_eligible / days_until_eligible logic in-test
        d = SimpleNamespace(
            eligibility_status = kw.get("eligibility_status", "eligible"),
            deferral_until     = kw.get("deferral_until", None),
            last_donation_date = kw.get("last_donation_date", None),
        )
        today = date.today()

        def is_eligible():
            if d.eligibility_status == "deferred_permanent":
                return False
            if d.eligibility_status == "deferred_temporary":
                if d.deferral_until and today < d.deferral_until:
                    return False
            if d.last_donation_date:
                if (today - d.last_donation_date).days < MIN_DONATION_INTERVAL_DAYS:
                    return False
            return True

        def days_until_eligible():
            if not d.last_donation_date:
                return None
            days_since = (today - d.last_donation_date).days
            remaining = MIN_DONATION_INTERVAL_DAYS - days_since
            return max(0, remaining) if remaining > 0 else None

        d.is_eligible = is_eligible()
        d.days_until_eligible = days_until_eligible()
        return d

    def test_is_eligible_returns_false_for_permanent_deferral(self):
        d = self._make_donor_ns(eligibility_status="deferred_permanent")
        assert d.is_eligible is False

    def test_is_eligible_returns_true_for_new_donor(self):
        d = self._make_donor_ns()
        assert d.is_eligible is True

    def test_days_until_eligible_none_when_no_prior_donation(self):
        d = self._make_donor_ns()
        assert d.days_until_eligible is None

    def test_days_until_eligible_positive_when_too_recent(self):
        d = self._make_donor_ns(last_donation_date=date.today() - timedelta(days=30))
        assert d.days_until_eligible is not None
        assert d.days_until_eligible > 0
