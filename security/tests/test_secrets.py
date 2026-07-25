"""Tests for GSF Secret Management (GSF-001/002).

Tests secret validation, rotation, environment backend, scanner patterns,
and edge cases for the secrets module.
"""

from __future__ import annotations

import json
import os
import re
import string
import sys
import tempfile
from pathlib import Path

import pytest

# Allow imports from the security package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.rotate_secrets import AuditLogger, RotationConfig, SecretValidator

# ---------------------------------------------------------------------------
# Secret Validation Tests
# ---------------------------------------------------------------------------

class TestSecretValidation:
    """Test secret strength validation and entropy calculation."""

    @pytest.fixture
    def validator(self) -> SecretValidator:
        config = {
            "min_secret_length": 32,
            "min_entropy_bits": 128,
            "allowed_characters": (
                string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|;:,.<>?"
            ),
        }
        return SecretValidator(config)

    def test_generate_default_length(self, validator: SecretValidator) -> None:
        secret = validator.generate()
        assert len(secret) == 32

    def test_generate_custom_length(self, validator: SecretValidator) -> None:
        secret = validator.generate(length=64)
        assert len(secret) == 64

    def test_generate_varied_characters(self, validator: SecretValidator) -> None:
        secrets = [validator.generate() for _ in range(100)]
        unique = len(set(secrets))
        assert unique > 90

    def test_validate_strong_secret(self, validator: SecretValidator) -> None:
        strong = "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8S9t0U1v2W3x4Y5z6A1b2C3d4!"
        valid, errors = validator.validate(strong)
        assert valid
        assert errors == []

    def test_validate_short_secret(self, validator: SecretValidator) -> None:
        short = "Ab1!"
        valid, errors = validator.validate(short)
        assert not valid
        assert any("Length" in e for e in errors)

    def test_validate_only_lowercase(self, validator: SecretValidator) -> None:
        weak = "a" * 40
        valid, errors = validator.validate(weak)
        assert not valid
        assert any("character categories" in e for e in errors)

    def test_validate_low_entropy(self, validator: SecretValidator) -> None:
        low_entropy = "a" * 50
        valid, errors = validator.validate(low_entropy)
        assert not valid

    def test_validate_high_entropy(self, validator: SecretValidator) -> None:
        high = "".join(
            __import__("secrets").choice(string.ascii_letters + string.digits + "!@#$%")
            for _ in range(50)
        )
        valid, errors = validator.validate(high)
        assert valid

    def test_entropy_estimate_empty(self, validator: SecretValidator) -> None:
        entropy = validator._estimate_entropy("")
        assert entropy == 0.0

    def test_entropy_estimate_single_char(self, validator: SecretValidator) -> None:
        entropy = validator._estimate_entropy("aaaaa")
        assert entropy == 0.0

    def test_entropy_estimate_high(self, validator: SecretValidator) -> None:
        entropy = validator._estimate_entropy(
            "".join(__import__("secrets").choice(string.printable) for _ in range(100))
        )
        assert entropy > 4.0


# ---------------------------------------------------------------------------
# Secret Rotation Tests
# ---------------------------------------------------------------------------

