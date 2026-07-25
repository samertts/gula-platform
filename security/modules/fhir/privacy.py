from __future__ import annotations

import hashlib
import json
import logging
import re
import secrets
import threading
from base64 import urlsafe_b64encode
from datetime import UTC, datetime
from typing import Any

from security.modules.fhir.models import FHIRSecurityLabel

logger = logging.getLogger("gula.security.modules.fhir.privacy")

_PHI_FIELDS: set[str] = {
    "name", "given_name", "family_name", "middle_name", "maiden_name",
    "ssn", "social_security_number", "national_id", "national_id_number",
    "mrn", "medical_record_number", "patient_id",
    "dob", "date_of_birth", "birth_date",
    "address", "street_address", "city", "state", "zip", "postal_code",
    "phone", "phone_number", "telephone", "mobile", "cell",
    "email", "email_address",
    "insurance_id", "medicaid_id", "medicare_id",
    "driver_license", "license_number",
    "passport_number", "passport",
    "biometric", "fingerprint", "iris_scan", "face_scan",
    "genetic_data", "dna", "genome",
}

_PHI_PATTERNS: list[re.Pattern] = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b\d{9,12}\b"),
    re.compile(r"[A-Z]{2}\d{6}[A-Z]?\d?"),
    re.compile(r"\b\d{3}\s?\d{3}\s?\d{4}\b"),
]

_CLASSIFICATION_SENSITIVITY: dict[str, FHIRSecurityLabel] = {
    "genetic": FHIRSecurityLabel.GENETIC,
    "hiv": FHIRSecurityLabel.HIV,
    "psych": FHIRSecurityLabel.PSYCH,
    "sexual_health": FHIRSecurityLabel.SEXUAL_HEALTH,
    "substance_abuse": FHIRSecurityLabel.SUBSTANCE_ABUSE,
    "demographic": FHIRSecurityLabel.MODERATE,
    "contact": FHIRSecurityLabel.LOW,
    "clinical": FHIRSecurityLabel.MODERATE,
    "financial": FHIRSecurityLabel.MODERATE,
    "research": FHIRSecurityLabel.RESEARCH,
}

_MASK_CHAR = "*"


