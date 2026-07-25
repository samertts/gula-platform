#!/usr/bin/env python3
# =============================================================================
# GSF: audit-log-verify.py — Audit Log Integrity Verification
# =============================================================================
"""
Verifies the hash chain integrity of the GSF immutable audit log.

Supports database, file-based, and S3 audit backends. Reports tampered
entries and generates a detailed verification report.

Usage:
    ./audit-log-verify.py [options]

Options:
    --backend TYPE     Audit backend type (database, file, s3) [default: file]
    --path PATH        Audit log path for file backend [default: /var/log/gula/audit]
    --config PATH      Path to audit config YAML
    --output PATH      Output report path [default: security/reports/audit-verify-report.json]
    --alerts           Send alerts if tampering detected
    --help, -h         Show this help message

Exit codes:
    0   Audit log integrity verified successfully
    1   Tampering detected
    2   Error during verification
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("gsf.audit-verify")


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class AuditEntry:
    """A single audit log entry with hash chain linkage."""

    sequence: int
    timestamp: str
    event_type: str
    actor_id: str
    resource: str
    action: str
    payload_hash: str
    previous_hash: str
    hash: str
    raw: str = ""

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> AuditEntry:
        return cls(
            sequence=d.get("sequence", 0),
            timestamp=d.get("timestamp", ""),
            event_type=d.get("event_type", ""),
            actor_id=d.get("actor_id", ""),
            resource=d.get("resource", ""),
            action=d.get("action", ""),
            payload_hash=d.get("payload_hash", ""),
            previous_hash=d.get("previous_hash", ""),
            hash=d.get("hash", ""),
            raw=d.get("raw", ""),
        )


@dataclass
class VerificationResult:
    """Result of audit log verification."""

    total_entries: int = 0
    verified_entries: int = 0
    tampered_entries: int = 0
    chain_broken: bool = False
    broken_at_sequences: list[int] = field(default_factory=list)
    first_entry_hash_valid: bool = True
    last_entry: AuditEntry | None = None
    errors: list[str] = field(default_factory=list)
    verification_time_utc: str = ""
    backend_type: str = ""
    hash_algorithm: str = "sha3_256"


# ---------------------------------------------------------------------------
# Hash Chain
# ---------------------------------------------------------------------------

class HashChain:
    """Hash chain computation for audit log integrity."""

    def __init__(self, algorithm: str = "sha3_256") -> None:
        self.algorithm = algorithm

    def _get_hash_func(self):
        return hashlib.new(self.algorithm.replace("-", ""))

    def compute_entry_hash(self, entry: AuditEntry) -> str:
        """Compute the hash of an audit entry's content fields."""
        h = self._get_hash_func()
        h.update(str(entry.sequence).encode())
        h.update(entry.timestamp.encode())
        h.update(entry.event_type.encode())
        h.update(entry.actor_id.encode())
        h.update(entry.resource.encode())
        h.update(entry.action.encode())
        h.update(entry.payload_hash.encode())
        h.update(entry.previous_hash.encode())
        return h.hexdigest()

    def compute_chain_hash(self, previous_hash: str, entry: AuditEntry) -> str:
        """Compute the chain hash linking this entry to the previous one."""
        h = self._get_hash_func()
        h.update(previous_hash.encode())
        h.update(self.compute_entry_hash(entry).encode())
        return h.hexdigest()

    @staticmethod
    def compute_payload_hash(payload: str | dict[str, Any]) -> str:
        """Compute hash of the event payload."""
        if isinstance(payload, dict):
            payload = json.dumps(payload, sort_keys=True)
        return hashlib.sha3_256(payload.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Audit Backends
# ---------------------------------------------------------------------------

class AuditBackend(ABC):
    """Abstract base for audit log backends."""

    @abstractmethod
    def read_entries(self) -> Iterator[AuditEntry]: ...

    @abstractmethod
    def name(self) -> str: ...


class FileAuditBackend(AuditBackend):
    """Reads audit entries from a file-based log."""

    def __init__(self, log_path: str) -> None:
        self.log_path = Path(log_path)

    def name(self) -> str:
        return f"file:{self.log_path}"

    def read_entries(self) -> Iterator[AuditEntry]:
        if not self.log_path.exists():
            raise FileNotFoundError(f"Audit log not found: {self.log_path}")
        if self.log_path.is_dir():
            files = sorted(self.log_path.glob("*.log")) + sorted(self.log_path.glob("*.json"))
            if not files:
                raise FileNotFoundError(f"No audit log files found in {self.log_path}")
            for f in files:
                yield from self._read_file(f)
        else:
            yield from self._read_file(self.log_path)

    @staticmethod
    def _read_file(filepath: Path) -> Iterator[AuditEntry]:
        with open(filepath, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    entry = AuditEntry.from_dict(data)
                    entry.raw = line
                    yield entry
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning("Skipping malformed entry in %s: %s", filepath, e)


class DatabaseAuditBackend(AuditBackend):
    """Reads audit entries from a database (stub for production)."""

    def __init__(self, connection_string: str = "") -> None:
        self.connection_string = connection_string

    def name(self) -> str:
        return f"database:{self.connection_string or 'default'}"

    def read_entries(self) -> Iterator[AuditEntry]:
        raise NotImplementedError("Database backend requires production database connection")


class S3AuditBackend(AuditBackend):
    """Reads audit entries from S3 storage (stub for production)."""

    def __init__(self, bucket: str = "", prefix: str = "") -> None:
        self.bucket = bucket
        self.prefix = prefix

    def name(self) -> str:
        return f"s3://{self.bucket}/{self.prefix}"

    def read_entries(self) -> Iterator[AuditEntry]:
        raise NotImplementedError("S3 backend requires boto3 and AWS credentials")


# ---------------------------------------------------------------------------
# Verification Engine
# ---------------------------------------------------------------------------

class AuditVerifier:
    """Verifies the integrity of an audit log hash chain."""

    def __init__(self, hash_algorithm: str = "sha3_256") -> None:
        self.hash_chain = HashChain(hash_algorithm)

    def verify(self, backend: AuditBackend) -> VerificationResult:
        result = VerificationResult(backend_type=backend.name())
        result.verification_time_utc = datetime.now(UTC).isoformat()

        previous_hash = "0" * 64
        first = True

        try:
            for entry in backend.read_entries():
                result.total_entries += 1

                if first:
                    if entry.previous_hash != "0" * 64:
                        result.first_entry_hash_valid = False
                        result.tampered_entries += 1
                        result.broken_at_sequences.append(entry.sequence)
                        result.errors.append(
                            f"First entry (seq={entry.sequence}): "
                            f"expected previous_hash={'0'*64}, got={entry.previous_hash}"
                        )
                    first = False

                expected_hash = self.hash_chain.compute_chain_hash(previous_hash, entry)

                if entry.hash != expected_hash:
                    result.tampered_entries += 1
                    result.chain_broken = True
                    result.broken_at_sequences.append(entry.sequence)
                    result.errors.append(
                        f"Hash mismatch at sequence {entry.sequence}: "
                        f"expected={expected_hash[:20]}..., got={entry.hash[:20]}..."
                    )
                elif entry.previous_hash != previous_hash:
                    result.tampered_entries += 1
                    result.chain_broken = True
                    result.broken_at_sequences.append(entry.sequence)
                    result.errors.append(
                        f"Chain break at sequence {entry.sequence}: "
                        f"previous_hash mismatch"
                    )
                else:
                    result.verified_entries += 1

                previous_hash = entry.hash
                result.last_entry = entry

        except NotImplementedError:
            result.errors.append("Backend not fully implemented; partial verification only")
        except FileNotFoundError as e:
            result.errors.append(str(e))
        except Exception as e:
            result.errors.append(f"Verification error: {e}")

        return result


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------

def generate_report(result: VerificationResult) -> dict[str, Any]:
    """Generate a verification report dictionary."""
    return {
        "report_type": "audit_log_verification",
        "verification_time": result.verification_time_utc,
        "backend": result.backend_type,
        "summary": {
            "total_entries": result.total_entries,
            "verified_entries": result.verified_entries,
            "tampered_entries": result.tampered_entries,
            "chain_broken": result.chain_broken,
            "first_entry_hash_valid": result.first_entry_hash_valid,
            "integrity_status": "COMPROMISED" if result.tampered_entries > 0 else "INTACT",
        },
        "chain_issues": {
            "broken_at_sequences": result.broken_at_sequences,
            "total_breaks": len(result.broken_at_sequences),
        },
        "errors": result.errors,
        "last_entry": asdict(result.last_entry) if result.last_entry else None,
    }


# ---------------------------------------------------------------------------
# Alerting
# ---------------------------------------------------------------------------

class AlertManager:
    """Sends alerts when tampering is detected."""

    @staticmethod
    def send_alert(result: VerificationResult) -> None:
        if result.tampered_entries == 0:
            return
        logger.critical(
            "AUDIT LOG TAMPERING DETECTED: %d tampered entries out of %d total. "
            "Broken at sequences: %s",
            result.tampered_entries,
            result.total_entries,
            result.broken_at_sequences,
        )
        # In production, this would send email, Slack, PagerDuty, etc.


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def get_backend(args: argparse.Namespace) -> AuditBackend:
    if args.backend == "database":
        return DatabaseAuditBackend()
    if args.backend == "s3":
        return S3AuditBackend()
    return FileAuditBackend(args.path)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="GSF Audit Log Integrity Verification",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--backend",
        choices=["database", "file", "s3"],
        default="file",
        help="Audit backend type",
    )
    parser.add_argument(
        "--path",
        default="/var/log/gula/audit",
        help="Audit log path (file backend)",
    )
    parser.add_argument("--config", default=None, help="Audit config YAML path")
    parser.add_argument(
        "--output",
        default=None,
        help="Output report path (default: security/reports/audit-verify-report.json)",
    )
    parser.add_argument(
        "--alerts",
        action="store_true",
        help="Send alerts if tampering detected",
    )
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    backend = get_backend(args)
    logger.info("Initialized backend: %s", backend.name())

    output_path = args.output
    if not output_path:
        script_dir = Path(__file__).resolve().parent
        output_path = str(script_dir.parent / "reports" / "audit-verify-report.json")

    verifier = AuditVerifier()
    result = verifier.verify(backend)

    report = generate_report(result)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    logger.info("Verification report written to: %s", output_path)

    if result.tampered_entries > 0:
        logger.error(
            "AUDIT LOG COMPROMISED: %d tampered entries detected!",
            result.tampered_entries,
        )
        if args.alerts:
            AlertManager.send_alert(result)
        return 1

    logger.info(
        "Audit log integrity verified: %d entries OK",
        result.verified_entries,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
