"""
GULA Platform - Security & API Tests
Tests for authentication, authorization, mobile API, and security controls.
Run with: python -m pytest backend/tests/ -v
"""

import os
import secrets
import sys
import time
from unittest.mock import MagicMock, patch

# Set ENV=development before any app imports
os.environ.setdefault("ENV", "development")
os.environ.setdefault("DATABASE_URL", "sqlite:///test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")


# ===== 1. JWT TOKEN TESTS =====

class TestJWTTokens:
    """Test access and refresh token generation/validation."""

    def test_create_access_token(self):
        """Should create a valid access token."""
        from app.security.auth import create_token, decode_token
        token = create_token({"user_id": 1, "lab_id": 1, "role": "admin"})
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 20

    def test_decode_access_token(self):
        """Should decode a valid access token."""
        from app.security.auth import create_token, decode_token
        token = create_token({"user_id": 42, "lab_id": 5, "role": "staff"})
        payload = decode_token(token)
        assert payload is not None
        assert payload["user_id"] == 42
        assert payload["lab_id"] == 5
        assert payload["role"] == "staff"
        assert payload["type"] == "access"

    def test_invalid_token_returns_none(self):
        """Invalid token should return None, not raise exception."""
        from app.security.auth import decode_token
        result = decode_token("invalid.token.string")
        assert result is None

    def test_empty_token_returns_none(self):
        """Empty token should return None."""
        from app.security.auth import decode_token
        assert decode_token("") is None

    def test_create_refresh_token(self):
        """Should create a valid refresh token."""
        from app.security.auth import create_refresh_token, decode_refresh_token
        token = create_refresh_token({"user_id": 1, "lab_id": 1, "role": "admin"})
        assert token is not None
        assert isinstance(token, str)

    def test_decode_refresh_token(self):
        """Should decode a valid refresh token."""
        from app.security.auth import create_refresh_token, decode_refresh_token
        token = create_refresh_token({"user_id": 99, "lab_id": 3, "role": "technician"})
        payload = decode_refresh_token(token)
        assert payload is not None
        assert payload["user_id"] == 99
        assert payload["type"] == "refresh"

    def test_access_token_rejected_as_refresh(self):
        """Access token should not be accepted as refresh token."""
        from app.security.auth import create_token, decode_refresh_token
        access_token = create_token({"user_id": 1, "lab_id": 1, "role": "admin"})
        result = decode_refresh_token(access_token)
        assert result is None

    def test_refresh_token_rejected_as_access(self):
        """Refresh token should not be accepted as access token."""
        from app.security.auth import create_refresh_token, decode_token
        refresh_token = create_refresh_token({"user_id": 1, "lab_id": 1, "role": "admin"})
        result = decode_token(refresh_token)
        assert result is None

    def test_tokens_differ_for_different_users(self):
        """Different users should receive different tokens."""
        from app.security.auth import create_token
        token1 = create_token({"user_id": 1, "lab_id": 1, "role": "admin"})
        token2 = create_token({"user_id": 2, "lab_id": 1, "role": "admin"})
        token3 = create_token({"user_id": 1, "lab_id": 2, "role": "admin"})
        assert token1 != token2
        assert token1 != token3


# ===== 2. PASSWORD HASHING TESTS =====

class TestPasswordHashing:
    """Test bcrypt password hashing."""

    @staticmethod
    def _can_hash():
        """Check if bcrypt is working in this environment."""
        try:
            from app.security.auth import hash_password
            hash_password("test")
            return True
        except Exception:
            return False

    def test_hash_password_returns_hash(self):
        """Should return a bcrypt hash string."""
        if not self._can_hash():
            import pytest; pytest.skip("bcrypt not available in test environment")
        from app.security.auth import hash_password
        h = hash_password("MyPassword123")
        assert h is not None
        assert h.startswith("$2")  # bcrypt prefix

    def test_verify_correct_password(self):
        """Correct password should verify successfully."""
        if not self._can_hash():
            import pytest; pytest.skip("bcrypt not available in test environment")
        from app.security.auth import hash_password, verify_password
        h = hash_password("CorrectHorseBatteryStaple")
        assert verify_password("CorrectHorseBatteryStaple", h) is True

    def test_verify_wrong_password(self):
        """Wrong password should fail verification."""
        if not self._can_hash():
            import pytest; pytest.skip("bcrypt not available in test environment")
        from app.security.auth import hash_password, verify_password
        h = hash_password("CorrectPassword")
        assert verify_password("WrongPassword", h) is False

    def test_different_hashes_for_same_password(self):
        """bcrypt should produce different hashes due to salting."""
        if not self._can_hash():
            import pytest; pytest.skip("bcrypt not available in test environment")
        from app.security.auth import hash_password
        h1 = hash_password("SamePassword")
        h2 = hash_password("SamePassword")
        assert h1 != h2  # bcrypt uses random salt


