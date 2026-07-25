from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from security.modules.fhir.models import (
    FHIRConsentDirective,
    FHIRSecurityLabel,
    PatientConsent,
    PurposeOfUse,
)

logger = logging.getLogger("gula.security.modules.fhir.consent")

_DEFAULT_PURPOSE_HIERARCHY: dict[str, list[str]] = {
    PurposeOfUse.TREATMENT.value: ["*"],
    PurposeOfUse.PAYMENT.value: [PurposeOfUse.TREATMENT.value],
    PurposeOfUse.OPERATIONS.value: [PurposeOfUse.TREATMENT.value],
    PurposeOfUse.EMERGENCY.value: ["*"],
    PurposeOfUse.DISASTER.value: ["*"],
    PurposeOfUse.BREAK_GLASS.value: ["*"],
    PurposeOfUse.RESEARCH.value: [],
    PurposeOfUse.PUBLIC_HEALTH.value: [PurposeOfUse.TREATMENT.value],
}


class ConsentManager:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._consents: dict[str, PatientConsent] = {}
        self._patient_consents: dict[str, list[str]] = {}
        self._breach_log: list[dict[str, Any]] = []

    def add_consent(
        self,
        patient_id: str,
        scope: FHIRConsentDirective = FHIRConsentDirective.OPT_IN,
        purpose: list[PurposeOfUse] | None = None,
        effective_start: datetime | None = None,
        effective_end: datetime | None = None,
        restrictions: list[str] | None = None,
    ) -> PatientConsent:
        consent = PatientConsent(
            patient_id=patient_id,
            consent_id=str(uuid4()),
            status="active",
            scope=scope,
            purpose=purpose or [],
            effective_start=effective_start or datetime.now(timezone.utc),
            effective_end=effective_end,
            restrictions=restrictions or [],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        with self._lock:
            self._consents[consent.consent_id] = consent
            self._patient_consents.setdefault(patient_id, []).append(consent.consent_id)

        logger.info("Consent added: %s for patient %s", consent.consent_id[:16], patient_id)
        return consent

    def revoke_consent(self, consent_id: str) -> bool:
        with self._lock:
            consent = self._consents.get(consent_id)
            if consent is None:
                return False
            consent.status = "revoked"
            consent.updated_at = datetime.now(timezone.utc)

        logger.info("Consent revoked: %s", consent_id[:16])
        return True

    def get_patient_consents(self, patient_id: str) -> list[PatientConsent]:
        with self._lock:
            consent_ids = self._patient_consents.get(patient_id, [])
            return [self._consents[cid] for cid in consent_ids if cid in self._consents]

    def get_active_consent(self, patient_id: str) -> PatientConsent | None:
        consents = self.get_patient_consents(patient_id)
        now = datetime.now(timezone.utc)

        active = [
            c for c in consents
            if c.status == "active"
            and c.effective_start <= now
            and (c.effective_end is None or c.effective_end > now)
        ]

        if not active:
            return None

        active.sort(key=lambda c: c.effective_start, reverse=True)
        return active[0]

    def check_access(
        self,
        patient_id: str,
        purpose: PurposeOfUse,
        resource_type: str = "",
        sensitivity: FHIRSecurityLabel | None = None,
    ) -> dict[str, Any]:
        consent = self.get_active_consent(patient_id)

        if consent is None:
            return {
                "permitted": True,
                "reason": "No consent on file - access not restricted",
                "enforcement": "permissive",
            }

        scope = consent.scope
        purpose_list = consent.purpose

        if scope == FHIRConsentDirective.NO_CONSENT:
            return {
                "permitted": False,
                "reason": "Patient has no consent on record",
                "enforcement": "denied",
            }

        if scope == FHIRConsentDirective.EMERGENCY_ONLY:
            permitted = purpose in {PurposeOfUse.EMERGENCY, PurposeOfUse.DISASTER, PurposeOfUse.BREAK_GLASS}
            return {
                "permitted": permitted,
                "reason": "Emergency-only consent" if not permitted else "Emergency access permitted",
                "enforcement": "strict",
            }

        if scope == FHIRConsentDirective.RESEARCH_ONLY:
            permitted = purpose == PurposeOfUse.RESEARCH
            return {
                "permitted": permitted,
                "reason": "Research-only consent" if not permitted else "Research access permitted",
                "enforcement": "strict",
            }

        if scope == FHIRConsentDirective.OPT_IN:
            permitted = purpose in purpose_list if purpose_list else True
            if not permitted:
                return {
                    "permitted": False,
                    "reason": f"Purpose '{purpose.value}' not in patient consent",
                    "enforcement": "strict",
                }

        if scope == FHIRConsentDirective.OPT_OUT:
            if purpose in purpose_list:
                return {
                    "permitted": False,
                    "reason": f"Patient opted out for purpose '{purpose.value}'",
                    "enforcement": "strict",
                }

        if sensitivity and consent.restrictions:
            if sensitivity.value in consent.restrictions:
                return {
                    "permitted": False,
                    "reason": f"Data with sensitivity '{sensitivity.value}' is restricted by patient consent",
                    "enforcement": "strict",
                }

        return {
            "permitted": True,
            "reason": f"Access permitted under consent {consent.consent_id[:16]}",
            "enforcement": "permitted",
            "consent_id": consent.consent_id,
        }

    def enforce_purpose_of_use(
        self,
        purpose: PurposeOfUse,
        requested_data: list[str],
        patient_id: str = "",
        sensitivity: FHIRSecurityLabel | None = None,
    ) -> dict[str, Any]:
        access_check = self.check_access(patient_id, purpose, sensitivity=sensitivity) if patient_id else {"permitted": True}
        if not access_check.get("permitted", True):
            return {"permitted": False, "reason": access_check.get("reason", "")}

        hierarchy = _DEFAULT_PURPOSE_HIERARCHY.get(purpose.value, [])
        if "*" not in hierarchy:
            return {
                "permitted": True,
                "reason": f"Purpose '{purpose.value}' permitted with scope limitations",
                "limited_data": requested_data,
            }

        return {
            "permitted": True,
            "reason": f"Full access for purpose '{purpose.value}'",
            "data": requested_data,
        }

    def check_temporal_validity(self, consent_id: str) -> dict[str, Any]:
        with self._lock:
            consent = self._consents.get(consent_id)
        if consent is None:
            return {"valid": False, "reason": "Consent not found"}

        now = datetime.now(timezone.utc)

        if consent.status != "active":
            return {"valid": False, "reason": f"Consent status is '{consent.status}'"}

        if now < consent.effective_start:
            remaining = (consent.effective_start - now).total_seconds()
            return {"valid": False, "reason": "Consent not yet effective", "seconds_until_active": int(remaining)}

        if consent.effective_end and now > consent.effective_end:
            return {"valid": False, "reason": "Consent has expired"}

        return {"valid": True, "reason": "Consent is temporally valid"}

    def log_breach(self, patient_id: str, user_id: str, reason: str) -> None:
        breach = {
            "patient_id": patient_id,
            "user_id": user_id,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "breach_id": str(uuid4()),
        }
        with self._lock:
            self._breach_log.append(breach)
        logger.warning("Consent breach logged: patient=%s user=%s reason=%s", patient_id, user_id, reason)

    def get_consent(self, consent_id: str) -> PatientConsent | None:
        with self._lock:
            return self._consents.get(consent_id)

    def list_consents(self, status: str = "active") -> list[PatientConsent]:
        with self._lock:
            return [c for c in self._consents.values() if c.status == status]

    def list_breaches(self, patient_id: str | None = None) -> list[dict[str, Any]]:
        if patient_id:
            return [b for b in self._breach_log if b["patient_id"] == patient_id]
        return list(self._breach_log)
