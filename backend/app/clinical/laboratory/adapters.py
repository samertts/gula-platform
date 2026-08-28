"""Provider-neutral laboratory adapter boundaries.

Only the synthetic adapter is executable in this repository. ASTM, HL7 v2,
FHIR, and file mappings remain declarative future boundaries and never perform
network I/O or write CoreLabResult rows directly.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol


@dataclass(frozen=True)
class ValidatedAnalyzerMessage:
    message_id: str
    analyzer_id: str
    specimen_id: str
    test_code: str
    payload_hash: str
    occurred_at: datetime
    source: str


class AnalyzerAdapter(Protocol):
    def validate_message(
        self,
        *,
        message_id: str,
        analyzer_id: str,
        specimen_id: str,
        test_code: str,
        payload_hash: str,
        occurred_at: datetime,
        source: str,
    ) -> ValidatedAnalyzerMessage:
        """Validate a bounded message envelope; never persist raw payload."""


class SyntheticAnalyzerAdapter:
    """Deterministic synthetic envelope validator with no external side effects."""

    _HASH_RE = re.compile(r"^[0-9a-fA-F]{64}$")
    _SUPPORTED_SOURCE = "SYNTHETIC"
    _MAX_AGE = timedelta(hours=24)

    def validate_message(
        self,
        *,
        message_id: str,
        analyzer_id: str,
        specimen_id: str,
        test_code: str,
        payload_hash: str,
        occurred_at: datetime,
        source: str,
    ) -> ValidatedAnalyzerMessage:
        if source != self._SUPPORTED_SOURCE:
            raise ValueError("external analyzer adapters are unavailable")
        if not self._HASH_RE.fullmatch(payload_hash):
            raise ValueError("payload_hash must be a SHA-256 hex digest")
        timestamp = occurred_at.replace(tzinfo=UTC) if occurred_at.tzinfo is None else occurred_at.astimezone(UTC)
        now = datetime.now(UTC)
        if timestamp > now or now - timestamp > self._MAX_AGE:
            raise ValueError("analyzer message is outside the accepted time window")
        return ValidatedAnalyzerMessage(
            message_id=message_id,
            analyzer_id=analyzer_id,
            specimen_id=specimen_id,
            test_code=test_code,
            payload_hash=payload_hash.lower(),
            occurred_at=timestamp,
            source=self._SUPPORTED_SOURCE,
        )