# ===== 3. ENCRYPTION TESTS =====

class TestEncryption:
    """Test Fernet encryption/decryption."""

    def test_encrypt_and_decrypt(self):
        """Should encrypt and decrypt correctly."""
        from app.security.encryption import decrypt, encrypt
        original = "sensitive data - بيانات حساسة"
        encrypted = encrypt(original)
        assert encrypted != original
        decrypted = decrypt(encrypted)
        assert decrypted == original

    def test_encrypt_produces_different_ciphertexts(self):
        """Same plaintext should produce different ciphertexts (Fernet uses IV)."""
        from app.security.encryption import encrypt
        c1 = encrypt("same data")
        c2 = encrypt("same data")
        assert c1 != c2  # Fernet adds randomness

    def test_decrypt_wrong_data_raises(self):
        """Decrypting invalid data should raise exception."""
        import pytest
        from app.security.encryption import decrypt
        with pytest.raises(Exception):
            decrypt("not-encrypted-data")


# ===== 4. RATE LIMITING TESTS =====

class TestRateLimiting:
    """Test rate limiting behavior."""

    def test_rate_limiter_allows_up_to_limit(self):
        """Should allow requests up to the limit."""
        from app.security.rate_limit import RateLimiter
        limiter = RateLimiter()
        key = f"test:{secrets.token_hex(8)}"
        for _ in range(5):
            assert limiter.check(key, max_requests=5, window_seconds=60) is True

    def test_rate_limiter_blocks_over_limit(self):
        """Should block requests exceeding the limit."""
        from app.security.rate_limit import RateLimiter
        limiter = RateLimiter()
        key = f"test:{secrets.token_hex(8)}"
        for _ in range(5):
            limiter.check(key, max_requests=5, window_seconds=60)
        assert limiter.check(key, max_requests=5, window_seconds=60) is False

    def test_get_client_ip_returns_string(self):
        """get_client_ip should return a string IP."""
        from app.security.rate_limit import get_client_ip
        mock_request = MagicMock()
        mock_request.client.host = "192.168.1.1"
        mock_request.headers.get.return_value = None
        ip = get_client_ip(mock_request)
        assert isinstance(ip, str)
        assert len(ip) > 0


# ===== 5. CONFIG TESTS =====

class TestConfig:
    """Test configuration values."""

    def test_config_has_refresh_token_settings(self):
        """Config should have refresh token settings."""
        from app import config
        assert hasattr(config, "REFRESH_TOKEN_SECRET")
        assert hasattr(config, "REFRESH_TOKEN_EXPIRE_DAYS")

    def test_refresh_token_expire_days_reasonable(self):
        """Refresh token expiry should be between 1 and 365 days."""
        from app.config import REFRESH_TOKEN_EXPIRE_DAYS
        assert 1 <= REFRESH_TOKEN_EXPIRE_DAYS <= 365

    def test_config_has_mobile_settings(self):
        """Config should have mobile-related settings."""
        from app import config
        assert hasattr(config, "FCM_SERVER_KEY")
        assert hasattr(config, "ENABLE_API_DOCS")

    def test_config_has_max_body_size(self):
        """Config should have request body size limits."""
        from app import config
        assert hasattr(config, "MAX_REQUEST_BODY_MB")
        assert config.MAX_REQUEST_BODY_MB > 0

    def test_app_version_format(self):
        """App version should be in semver format."""
        import re

        from app.config import APP_VERSION
        assert re.match(r"^\d+\.\d+\.\d+$", APP_VERSION), f"Invalid version: {APP_VERSION}"

    def test_platform_name_arabic(self):
        """Platform should have Arabic name."""
        from app.config import PLATFORM_NAME_AR
        assert PLATFORM_NAME_AR
        assert len(PLATFORM_NAME_AR) > 2


# ===== 6. SECURITY CONTROLS =====