class TestSecretRotation:
    """Test secret rotation configuration and logic."""

    def test_rotation_config_defaults(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            f.write(b"rotation:\n  secrets:\n    rotation_enabled: true\n")
            tmp_path = f.name

        try:
            config = RotationConfig(tmp_path)
            assert config.rotate_all_secrets() is True
        finally:
            os.unlink(tmp_path)

    def test_rotation_config_file(self) -> None:
        config_content = """
rotation:
  secrets:
    rotation_enabled: true
    check_interval_hours: 12
    backends:
      env: true
      vault: false
"""
        with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as f:
            f.write(config_content)
            tmp_path = f.name

        try:
            config = RotationConfig(tmp_path)
            assert config.secret_config["check_interval_hours"] == 12
            assert config.secret_config["backends"]["vault"] is False
        finally:
            os.unlink(tmp_path)

    def test_rotation_config_missing_file(self) -> None:
        config = RotationConfig("/tmp/nonexistent/rotation.yaml")
        assert config.rotate_all_secrets() is True

    def test_audit_logger_file(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as f:
            log_path = f.name

        try:
            audit = AuditLogger(log_path)
            audit.log("TEST_SECRET", "rotate", "SUCCESS", "test rotation")
            content = Path(log_path).read_text()
            assert "TEST_SECRET" in content
            assert "SUCCESS" in content
        finally:
            os.unlink(log_path)


# ---------------------------------------------------------------------------
# Secret Scanner Tests
# ---------------------------------------------------------------------------

class TestSecretScanner:
    """Test secret scanning patterns."""

    SECRET_PATTERNS = [
        (r'(?i)api[_-]?key[=\s"\']+[A-Za-z0-9_\-]{16,}', "API Key"),
        (r'(?i)secret[=\s"\']+[A-Za-z0-9_\-!@#$%^&*()=+]{16,}', "Secret"),
        (r'(?i)password[=\s"\']+[^,;\])\)\s]{8,}', "Password"),
        (r"AKIA[0-9A-Z]{16}", "AWS Access Key"),
        (r"(?i)ghp_[A-Za-z0-9]{36}", "GitHub Token"),
        (r"(?i)-----BEGIN\s+(RSA|EC|DSA|OPENSSH|PRIVATE)\s+KEY-----", "Private Key"),
    ]

    @pytest.mark.parametrize(
        "content,expected_type",
        [
            ('password = "super_secret_123!"', "Password"),
            ("API_KEY=abc123def456ghi789jkl012mno345pqr", "API Key"),
            ("AKIA1234567890123456", "AWS Access Key"),
            ("ghp_abcdefghijklmnopqrstuvwxyz0123456789", "GitHub Token"),
            ("-----BEGIN RSA PRIVATE KEY-----", "Private Key"),
        ],
    )
    def test_secret_detection(self, content: str, expected_type: str) -> None:
        detected = False
        for pattern, name in self.SECRET_PATTERNS:
            if re.search(pattern, content):
                if name == expected_type:
                    detected = True
                break
        assert detected, f"Failed to detect {expected_type} in: {content[:40]}"

    @pytest.mark.parametrize(
        "content",
        [
            'password = "example"',
            "api_key = placeholder",
            "secret = none",
            "not a secret at all",
            "# password is set via environment variable",
        ],
    )
    def test_no_false_positive(self, content: str) -> None:
        for pattern, _ in self.SECRET_PATTERNS:
            if re.search(pattern, content):
                pytest.fail(f"False positive for pattern in: {content}")

    def test_scanner_skips_binary(self) -> None:
        binary = b"\x00\x01\x02\x03password=secret\xff\xfe"
        detected = False
        for pattern, _ in self.SECRET_PATTERNS:
            try:
                if re.search(pattern, binary.decode("utf-8", errors="ignore")):
                    detected = True
            except Exception:
                pass
        assert not detected, "Binary content caused false positive"


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------

class TestSecretEdgeCases:
    """Test edge cases for secret management."""

    def test_empty_secret(self) -> None:
        validator = SecretValidator({})
        valid, errors = validator.validate("")
        assert not valid

    def test_unicode_secret(self) -> None:
        validator = SecretValidator({"min_secret_length": 8})
        unicode_secret = "héllo wörld 🔐 秘密 パスワード"
        valid, errors = validator.validate(unicode_secret)
        assert not valid  # Unicode may not have enough ASCII character categories

    def test_max_length_secret(self) -> None:
        validator = SecretValidator({"min_secret_length": 8})
        long_secret = "A1!" + "b" * 1000
        valid, errors = validator.validate(long_secret)
        assert valid

    def test_secret_with_newlines(self) -> None:
        validator = SecretValidator({"min_secret_length": 8})
        secret = "A1!bcde\nfghij"
        valid, _ = validator.validate(secret)
        assert not valid  # newline is not a standard character category

    def test_rotation_config_empty(self) -> None:
        config = RotationConfig.__new__(RotationConfig)
        config._data = {}
        assert isinstance(config.validation_config, dict)
        assert isinstance(config.notification_config, dict)

    def test_generate_empty_allowed_chars(self) -> None:
        validator = SecretValidator({"min_secret_length": 10, "allowed_characters": "ABC"})
        secret = validator.generate(10)
        assert all(c in "ABC" for c in secret)
        assert len(secret) == 10


# ---------------------------------------------------------------------------
# Integration-Style Tests
# ---------------------------------------------------------------------------

class TestSecretIntegration:
    """Integration tests for secret workflows."""

    def test_generate_validate_cycle(self) -> None:
        validator = SecretValidator({
            "min_secret_length": 32,
            "min_entropy_bits": 128,
        })
        for _ in range(10):
            secret = validator.generate()
            valid, _ = validator.validate(secret)
            assert valid, f"Generated secret failed validation: {secret[:16]}..."

    def test_audit_log_rotation_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "rotations.log")
            audit = AuditLogger(log_path)

            for i in range(5):
                audit.log(f"SECRET_{i}", "rotate", "SUCCESS", f"rotation_{i}")

            content = Path(log_path).read_text()
            lines = content.strip().split("\n")
            assert len(lines) == 5
            for i, line in enumerate(lines):
                assert f"SECRET_{i}" in line
                assert "SUCCESS" in line
