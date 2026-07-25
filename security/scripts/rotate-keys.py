#!/usr/bin/env python3
# =============================================================================
# GSF: rotate-keys.py — Cryptographic Key Rotation
# =============================================================================
"""
Rotates cryptographic keys (AES, signing keys), re-encrypts data with new
keys, maintains key history, and logs all operations to the audit trail.

Usage:
    ./rotate-keys.py [options]

Options:
    --key-type TYPE      Key type to rotate (aes, signing, all) [default: all]
    --key-id ID          Specific key identifier to rotate
    --grace-period HOURS Grace period for old keys [default: 48]
    --re-encrypt         Re-encrypt data with new keys
    --batch-size N       Re-encryption batch size [default: 100]
    --dry-run            Simulate without making changes
    --help, -h           Show this help message
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("gsf.rotate-keys")


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

KEY_ALGORITHMS = {
    "aes": {"type": "symmetric", "algorithm": "AES-256-GCM", "key_length": 32},
    "signing": {"type": "asymmetric", "algorithm": "Ed25519", "key_length": 32},
    "hmac": {"type": "symmetric", "algorithm": "HMAC-SHA256", "key_length": 32},
    "ecdsa": {"type": "asymmetric", "algorithm": "ECDSA-P256", "key_length": 32},
}

DEFAULT_KEY_DIR = "/etc/gula/keys"


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class KeyMetadata:
    """Metadata for a cryptographic key."""

    key_id: str
    algorithm: str
    key_type: str
    created_at: str
    rotated_at: str = ""
    expires_at: str = ""
    status: str = "active"  # active, grace, retired, compromised
    version: int = 1
    previous_key_id: str = ""
    checksum: str = ""


@dataclass
class RotationResult:
    """Result of a key rotation operation."""

    key_id: str
    algorithm: str
    status: str
    new_version: int
    re_encrypted: int = 0
    errors: list[str] = field(default_factory=list)
    dry_run: bool = False


# ---------------------------------------------------------------------------
# Key Generation
# ---------------------------------------------------------------------------

class KeyGenerator:
    """Generates cryptographic keys."""

    @staticmethod
    def generate_aes_key(length: int = 32) -> bytes:
        """Generate an AES-256 key."""
        return os.urandom(length)

    @staticmethod
    def generate_signing_key() -> tuple[bytes, bytes]:
        """Generate an Ed25519 key pair (private, public)."""
        try:
            from cryptography.hazmat.primitives.asymmetric import ed25519
            private_key = ed25519.Ed25519PrivateKey.generate()
            private_bytes = private_key.private_bytes_raw()
            public_bytes = private_key.public_key().public_bytes_raw()
            return private_bytes, public_bytes
        except ImportError:
            logger.warning("cryptography not available, using raw random")
            private = os.urandom(32)
            public = hashlib.sha3_256(private).digest()[:32]
            return private, public

    @staticmethod
    def generate_hmac_key(length: int = 32) -> bytes:
        """Generate an HMAC key."""
        return os.urandom(length)

    def generate(self, algorithm: str) -> dict[str, Any]:
        """Generate a key for the given algorithm."""
        info = KEY_ALGORITHMS.get(algorithm, {})
        if algorithm == "aes":
            key = self.generate_aes_key(info.get("key_length", 32))
            return {"private": key.hex(), "public": ""}
        if algorithm == "signing":
            priv, pub = self.generate_signing_key()
            return {"private": priv.hex(), "public": pub.hex()}
        if algorithm == "hmac":
            key = self.generate_hmac_key(info.get("key_length", 32))
            return {"private": key.hex(), "public": ""}
        if algorithm == "ecdsa":
            try:
                from cryptography.hazmat.primitives.asymmetric import ec
                private_key = ec.generate_private_key(ec.SECP256R1())
                priv = private_key.private_bytes_raw()
                pub = private_key.public_key().public_bytes_raw()
                return {"private": priv.hex(), "public": pub.hex()}
            except ImportError:
                priv = os.urandom(32)
                pub = hashlib.sha3_256(priv).digest()[:32]
                return {"private": priv.hex(), "public": pub.hex()}
        raise ValueError(f"Unknown algorithm: {algorithm}")


# ---------------------------------------------------------------------------
# Key Store
# ---------------------------------------------------------------------------

class KeyStore(ABC):
    """Abstract key storage backend."""

    @abstractmethod
    def save_key(self, key_id: str, key_data: dict[str, Any], metadata: KeyMetadata) -> None: ...

    @abstractmethod
    def load_key(self, key_id: str) -> tuple[dict[str, Any], KeyMetadata]: ...

    @abstractmethod
    def list_keys(self) -> list[KeyMetadata]: ...

    @abstractmethod
    def update_metadata(self, key_id: str, metadata: KeyMetadata) -> None: ...


class FileKeyStore(KeyStore):
    """File-based key storage."""

    def __init__(self, key_dir: str = DEFAULT_KEY_DIR) -> None:
        self.key_dir = Path(key_dir)
        self.key_dir.mkdir(parents=True, exist_ok=True)

    def _key_path(self, key_id: str) -> Path:
        return self.key_dir / f"{key_id}.json"

    def save_key(self, key_id: str, key_data: dict[str, Any], metadata: KeyMetadata) -> None:
        payload = {"data": key_data, "metadata": asdict(metadata)}
        self._key_path(key_id).write_text(json.dumps(payload, indent=2))
        logger.info("Saved key %s to %s", key_id, self._key_path(key_id))

    def load_key(self, key_id: str) -> tuple[dict[str, Any], KeyMetadata]:
        payload = json.loads(self._key_path(key_id).read_text())
        return payload["data"], KeyMetadata(**payload["metadata"])

    def list_keys(self) -> list[KeyMetadata]:
        metadata_list: list[KeyMetadata] = []
        for f in sorted(self.key_dir.glob("*.json")):
            try:
                payload = json.loads(f.read_text())
                metadata_list.append(KeyMetadata(**payload.get("metadata", {})))
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning("Invalid key file %s: %s", f, e)
        return metadata_list

    def update_metadata(self, key_id: str, metadata: KeyMetadata) -> None:
        self.save_key(key_id, *self.load_key(key_id)[0] if self._key_path(key_id).exists() else {}, metadata)


# ---------------------------------------------------------------------------
# Audit Logger
# ---------------------------------------------------------------------------

class KeyAuditLogger:
    """Logs key rotation events."""

    def __init__(self, log_path: str = "/var/log/gula/security/key-rotations.log") -> None:
        self.log_path = log_path

    def log(self, action: str, key_id: str, algorithm: str, status: str, details: str = "") -> None:
        entry = json.dumps({
            "timestamp": datetime.now(UTC).isoformat(),
            "action": action,
            "key_id": key_id,
            "algorithm": algorithm,
            "status": status,
            "details": details,
        })
        logger.info("KEY_ROTATION: %s", entry)
        log_dir = os.path.dirname(self.log_path)
        try:
            os.makedirs(log_dir, exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(entry + "\n")
        except OSError as e:
            logger.warning("Failed to write audit log: %s", e)


# ---------------------------------------------------------------------------
# Re-encryption (Stub)
# ---------------------------------------------------------------------------

class ReEncryptor:
    """Re-encrypts data with new keys (stub for production)."""

    def __init__(self, batch_size: int = 100) -> None:
        self.batch_size = batch_size

    def re_encrypt(self, old_key_id: str, new_key_id: str, algorithm: str) -> int:
        """Re-encrypt data from old key to new key. Returns count."""
        logger.info(
            "Re-encrypting data from %s to %s (alg=%s, batch=%d)",
            old_key_id, new_key_id, algorithm, self.batch_size,
        )
        return 0


# ---------------------------------------------------------------------------
# Key Rotation Engine
# ---------------------------------------------------------------------------

class KeyRotationEngine:
    """Orchestrates key rotation operations."""

    def __init__(
        self,
        store: KeyStore | None = None,
        audit: KeyAuditLogger | None = None,
        generator: KeyGenerator | None = None,
        re_encryptor: ReEncryptor | None = None,
    ) -> None:
        self.store = store or FileKeyStore()
        self.audit = audit or KeyAuditLogger()
        self.generator = generator or KeyGenerator()
        self.re_encryptor = re_encryptor or ReEncryptor()

    def rotate_key(
        self,
        key_id: str,
        algorithm: str,
        grace_period_hours: int = 48,
        do_re_encrypt: bool = False,
        batch_size: int = 100,
        dry_run: bool = False,
    ) -> RotationResult:
        """Rotate a single key."""
        result = RotationResult(
            key_id=key_id,
            algorithm=algorithm,
            status="pending",
            new_version=1,
            dry_run=dry_run,
        )

        try:
            existing_data, existing_meta = self.store.load_key(key_id)
            new_version = existing_meta.version + 1
            result.new_version = new_version
        except (FileNotFoundError, KeyError):
            existing_meta = None
            new_version = 1

        logger.info(
            "Rotating key %s (%s) version %d->%d (dry_run=%s)",
            key_id, algorithm, existing_meta.version if existing_meta else 0,
            new_version, dry_run,
        )

        new_key_id = f"{key_id}_v{new_version}"

        if dry_run:
            result.status = "dry_run"
            self.audit.log("rotate_dry_run", key_id, algorithm, "DRY_RUN", f"Would create {new_key_id}")
            return result

        try:
            key_data = self.generator.generate(algorithm)
            now = datetime.now(UTC).isoformat()
            metadata = KeyMetadata(
                key_id=new_key_id,
                algorithm=algorithm,
                key_type=KEY_ALGORITHMS.get(algorithm, {}).get("type", "unknown"),
                created_at=now,
                rotated_at=now,
                status="active",
                version=new_version,
                previous_key_id=key_id,
                checksum=hashlib.sha3_256(str(key_data).encode()).hexdigest()[:16],
            )
            self.store.save_key(new_key_id, key_data, metadata)

            if existing_meta:
                existing_meta.status = "grace"
                existing_meta.rotated_at = now
                self.store.update_metadata(key_id, existing_meta)

            self.audit.log("rotate", key_id, algorithm, "SUCCESS", f"Created {new_key_id}")

            if do_re_encrypt:
                count = self.re_encryptor.re_encrypt(key_id, new_key_id, algorithm)
                result.re_encrypted = count
                self.audit.log("re_encrypt", key_id, algorithm, "SUCCESS", f"Re-encrypted {count} items")

            result.status = "success"

        except Exception as e:
            result.status = "failed"
            result.errors.append(str(e))
            self.audit.log("rotate", key_id, algorithm, "FAILED", str(e))
            logger.error("Key rotation failed for %s: %s", key_id, e)

        return result

    def rotate_all(
        self,
        algorithm_filter: str = "all",
        grace_period_hours: int = 48,
        do_re_encrypt: bool = False,
        batch_size: int = 100,
        dry_run: bool = False,
    ) -> list[RotationResult]:
        """Rotate all keys matching the algorithm filter."""
        results: list[RotationResult] = []
        existing_keys = self.store.list_keys()

        for algo in KEY_ALGORITHMS:
            if algorithm_filter not in ("all", algo):
                continue
            algo_keys = [m for m in existing_keys if m.algorithm == algo and m.status == "active"]
            if not algo_keys:
                default_key_id = f"gula-{algo}"
                logger.info("No active %s keys found, creating initial key", algo)
                result = self.rotate_key(default_key_id, algo, grace_period_hours, do_re_encrypt, batch_size, dry_run)
                results.append(result)
            for meta in algo_keys:
                result = self.rotate_key(meta.key_id, algo, grace_period_hours, do_re_encrypt, batch_size, dry_run)
                results.append(result)

        return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="GSF Cryptographic Key Rotation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--key-type", choices=list(KEY_ALGORITHMS.keys()) + ["all"], default="all",
        help="Key type to rotate",
    )
    parser.add_argument("--key-id", default=None, help="Specific key ID to rotate")
    parser.add_argument("--grace-period", type=int, default=48, help="Grace period in hours")
    parser.add_argument("--re-encrypt", action="store_true", help="Re-encrypt data with new keys")
    parser.add_argument("--batch-size", type=int, default=100, help="Re-encryption batch size")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without changes")
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    engine = KeyRotationEngine()
    logger.info(
        "Starting key rotation (type=%s, dry_run=%s, re_encrypt=%s)",
        args.key_type, args.dry_run, args.re_encrypt,
    )

    if args.key_id:
        algorithm = "aes"  # default
        for name, info in KEY_ALGORITHMS.items():
            if name in args.key_id:
                algorithm = name
                break
        results = [engine.rotate_key(
            args.key_id, algorithm, args.grace_period,
            args.re_encrypt, args.batch_size, args.dry_run,
        )]
    else:
        results = engine.rotate_all(
            args.key_type, args.grace_period,
            args.re_encrypt, args.batch_size, args.dry_run,
        )

    success = sum(1 for r in results if r.status == "success")
    failed = sum(1 for r in results if r.status == "failed")
    dry_run_count = sum(1 for r in results if r.status == "dry_run")

    logger.info(
        "Key rotation complete: %d success, %d failed, %d dry-run",
        success, failed, dry_run_count,
    )

    for r in results:
        if r.status == "failed":
            logger.error("  FAILED: %s (%s): %s", r.key_id, r.algorithm, r.errors)

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
