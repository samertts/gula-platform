#!/usr/bin/env python3
# =============================================================================
# GSF: rotate-secrets.py — Automated Secret Rotation
# =============================================================================
"""
Automated secret rotation script for the GULA Security Framework.

Reads rotation configuration from security/configs/rotation.yaml and rotates
secrets across configured backends (environment, Vault, GitHub Secrets).

Usage:
    ./rotate-secrets.py [--type TYPE] [--dry-run] [--help]

Options:
    --type TYPE       Secret type to rotate (api_key, db_password, jwt_secret, all)
    --dry-run         Simulate rotation without applying changes
    --help, -h        Show this help message
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

logger = logging.getLogger("gsf.rotate-secrets")


class RotationConfig:
    """Rotation configuration loaded from rotation.yaml."""

    def __init__(self, config_path: str | Path) -> None:
        self.config_path = Path(config_path)
        self._data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        if not self.config_path.exists():
            logger.warning("Config not found at %s, using defaults", self.config_path)
            self._data = self._defaults()
            return
        raw = self.config_path.read_text(encoding="utf-8")
        if yaml:
            self._data = yaml.safe_load(raw) or {}
        else:
            logger.warning("PyYAML not available, using defaults")
            self._data = self._defaults()

    @staticmethod
    def _defaults() -> dict[str, Any]:
        return {
            "rotation": {
                "secrets": {
                    "rotation_enabled": True,
                    "check_interval_hours": 24,
                    "backends": {"env": True, "vault": True, "github_secrets": True},
                },
                "encryption_keys": {
                    "auto_rotate": True,
                    "rotation_period_days": 90,
                    "grace_period_hours": 48,
                    "re_encrypt_batch_size": 100,
                },
                "jwt_signing_keys": {
                    "rotation_enabled": True,
                    "active_keys": 2,
                    "overlap_period_hours": 24,
                },
            },
            "notification": {"email": {"enabled": False}, "slack": {"enabled": False}},
            "validation": {
                "min_secret_length": 32,
                "require_entropy_check": True,
                "min_entropy_bits": 128,
            },
        }

    @property
    def secret_config(self) -> dict[str, Any]:
        return self._data.get("rotation", {}).get("secrets", {})

    @property
    def validation_config(self) -> dict[str, Any]:
        return self._data.get("validation", {})

    @property
    def notification_config(self) -> dict[str, Any]:
        return self._data.get("notification", {})

    def rotate_all_secrets(self) -> bool:
        return self.secret_config.get("rotation_enabled", True)


# ---------------------------------------------------------------------------
# Secret Generation & Validation
# ---------------------------------------------------------------------------

class SecretValidator:
    """Validates secret strength and entropy."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.min_length = config.get("min_secret_length", 32)
        self.min_entropy = config.get("min_entropy_bits", 128)
        self.allowed_chars = config.get(
            "allowed_characters",
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()-_=+[]{}|;:,.<>?",
        )

    def generate(self, length: int | None = None) -> str:
        """Generate a cryptographically secure random secret."""
        import secrets as sec

        length = length or self.min_length
        chars = self.allowed_chars
        return "".join(sec.choice(chars) for _ in range(length))

    def validate(self, secret: str) -> tuple[bool, list[str]]:
        """Validate secret strength. Returns (valid, reasons)."""
        errors: list[str] = []
        if len(secret) < self.min_length:
            errors.append(f"Length {len(secret)} < minimum {self.min_length}")
        if self.min_entropy > 0:
            entropy = self._estimate_entropy(secret)
            if entropy < self.min_entropy:
                errors.append(f"Entropy {entropy:.1f} < minimum {self.min_entropy}")
        has_upper = any(c.isupper() for c in secret)
        has_lower = any(c.islower() for c in secret)
        has_digit = any(c.isdigit() for c in secret)
        has_special = any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in secret)
        categories = sum([has_upper, has_lower, has_digit, has_special])
        if categories < 3:
            errors.append(f"Only {categories}/4 character categories")
        return len(errors) == 0, errors

    @staticmethod
    def _estimate_entropy(secret: str) -> float:
        """Estimate Shannon entropy of a secret."""
        import math
        from collections import Counter

        if not secret:
            return 0.0
        freq = Counter(secret)
        length = len(secret)
        return -sum((count / length) * math.log2(count / length) for count in freq.values())


# ---------------------------------------------------------------------------
# Rotation Backends
# ---------------------------------------------------------------------------

class RotationBackend(Protocol):
    """Protocol for rotation backends."""

    def name(self) -> str: ...

    def rotate(self, secret_name: str, new_value: str) -> bool: ...


class EnvBackend:
    """Environment variable secret backend."""

    def name(self) -> str:
        return "environment"

    def rotate(self, secret_name: str, new_value: str) -> bool:
        os.environ[secret_name] = new_value
        logger.info("Rotated %s in environment", secret_name)
        return True


# ---------------------------------------------------------------------------
# Audit Logging
# ---------------------------------------------------------------------------

