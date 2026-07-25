from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DataClassification(str, Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"
    PHI = "PHI"
    PII = "PII"


class ConsentStatus(str, Enum):
    GRANTED = "GRANTED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"
    NOT_GIVEN = "NOT_GIVEN"


class DataSubjectConsent(BaseModel):
    subject_id: str
    purpose: str
    status: ConsentStatus = ConsentStatus.NOT_GIVEN
    granted_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None


class AnonymizationConfig(BaseModel):
    k_anonymity: int = 5
    l_diversity: int = 3
    generalization_levels: Dict[str, int] = Field(default_factory=dict)


PHI_FIELDS: Set[str] = {
    "ssn", "patient_id", "mrn", "medical_record_number",
    "diagnosis", "treatment", "medication", "prescription",
    "lab_result", "test_result", "procedure", "clinical_note",
    "doctor_notes", "insurance_id", "claim_id", "bill_id",
    "date_of_birth", "dob", "admission_date", "discharge_date",
}

PII_FIELDS: Set[str] = {
    "email", "phone", "phone_number", "mobile", "telephone",
    "address", "street", "city", "state", "zip", "postal_code",
    "full_name", "first_name", "last_name", "middle_name",
    "national_id", "passport", "driver_license", "id_number",
    "ip_address", "mac_address", "device_id", "user_agent",
}

SENSITIVE_FIELDS: Set[str] = PHI_FIELDS | PII_FIELDS | {
    "password", "password_hash", "secret", "token", "api_key",
    "credit_card", "cvv", "bank_account", "routing_number",
    "biometric", "fingerprint", "facial_scan", "iris_scan",
}


class PrivacyEnforcer:
    def __init__(self, anonymization_config: Optional[AnonymizationConfig] = None):
        self.anonymization_config = anonymization_config or AnonymizationConfig()
        self._consent_records: Dict[str, List[DataSubjectConsent]] = {}
        self._classification_rules: Dict[str, DataClassification] = {}
        self._masking_handlers: Dict[str, Callable] = self._register_default_maskers()

    def _register_default_maskers(self) -> Dict[str, Callable]:
        return {
            "email": lambda v: self._mask_email(v),
            "phone": lambda v: self._mask_phone(v),
            "ssn": lambda v: self._mask_ssn(v),
            "credit_card": lambda v: self._mask_credit_card(v),
            "password": lambda v: "********",
            "token": lambda v: v[:4] + "****" + v[-4:] if len(v) > 8 else "********",
            "api_key": lambda v: v[:4] + "****" + v[-4:] if len(v) > 8 else "********",
            "ip_address": lambda v: self._mask_ip(v),
            "date_of_birth": lambda v: v[:4] if v else "",
            "address": lambda v: self._mask_address(v),
            "full_name": lambda v: self._mask_name(v),
            "default": lambda v: v[:2] + "****" + v[-2:] if len(v) > 4 else "****",
        }

    def classify_data(self, field_name: str, value: Any) -> DataClassification:
        field_lower = field_name.lower().replace(" ", "_").replace("-", "_")

        if field_lower in PHI_FIELDS:
            return DataClassification.PHI
        elif field_lower in PII_FIELDS:
            return DataClassification.PII
        elif field_lower in {"password", "password_hash", "secret", "token", "api_key"}:
            return DataClassification.RESTRICTED

        for rule_field, classification in self._classification_rules.items():
            if re.search(rule_field, field_lower, re.IGNORECASE):
                return classification

        if isinstance(value, str):
            if re.match(r"^[\w.+-]+@[\w-]+\.[\w.]+$", value):
                return DataClassification.PII
            if re.match(r"^\d{3}-\d{2}-\d{4}$", value):
                return DataClassification.PHI

        return DataClassification.INTERNAL

    def mask_field(self, field_name: str, value: Any, user_role: str = "anonymous") -> Any:
        if value is None:
            return None

        field_lower = field_name.lower().replace(" ", "_").replace("-", "_")

        if user_role == "admin":
            return value
        if user_role == "practitioner" and field_lower in PHI_FIELDS:
            return value
        if user_role in ("patient", "anonymous") and field_lower in PHI_FIELDS:
            masked = self._get_default_mask(value)
            return masked
        if user_role == "analyst":
            return self.anonymize_field(field_name, value)

        if field_lower in self._masking_handlers:
            return self._masking_handlers[field_lower](value)
        if field_lower in SENSITIVE_FIELDS:
            masked = self._get_default_mask(value)
            return masked

        return value

    def mask_document(self, document: Dict[str, Any], user_role: str = "anonymous",
                       field_classifications: Optional[Dict[str, DataClassification]] = None) -> Dict[str, Any]:
        masked = {}
        for key, value in document.items():
            classification = field_classifications.get(key, self.classify_data(key, value)) if field_classifications else self.classify_data(key, value)

            if isinstance(value, dict):
                masked[key] = self.mask_document(value, user_role, field_classifications)
            elif isinstance(value, list):
                masked[key] = [
                    self.mask_document(item, user_role, field_classifications) if isinstance(item, dict)
                    else self.mask_field(key, item, user_role)
                    for item in value
                ]
            else:
                masked[key] = self.mask_field(key, value, user_role)

        return masked

    def anonymize_field(self, field_name: str, value: Any) -> Any:
        if value is None:
            return None

        field_lower = field_name.lower()
        if field_lower in ("email",):
            return hashlib.sha256(str(value).encode()).hexdigest()[:16] + "@anonymized.invalid"
        elif field_lower in ("phone", "phone_number", "mobile"):
            return hashlib.sha256(str(value).encode()).hexdigest()[:10]
        elif field_lower in ("ssn", "national_id", "passport", "id_number"):
            return hashlib.sha256(str(value).encode()).hexdigest()[:12]
        elif field_lower in ("ip_address",):
            parts = str(value).split(".")
            if len(parts) == 4:
                return f"{parts[0]}.{parts[1]}.xxx.xxx"
            return "xxx.xxx.xxx.xxx"
        elif field_lower in ("full_name", "first_name", "last_name"):
            return f"User-{hashlib.sha256(str(value).encode()).hexdigest()[:8]}"
        elif field_lower in ("date_of_birth", "dob"):
            year = str(value)[:4] if value else ""
            return f"{year}-01-01" if year else "1900-01-01"
        elif field_lower in ("address", "street"):
            return "[REDACTED ADDRESS]"
        elif isinstance(value, str) and len(value) > 4:
            return hashlib.sha256(value.encode()).hexdigest()[:16]

        return "[ANONYMIZED]"

    def anonymize_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        anonymized = {}
        for key, value in document.items():
            if isinstance(value, dict):
                anonymized[key] = self.anonymize_document(value)
            elif isinstance(value, list):
                anonymized[key] = [
                    self.anonymize_document(item) if isinstance(item, dict)
                    else self.anonymize_field(key, item)
                    for item in value
                ]
            else:
                anonymized[key] = self.anonymize_field(key, value)
        return anonymized

    def minimize_fields(self, document: Dict[str, Any], allowed_fields: Set[str]) -> Dict[str, Any]:
        return {k: v for k, v in document.items() if k in allowed_fields}

    def check_consent(self, subject_id: str, purpose: str) -> bool:
        records = self._consent_records.get(subject_id, [])
        for record in records:
            if record.purpose == purpose:
                if record.status == ConsentStatus.GRANTED:
                    if record.expires_at and record.expires_at < datetime.now(timezone.utc):
                        record.status = ConsentStatus.EXPIRED
                        return False
                    return True
                return False
        return False

    def grant_consent(self, subject_id: str, purpose: str,
                       ttl_days: Optional[int] = None) -> DataSubjectConsent:
        consent = DataSubjectConsent(
            subject_id=subject_id,
            purpose=purpose,
            status=ConsentStatus.GRANTED,
            granted_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=ttl_days) if ttl_days else None,
        )

        if subject_id not in self._consent_records:
            self._consent_records[subject_id] = []
        self._consent_records[subject_id].append(consent)
        return consent

    def revoke_consent(self, subject_id: str, purpose: str) -> bool:
        records = self._consent_records.get(subject_id, [])
        for record in records:
            if record.purpose == purpose and record.status == ConsentStatus.GRANTED:
                record.status = ConsentStatus.REVOKED
                record.revoked_at = datetime.now(timezone.utc)
                return True
        return False

    def enforce_storage_limit(self, data: Dict[str, Any], max_age_days: int = 90) -> bool:
        timestamp = data.get("timestamp", data.get("created_at", data.get("date", "")))
        if not timestamp:
            return True

        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except (ValueError, TypeError):
                return True

        if not isinstance(timestamp, datetime):
            return True

        age = (datetime.now(timezone.utc) - timestamp).days
        return age <= max_age_days

    def pseudonymize(self, value: str, salt: str = "gula-pseudonym") -> str:
        return hashlib.sha256(f"{salt}:{value}".encode()).hexdigest()[:24]

    @staticmethod
    def _mask_email(email: str) -> str:
        if "@" not in email:
            return email[:3] + "***"
        local, domain = email.split("@", 1)
        return local[:2] + "***@" + domain

    @staticmethod
    def _mask_phone(phone: str) -> str:
        digits = re.sub(r"\D", "", str(phone))
        if len(digits) >= 10:
            return digits[:3] + "-***-" + digits[-4:]
        return "***-***-****"

    @staticmethod
    def _mask_ssn(ssn: str) -> str:
        digits = re.sub(r"\D", "", str(ssn))
        if len(digits) >= 9:
            return "***-**-" + digits[-4:]
        return "***-**-****"

    @staticmethod
    def _mask_credit_card(cc: str) -> str:
        digits = re.sub(r"\D", "", str(cc))
        if len(digits) >= 16:
            return "****-****-****-" + digits[-4:]
        return "****-****-****-****"

    @staticmethod
    def _mask_ip(ip: str) -> str:
        parts = str(ip).split(".")
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.x.x"
        return "x.x.x.x"

    @staticmethod
    def _mask_address(address: str) -> str:
        if not address:
            return ""
        words = str(address).split()
        if len(words) <= 2:
            return "[REDACTED]"
        return words[0] + " ... [REDACTED]"

    @staticmethod
    def _mask_name(name: str) -> str:
        if not name:
            return ""
        parts = str(name).split()
        if len(parts) == 1:
            return parts[0][0] + "***"
        return parts[0][0] + "*** " + parts[-1][0] + "***"

    @staticmethod
    def _get_default_mask(value: Any) -> str:
        s = str(value)
        if len(s) <= 4:
            return "****"
        return s[:2] + "****" + s[-2:]
