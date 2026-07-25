"""Standardized validation module — JSON Schema and FHIR R4 resource validation."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from . import PlatformRegistry

logger = logging.getLogger("gula.platform.validation")


@dataclass
class ValidationResult:
    valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class ValidationService:
    def validate(self, data: Any, schema: dict) -> ValidationResult:
        import jsonschema

        try:
            jsonschema.validate(instance=data, schema=schema)
            return ValidationResult(valid=True)
        except jsonschema.exceptions.ValidationError as e:
            return ValidationResult(valid=False, errors=[e.message])

    def validate_model(self, model_name: str, data: dict) -> ValidationResult:
        from ..national.fhir.validation import FHIRValidationEngine

        engine = FHIRValidationEngine()
        result = engine.validate(data)
        return ValidationResult(valid=result.valid, errors=result.errors, warnings=result.warnings)

    def validate_fhir(self, resource: dict) -> ValidationResult:
        from ..national.fhir.validation import FHIRValidationEngine

        engine = FHIRValidationEngine()
        result = engine.validate(resource)
        return ValidationResult(valid=result.valid, errors=result.errors, warnings=result.warnings)


PlatformRegistry.register(
    "validation",
    ValidationService(),
    capabilities=[
        {"name": "validate", "description": "Validate data against a JSON Schema"},
        {"name": "validate_model", "description": "Validate a model against its schema"},
        {"name": "validate_fhir", "description": "Validate a FHIR R4 resource"},
    ],
)