class TestSecurityControls:
    """Test security control mechanisms."""

    def test_national_id_hashing_is_deterministic(self):
        """Same national ID should always produce same hash."""
        from app.services.identity import hash_national_id
        h1 = hash_national_id("123456789012")
        h2 = hash_national_id("123456789012")
        assert h1 == h2

    def test_national_id_hashing_different_ids(self):
        """Different national IDs should produce different hashes."""
        from app.services.identity import hash_national_id
        h1 = hash_national_id("123456789012")
        h2 = hash_national_id("123456789013")
        assert h1 != h2

    def test_national_id_hash_not_reversible(self):
        """Hash should not contain the original national ID."""
        from app.services.identity import hash_national_id
        nid = "123456789012"
        h = hash_national_id(nid)
        assert nid not in h

    def test_intrusion_detector_blocks_brute_force(self):
        """Should block IP after repeated failures."""
        from app.security.intrusion_detection import IntrusionDetector
        detector = IntrusionDetector(max_attempts=3, window_seconds=60)
        ip = "203.0.113.100"
        for _ in range(3):
            detector.detect(ip)
        assert detector.detect(ip) == "blocked"

    def test_no_tmp_file_in_admin_setup(self):
        """Admin setup code should NOT write to /tmp."""
        import inspect

        from app.routes import admin
        source = inspect.getsource(admin.ensure_master_admin)
        assert "/tmp/.gula_admin_pw" not in source, (
            "SECURITY: Admin setup must not write passwords to /tmp"
        )


# ===== 7. MOBILE API TESTS =====

class TestMobileAPILogic:
    """Test mobile API helper functions."""

    def test_role_arabic_translation(self):
        """Roles should have Arabic translations."""
        from app.routes.mobile import _role_ar
        assert _role_ar("admin") == "مدير المختبر"
        assert _role_ar("master_admin") == "مدير المنصة"
        assert _role_ar("staff") == "موظف"
        assert _role_ar("technician") == "تقني مختبر"

    def test_permissions_admin(self):
        """Admin should have extended permissions."""
        from app.routes.mobile import _get_permissions
        perms = _get_permissions("admin")
        assert "manage_users" in perms
        assert "view_patients" in perms
        assert "manage_lab" in perms

    def test_permissions_staff(self):
        """Staff should have basic permissions."""
        from app.routes.mobile import _get_permissions
        perms = _get_permissions("staff")
        assert "view_patients" in perms
        assert "create_order" in perms
        assert "manage_users" not in perms

    def test_permissions_technician(self):
        """Technician should have specific lab permissions."""
        from app.routes.mobile import _get_permissions
        perms = _get_permissions("technician")
        assert "enter_results" in perms
        assert "view_samples" in perms


# ===== 8. INPUT VALIDATION TESTS =====

class TestInputValidation:
    """Test Pydantic validation for security."""

    def test_patient_name_length_validation(self):
        """Patient name should reject too-short names."""
        import pytest
        from app.routes.patients import PatientCreate
        with pytest.raises(Exception):
            PatientCreate(full_name="A", phone="07901234567")  # name too short

    def test_patient_phone_validation(self):
        """Patient phone should only accept Iraqi numbers."""
        import pytest
        from app.routes.patients import PatientCreate
        # Valid Iraqi number
        p = PatientCreate(full_name="Test Name", phone="07901234567")
        assert p.phone == "07901234567"
        # Invalid number
        with pytest.raises(Exception):
            PatientCreate(full_name="Test Name", phone="12345")

    def test_patient_gender_validation(self):
        """Gender should only accept valid values."""
        import pytest
        from app.routes.patients import PatientCreate
        with pytest.raises(Exception):
            PatientCreate(full_name="Test Name", phone="07901234567", gender="unknown")

    def test_patient_birth_date_future_rejected(self):
        """Future birth dates should be rejected."""
        import pytest
        from app.routes.patients import PatientCreate
        with pytest.raises(Exception):
            PatientCreate(
                full_name="Test Name",
                phone="07901234567",
                birth_date="2099-01-01",
            )

    def test_email_validation(self):
        """Invalid email should be rejected."""
        import pytest
        from app.routes.patients import PatientCreate
        with pytest.raises(Exception):
            PatientCreate(
                full_name="Test Name",
                phone="07901234567",
                email="not-an-email",
            )


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
