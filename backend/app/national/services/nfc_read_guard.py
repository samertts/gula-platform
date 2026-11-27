"""Synthetic NFC read-session guard for Route A.

The guard binds an NFC read to a completed live-capture session, requires
explicit synthetic consent, rejects replay and session hijack attempts, and
reports malformed or inconsistent reads as review-only evidence. It never reads
a chip, handles keys, or asserts chip authenticity.
"""

from __future__ import annotations

import hashlib
import json
import re
import threading
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from app.national.services.document_authenticity import (
    LiveCaptureSession,
    NfcState,
)
from app.national.services.document_extraction import NfcCardReference
from app.national.services.identity_access import (
    NFC_EXTRACTION,
    build_wave053_audit_event,
)

PIPELINE_VERSION = "phase1-synthetic-nfc-guard-v1"
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_REFERENCE = re.compile(r"^[A-Za-z0-9._:\-/]{1,200}$")


class NfcReadGuardError(ValueError):
    """Raised when a synthetic NFC read violates its session contract."""


@dataclass(frozen=True)
class NfcReadRequest:
    session: LiveCaptureSession
    card: NfcCardReference
    actor_id: str
    organization_id: str
    facility_id: str
    purpose: str
    correlation_id: str
    consent_reference: str
    evidence_reference: str
    state: NfcState
    read_at: datetime
    field_digests: Mapping[str, str]

    def __post_init__(self) -> None:
        if not isinstance(self.session, LiveCaptureSession):
            raise NfcReadGuardError("a completed live-capture session is required")
        if not isinstance(self.card, NfcCardReference):
            raise NfcReadGuardError("an opaque synthetic NFC card reference is required")
        for label, value in (
            ("actor", self.actor_id),
            ("organization", self.organization_id),
            ("facility", self.facility_id),
            ("purpose", self.purpose),
            ("correlation id", self.correlation_id),
            ("consent reference", self.consent_reference),
            ("evidence reference", self.evidence_reference),
        ):
            if not value or not value.strip():
                raise NfcReadGuardError(f"{label} is required")
            if _REFERENCE.fullmatch(value) is None:
                raise NfcReadGuardError(f"{label} must be an opaque reference")
        # Consent is not a free-form token: it must name the exact session and
        # correlation it authorizes, so a consent from another read cannot be
        # replayed against this one.
        expected_consent = f"CONSENT:{self.session.challenge.session_id}:{self.correlation_id}"
        if self.consent_reference != expected_consent:
            raise NfcReadGuardError("consent must be bound to the capture session and correlation")
        if self.read_at.tzinfo is None:
            raise NfcReadGuardError("NFC read timestamp must be timezone aware")
        for field_name, digest in self.field_digests.items():
            if not field_name or _REFERENCE.fullmatch(field_name) is None:
                raise NfcReadGuardError("field names must be opaque")
            if _DIGEST.fullmatch(digest) is None:
                raise NfcReadGuardError("field digests must be 64-character hex values")


@dataclass(frozen=True)
class NfcReadEvidence:
    pipeline_version: str
    session_id: str
    correlation_id: str
    evidence_reference: str
    state: NfcState
    chip_authenticity_verified: bool
    requires_review: bool
    reasons: tuple[str, ...]
    field_names: tuple[str, ...]
    audit_event: Any

    def __post_init__(self) -> None:
        if self.chip_authenticity_verified is not False:
            raise NfcReadGuardError("NFC reads never establish chip authenticity")

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "pipeline_version": self.pipeline_version,
            "state": self.state.value,
            "chip_authenticity_verified": self.chip_authenticity_verified,
            "requires_review": self.requires_review,
            "reasons": self.reasons,
            "field_names": sorted(self.field_names),
        }


