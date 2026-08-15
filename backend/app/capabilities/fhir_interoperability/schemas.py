"""Typed, minimal FHIR R4 contracts used by GULA's interoperability boundary."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

FHIR_RESOURCE_TYPES = (
    "Patient",
    "Encounter",
    "Observation",
    "DiagnosticReport",
    "Specimen",
    "ServiceRequest",
    "MedicationRequest",
    "Practitioner",
    "Organization",
)


class FHIRResourceInput(BaseModel):
    model_config = ConfigDict(extra="allow")

    resourceType: Literal[
        "Patient",
        "Encounter",
        "Observation",
        "DiagnosticReport",
        "Specimen",
        "ServiceRequest",
        "MedicationRequest",
        "Practitioner",
        "Organization",
    ]
    id: str | None = Field(default=None, min_length=1, max_length=128, pattern=r"^[A-Za-z0-9.-]+$")
    meta: dict[str, Any] | None = None
    subject: dict[str, Any] | None = None
    patient: dict[str, Any] | None = None
    identifier: list[dict[str, Any]] | None = None

    @field_validator("subject", "patient")
    @classmethod
    def validate_reference_shape(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is None:
            return value
        reference = value.get("reference")
        if reference is not None and not isinstance(reference, str):
            raise ValueError("FHIR subject/patient reference must be a string")
        if reference is not None and len(reference) > 255:
            raise ValueError("FHIR subject/patient reference is too long")
        return value


class FHIRResourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    resourceType: str
    id: str
    meta: dict[str, Any] | None = None
    resource: dict[str, Any]
    version: int
    lastUpdated: str


class FHIRResourceListResponse(BaseModel):
    resourceType: Literal["Bundle"] = "Bundle"
    type: Literal["searchset"] = "searchset"
    total: int
    entry: list[FHIRResourceResponse]


class FHIRSearchRequest(BaseModel):
    subject: str | None = Field(default=None, max_length=255)
    patient: str | None = Field(default=None, max_length=255)
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class FHIRCapabilityStatement(BaseModel):
    resourceType: Literal["CapabilityStatement"] = "CapabilityStatement"
    status: Literal["active"] = "active"
    kind: Literal["instance"] = "instance"
    fhirVersion: Literal["4.0.1"] = "4.0.1"
    format: list[str] = ["json"]
    supportedResourceTypes: list[str]
    simulationOnly: bool = True


class HL7ConversionRequest(BaseModel):
    message: str = Field(min_length=16, max_length=200_000)


class HL7ConversionResponse(BaseModel):
    messageType: Literal["ORU^R01"]
    resourceCount: int
    simulationOnly: bool = True
    bundle: dict[str, Any]