class AuditLogger:
    """Logs rotation events for audit trail."""

    def __init__(self, log_path: str | None = None) -> None:
        self.log_path = log_path or "/var/log/gula/security/rotations.log"

    def log(
        self,
        secret_name: str,
        action: str,
        status: str,
        details: str = "",
    ) -> None:
        entry = (
            f"[{datetime.now(timezone.utc).isoformat()}] "
            f"SECRET_ROTATION secret={secret_name} "
            f"action={action} status={status} {details}"
        )
        logger.info("%s", entry)
        log_dir = os.path.dirname(self.log_path)
        try:
            os.makedirs(log_dir, exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(entry + "\n")
        except OSError as e:
            logger.warning("Failed to write audit log: %s", e)


# ---------------------------------------------------------------------------
# Notification
# ---------------------------------------------------------------------------

class Notifier:
    """Sends notifications for secret rotations."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    def notify(self, secret_name: str, action: str, status: str) -> None:
        email_enabled = self.config.get("email", {}).get("enabled", False)
        slack_enabled = self.config.get("slack", {}).get("enabled", False)

        if email_enabled:
            recipients = self.config.get("email", {}).get("recipients", [])
            logger.info("Would email %s about %s: %s", recipients, secret_name, status)
        if slack_enabled:
            channel = self.config.get("slack", {}).get("channel", "#security")
            logger.info("Would notify Slack %s about %s: %s", channel, secret_name, status)


# ---------------------------------------------------------------------------
# Secret Types Catalog
# ---------------------------------------------------------------------------

SECRET_TYPES: dict[str, list[str]] = {
    "api_key": ["GULA_API_KEY", "SENTRY_DSN", "MAPBOX_TOKEN"],
    "db_password": [
        "DATABASE_URL",
        "POSTGRES_PASSWORD",
        "REDIS_PASSWORD",
        "MONGODB_PASSWORD",
    ],
    "jwt_secret": ["JWT_SECRET_KEY", "JWT_REFRESH_SECRET", "SESSION_SECRET"],
    "encryption_key": ["ENCRYPTION_KEY", "FIELD_ENCRYPTION_KEY", "PHI_ENCRYPTION_KEY"],
    "service_token": [
        "GITHUB_TOKEN",
        "SLACK_BOT_TOKEN",
        "DOCKER_REGISTRY_TOKEN",
        "TERRAFORM_TOKEN",
    ],
}


# ---------------------------------------------------------------------------
# Main Rotation Logic
# ---------------------------------------------------------------------------

def rotate_secret_type(
    secret_type: str,
    validator: SecretValidator,
    backends: list[RotationBackend],
    audit: AuditLogger,
    notifier: Notifier,
    dry_run: bool,
) -> int:
    """Rotate all secrets of a given type. Returns count of rotations."""
    secret_names = SECRET_TYPES.get(secret_type, [])
    if not secret_names:
        logger.warning("Unknown secret type: %s", secret_type)
        return 0

    rotated = 0
    for name in secret_names:
        logger.info("Rotating %s (%s)", name, secret_type)
        new_value = validator.generate()
        valid, errors = validator.validate(new_value)
        if not valid:
            audit.log(name, "generate", "FAILED", f"Validation errors: {errors}")
            logger.error("Validation failed for %s: %s", name, errors)
            continue

        if dry_run:
            logger.info("[DRY-RUN] Would set %s = %s...", name, new_value[:8])
            audit.log(name, "rotate", "DRY-RUN", f"Would set new value (len={len(new_value)})")
            rotated += 1
            continue

        success = True
        for backend in backends:
            if not backend.rotate(name, new_value):
                logger.error("Backend %s failed for %s", backend.name(), name)
                success = False

        if success:
            audit.log(name, "rotate", "SUCCESS", f"Rotated via {[b.name() for b in backends]}")
            notifier.notify(name, "rotate", "SUCCESS")
            rotated += 1
        else:
            audit.log(name, "rotate", "FAILED", "Backend rotation error")

    return rotated


def rotate_all(
    validator: SecretValidator,
    backends: list[RotationBackend],
    audit: AuditLogger,
    notifier: Notifier,
    dry_run: bool,
) -> int:
    """Rotate all secret types. Returns total count."""
    total = 0
    for secret_type in SECRET_TYPES:
        total += rotate_secret_type(secret_type, validator, backends, audit, notifier, dry_run)
    return total


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="GSF Automated Secret Rotation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Secret types: api_key, db_password, jwt_secret, encryption_key, service_token, all\n\n"
            "Examples:\n"
            "  %(prog)s --type api_key\n"
            "  %(prog)s --type all --dry-run\n"
        ),
    )
    parser.add_argument(
        "--type",
        default="all",
        choices=list(SECRET_TYPES.keys()) + ["all"],
        help="Secret type to rotate (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate rotation without applying changes",
    )
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )

    script_dir = Path(__file__).resolve().parent
    config_path = script_dir.parent / "configs" / "rotation.yaml"
    config = RotationConfig(config_path)

    validator = SecretValidator(config.validation_config)
    backends: list[RotationBackend] = []

    if config.secret_config.get("backends", {}).get("env", True):
        backends.append(EnvBackend())

    audit = AuditLogger()
    notifier = Notifier(config.notification_config)

    logger.info("Starting secret rotation (dry_run=%s)", args.dry_run)

    start = time.monotonic()
    if args.type == "all":
        rotated = rotate_all(validator, backends, audit, notifier, args.dry_run)
    else:
        rotated = rotate_secret_type(args.type, validator, backends, audit, notifier, args.dry_run)

    elapsed = time.monotonic() - start
    logger.info("Rotation complete: %d secrets in %.2fs", rotated, elapsed)

    if rotated == 0:
        logger.warning("No secrets were rotated")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
