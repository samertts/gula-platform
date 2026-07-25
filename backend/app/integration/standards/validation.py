from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("gula.integration.standards.validation")


@dataclass
class ValidationResult:
    valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, error: str) -> None:
        self.valid = False
        self.errors.append(error)

    def add_warning(self, warning: str) -> None:
        self.warnings.append(warning)

    def merge(self, other: ValidationResult) -> None:
        if not other.valid:
            self.valid = False
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)


class ValidationService:
    def __init__(self):
        self._validators: dict[str, Any] = {}

    def register_validator(self, name: str, validator: Any) -> None:
        self._validators[name] = validator
        logger.info("Validator registered: %s", name)

    def validate_fhir(self, resource: dict[str, Any]) -> ValidationResult:
        result = ValidationResult()
        if "resourceType" not in resource:
            result.add_error("FHIR resource must have resourceType")
        if "id" not in resource:
            result.add_warning("FHIR resource without id")
        return result

    def validate_hl7(self, message: str) -> ValidationResult:
        result = ValidationResult()
        if not message:
            result.add_error("HL7 message is empty")
            return result
        if not message.startswith("MSH"):
            result.add_error("HL7 message must start with MSH segment")
        segments = message.split("\r")
        for seg in segments:
            if seg and "|" not in seg:
                result.add_warning(f"Segment missing field separator: {seg}")
        return result

    def validate_national_id(self, national_id: str) -> ValidationResult:
        result = ValidationResult()
        if not national_id:
            result.add_error("National ID is required")
            return result
        if not re.match(r"^\d{14,16}$", national_id):
            result.add_error("National ID must be 14-16 digits")
        return result

    def validate_phone(self, phone: str) -> ValidationResult:
        result = ValidationResult()
        if not phone:
            result.add_error("Phone is required")
            return result
        cleaned = re.sub(r"[\s\-()+]", "", phone)
        if not cleaned.startswith("964") and not cleaned.startswith("0"):
            result.add_error("Iraqi phone must start with 964 or 0")
        if len(cleaned.replace("964", "").replace("0", "", 1)) not in (10, 11):
            result.add_warning("Phone number length seems unusual")
        return result

    def validate_email(self, email: str) -> ValidationResult:
        result = ValidationResult()
        if not email:
            result.add_error("Email is required")
            return result
        if "@" not in email or "." not in email.rsplit("@", maxsplit=1)[-1]:
            result.add_error("Invalid email format")
        return result

    def validate_required_fields(
        self, data: dict[str, Any], required: list[str]
    ) -> ValidationResult:
        result = ValidationResult()
        for field_name in required:
            if field_name not in data or data[field_name] is None or data[field_name] == "":
                result.add_error(f"Required field '{field_name}' is missing")
        return result

    def validate_range(
        self, value: float, field_name: str, low: float | None = None, high: float | None = None
    ) -> ValidationResult:
        result = ValidationResult()
        if low is not None and value < low:
            result.add_error(f"{field_name} ({value}) is below minimum ({low})")
        if high is not None and value > high:
            result.add_error(f"{field_name} ({value}) is above maximum ({high})")
        return result

    def validate_length(self, value: str, field_name: str, max_length: int) -> ValidationResult:
        result = ValidationResult()
        if len(value) > max_length:
            result.add_error(f"{field_name} exceeds maximum length of {max_length}")
        return result