class PrivacyEngine:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._deid_cache: dict[str, str] = {}
        self._classification_rules: dict[str, FHIRSecurityLabel] = dict(_CLASSIFICATION_SENSITIVITY)

    def classify_phi_field(self, field_name: str) -> bool:
        name_lower = field_name.lower().replace("_", "").replace("-", "")
        return any(phi.replace("_", "") in name_lower for phi in _PHI_FIELDS)

    def detect_phi(self, value: str) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        for pattern in _PHI_PATTERNS:
            matches = pattern.findall(value)
            for match in matches:
                findings.append({
                    "pattern": pattern.pattern,
                    "match": match[:4] + "****",
                    "position": value.index(match) if match in value else -1,
                })
        return findings

    def mask_value(self, value: str, show_first: int = 1, show_last: int = 1, mask_char: str = _MASK_CHAR) -> str:
        if not value:
            return value
        if len(value) <= show_first + show_last:
            return value[0] * len(value)

        return value[:show_first] + mask_char * (len(value) - show_first - show_last) + value[-show_last:]

    def mask_email(self, email: str) -> str:
        parts = email.split("@")
        if len(parts) != 2:
            return self.mask_value(email, show_first=1)
        local = parts[0]
        masked_local = local[0] + _MASK_CHAR * max(len(local) - 1, 1) if local else _MASK_CHAR
        return f"{masked_local}@{parts[1]}"

    def mask_phone(self, phone: str) -> str:
        digits = re.sub(r"\D", "", phone)
        if len(digits) <= 4:
            return phone
        return digits[:2] + _MASK_CHAR * (len(digits) - 4) + digits[-2:]

    def deidentify(
        self,
        data: dict[str, Any],
        fields_to_mask: list[str] | None = None,
        replace_with_hash: bool = False,
        salt: str = "",
    ) -> dict[str, Any]:
        result: dict[str, Any] = {}
        mask_fields = fields_to_mask or [f for f in data if self.classify_phi_field(f)]

        for key, value in data.items():
            if key in mask_fields:
                if replace_with_hash and isinstance(value, str):
                    hash_input = (value + salt).encode() if salt else value.encode()
                    result[key] = hashlib.sha256(hash_input).hexdigest()[:16]
                elif isinstance(value, str):
                    result[key] = self.mask_value(value)
                else:
                    result[key] = _MASK_CHAR * 8
            elif isinstance(value, dict):
                result[key] = self.deidentify(value, fields_to_mask, replace_with_hash, salt)
            elif isinstance(value, list):
                result[key] = [
                    self.deidentify(item, fields_to_mask, replace_with_hash, salt)
                    if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[key] = value

        return result

    def anonymize(
        self,
        data: dict[str, Any],
        irretrievable_fields: list[str] | None = None,
    ) -> dict[str, Any]:
        anon_fields = irretrievable_fields or [f for f in data if self.classify_phi_field(f)]
        result = dict(data)

        for key in anon_fields:
            if key in result:
                result[key] = f"ANON-{hashlib.sha256(str(result[key]).encode()).hexdigest()[:12]}"

        return result

    def assess_reidentification_risk(
        self,
        data: dict[str, Any],
        quasi_identifiers: list[str] | None = None,
    ) -> dict[str, Any]:
        qids = quasi_identifiers or ["dob", "gender", "zip", "city"]
        risk_factors: list[dict[str, Any]] = []
        total_risk = 0.0

        for qid in qids:
            if qid in data and data[qid] is not None:
                uniqueness = self._estimate_uniqueness(qid, str(data[qid]))
                risk_factors.append({
                    "quasi_identifier": qid,
                    "present": True,
                    "uniqueness_estimate": uniqueness,
                    "risk_contribution": round(uniqueness * 0.15, 4),
                })
                total_risk += uniqueness * 0.15

        phi_count = sum(1 for f in _PHI_FIELDS if f in data)
        total_risk += min(phi_count * 0.05, 0.5)

        return {
            "risk_score": round(min(total_risk, 1.0), 4),
            "risk_level": "high" if total_risk > 0.5 else "medium" if total_risk > 0.2 else "low",
            "risk_factors": risk_factors,
            "quasi_identifiers_present": len([r for r in risk_factors if r["present"]]),
            "phi_field_count": phi_count,
            "recommendations": self._get_risk_recommendations(total_risk),
        }

    def determine_minimum_necessary(
        self,
        requested_fields: list[str],
        purpose: str,
    ) -> dict[str, Any]:
        purpose_field_mapping: dict[str, list[str]] = {
            "treatment": ["name", "dob", "gender", "diagnosis", "medications", "allergies", "lab_results"],
            "payment": ["name", "insurance_id", "procedure_codes", "diagnosis_codes", "service_dates"],
            "operations": ["department", "procedure", "provider", "resource_usage"],
            "research": ["diagnosis", "lab_results", "procedures", "outcomes", "demographics"],
            "public_health": ["diagnosis", "demographics", "geography"],
            "emergency": ["name", "dob", "allergies", "medications", "diagnosis", "blood_type"],
        }

        necessary = purpose_field_mapping.get(purpose, [])
        unnecessary = [f for f in requested_fields if f not in necessary]

        return {
            "minimum_fields": necessary,
            "requested_fields": requested_fields,
            "unnecessary_fields": unnecessary,
            "is_minimum": len(unnecessary) == 0,
            "reason": f"Fields {unnecessary} are not necessary for '{purpose}'" if unnecessary else "Request meets minimum necessary standard",
        }

    def classify_sensitivity(self, resource_type: str, data: dict[str, Any]) -> FHIRSecurityLabel:
        for category, label in self._classification_rules.items():
            if category in resource_type.lower():
                return label

        sensitive_content = {"hiv", "aids", "mental", "psychiatric", "genetic", "std", "substance"}
        for key, value in data.items():
            key_lower = key.lower()
            val_lower = str(value).lower()
            combined = f"{key_lower} {val_lower}"
            if any(term in combined for term in sensitive_content):
                return FHIRSecurityLabel.SENSITIVE

        return FHIRSecurityLabel.MODERATE

    def support_right_to_access(self, patient_data: dict[str, Any], format: str = "json") -> dict[str, Any]:
        exported = {
            "exported_at": datetime.now(UTC).isoformat(),
            "data": patient_data,
            "format": format,
            "includes_phi": True,
        }

        if format == "json":
            exported["content"] = json.dumps(patient_data, indent=2, default=str)
        elif format == "fhir":
            exported["content"] = json.dumps({
                "resourceType": "Bundle",
                "type": "collection",
                "entry": [{"resource": patient_data}],
            }, indent=2, default=str)

        return exported

    def support_right_to_delete(
        self,
        patient_data: dict[str, Any],
        fields_to_redact: list[str] | None = None,
    ) -> dict[str, Any]:
        redact = fields_to_redact or [f for f in patient_data if self.classify_phi_field(f)]
        redacted = {k: v for k, v in patient_data.items() if k not in redact}

        return {
            "redacted": True,
            "fields_redacted": redact,
            "remaining_fields": list(redacted.keys()),
            "data": redacted,
            "redacted_at": datetime.now(UTC).isoformat(),
        }

    def generate_portability_package(
        self,
        patient_id: str,
        data: dict[str, Any],
        format: str = "fhir",
    ) -> dict[str, Any]:
        package: dict[str, Any] = {
            "patient_id": patient_id,
            "exported_at": datetime.now(UTC).isoformat(),
            "format": format,
            "data": data,
        }

        if format == "fhir":
            package["content"] = json.dumps({
                "resourceType": "Bundle",
                "type": "export",
                "timestamp": datetime.now(UTC).isoformat(),
                "entry": [{"resource": data}],
            }, indent=2, default=str)
        else:
            package["content"] = json.dumps(data, indent=2, default=str)

        return package

    def hash_national_id(self, national_id: str, salt: str | None = None) -> str:
        s = salt or secrets.token_hex(16)
        hashed = hashlib.pbkdf2_hmac("sha256", national_id.encode(), s.encode(), 100000)
        return f"{s}${urlsafe_b64encode(hashed).rstrip(b'=').decode()}"

    def _estimate_uniqueness(self, field: str, value: str) -> float:
        uniqueness_map: dict[str, float] = {
            "dob": 0.02,
            "gender": 0.5,
            "zip": 0.1,
            "city": 0.3,
            "phone": 0.001,
            "email": 0.0001,
            "name": 0.0005,
            "age": 0.05,
        }
        return uniqueness_map.get(field, 0.2)

    def _get_risk_recommendations(self, risk_score: float) -> list[str]:
        recommendations = []
        if risk_score > 0.5:
            recommendations.append("Apply statistical disclosure control")
            recommendations.append("Suppress quasi-identifiers before release")
            recommendations.append("Obtain data sharing agreement")
        elif risk_score > 0.2:
            recommendations.append("Generalize quasi-identifiers (e.g., age range instead of DOB)")
            recommendations.append("Apply k-anonymity (k >= 5)")
        else:
            recommendations.append("Low risk - standard de-identification sufficient")
        return recommendations