class NfcReadGuard:
    """In-process replay/session-binding guard; durable storage is not approved."""

    def __init__(self, *, max_read_window: timedelta = timedelta(minutes=15)) -> None:
        self._max_read_window = max_read_window
        self._seen: dict[str, str] = {}
        self._lock = threading.Lock()

    @staticmethod
    def fingerprint(request: NfcReadRequest) -> str:
        payload = {
            "actor_id": request.actor_id,
            "card_reference": request.card.card_reference,
            "consent_reference": request.consent_reference,
            "correlation_id": request.correlation_id,
            "evidence_reference": request.evidence_reference,
            "field_digests": dict(sorted(request.field_digests.items())),
            "reader_reference": request.card.reader_reference,
            "session_id": request.session.challenge.session_id,
            "state": request.state.value,
        }
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def authorize(
        self,
        request: NfcReadRequest,
        *,
        national_id_hash: str,
        gula_citizen_identifier: str,
        ocr_field_digests: Mapping[str, str] | None = None,
    ) -> NfcReadEvidence:
        challenge = request.session.challenge
        for label, expected, actual in (
            ("actor", challenge.actor_id, request.actor_id),
            ("organization", challenge.organization_id, request.organization_id),
            ("facility", challenge.facility_id, request.facility_id),
            ("purpose", challenge.purpose, request.purpose),
            ("correlation id", challenge.correlation_id, request.correlation_id),
        ):
            if expected != actual:
                raise NfcReadGuardError(f"NFC read {label} does not match its capture session")
        if not challenge.device_capabilities.nfc_supported:
            raise NfcReadGuardError("NFC path requires an NFC-capable device")
        if request.read_at < challenge.issued_at:
            raise NfcReadGuardError("NFC read cannot precede its capture challenge")
        if request.read_at > challenge.issued_at + self._max_read_window:
            raise NfcReadGuardError("NFC read is outside the synthetic capture window")

        fingerprint = self.fingerprint(request)
        with self._lock:
            existing = self._seen.get(challenge.session_id)
            if existing is not None and existing != fingerprint:
                raise NfcReadGuardError("NFC session replay or hijack attempt is rejected")
            if existing is None:
                self._seen[challenge.session_id] = fingerprint
            elif existing == fingerprint:
                raise NfcReadGuardError("NFC read replay is rejected")

        reasons: list[str] = []
        if request.state is not NfcState.NFC_READ_SUCCESSFULLY:
            reasons.append(f"NFC state is {request.state.value}")
        for field_name, digest in sorted((ocr_field_digests or {}).items()):
            observed = request.field_digests.get(field_name)
            if observed is None:
                reasons.append(f"missing NFC field: {field_name}")
            elif observed != digest:
                reasons.append(f"inconsistent NFC field: {field_name}")
        reasons.append("chip authenticity remains unverified")

        audit_event = build_wave053_audit_event(
            operation=NFC_EXTRACTION,
            actor_id=request.actor_id,
            purpose=request.purpose,
            facility_id=request.facility_id,
            organization_id=request.organization_id,
            gula_citizen_identifier=gula_citizen_identifier,
            national_id_hash=national_id_hash,
            metadata={
                "session_id": challenge.session_id,
                "state": request.state.value,
                "requires_review": True,
                "field_names": tuple(sorted(request.field_digests)),
                "consent_reference": request.consent_reference,
            },
            correlation_id=request.correlation_id,
            raw_nid_values=(request.consent_reference, request.evidence_reference),
        )
        return NfcReadEvidence(
            pipeline_version=PIPELINE_VERSION,
            session_id=challenge.session_id,
            correlation_id=request.correlation_id,
            evidence_reference=request.evidence_reference,
            state=request.state,
            chip_authenticity_verified=False,
            requires_review=True,
            reasons=tuple(reasons),
            field_names=tuple(sorted(request.field_digests)),
            audit_event=audit_event,
        )


__all__ = [
    "PIPELINE_VERSION",
    "NfcReadEvidence",
    "NfcReadGuard",
    "NfcReadGuardError",
    "NfcReadRequest",
]
