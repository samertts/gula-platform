"""AUD-API-001 — GET /integration/standards must not deterministically 500.

The auditor found the route read seven attributes that do not exist on the
standards service classes, so every call raised AttributeError before returning.

Falsification axes:
1. Calling the handler returns a well-formed body (no AttributeError).
2. Every reported value is derived from a REAL public accessor — no invented
   conformance data and no new @property aliases added to the service classes.
3. Static guard: the phantom attribute names never reappear in the handler.
"""
from __future__ import annotations

import asyncio
import inspect

from app.integration.routes import standards_conformance
from app.integration.standards import (
    DICOMService,
    FHIRService,
    HL7Service,
    IHEService,
    TerminologyService,
)


def _call() -> dict:
    return asyncio.run(standards_conformance())


class TestStandardsConformance:
    def test_handler_returns_well_formed_body(self):
        body = _call()
        assert set(body) == {"standards"}
        standards = body["standards"]
        assert set(standards) == {"fhir", "hl7", "dicom", "ihe", "terminology"}
        # JSON-serializable (FastAPI must encode it).
        import json

        json.dumps(body)

    def test_values_come_from_real_accessors(self):
        body = _call()["standards"]
        assert body["fhir"]["version"] == FHIRService().version()
        assert body["hl7"]["version"] == HL7Service().version()
        assert body["dicom"]["services"] == sorted(DICOMService().dicom_services())
        assert body["dicom"]["modalities"] == DICOMService().modalities()
        assert body["ihe"]["profiles"] == IHEService().list_profiles()
        assert body["terminology"]["systems"] == TerminologyService().list_systems()

    def test_fhir_interactions_are_derived_from_real_predicate(self):
        fhir = FHIRService()
        reported = _call()["standards"]["fhir"]["interactions"]
        assert reported == [
            name
            for name in ("read", "search", "create", "update", "delete", "history")
            if fhir.supports_interaction(name)
        ]
        assert reported, "the real FHIR service must report at least one interaction"

    def test_no_phantom_attributes_remain_in_handler(self):
        """The exact defect: reading attributes the service classes never define."""
        source = inspect.getsource(standards_conformance)
        forbidden = (
            "fhir_version",
            "capabilities",
            "hl7_version",
            "supported_message_types",
            "supported_sop_classes",
            "supported_profiles",
            "terminology_systems",
        )
        for name in forbidden:
            assert name not in source, f"phantom attribute '{name}' reintroduced"

    def test_service_classes_were_not_given_alias_properties(self):
        """Remediation must use real accessors, not invent attributes to satisfy the route."""
        for cls in (FHIRService, HL7Service, DICOMService, IHEService, TerminologyService):
            for name in ("fhir_version", "capabilities", "hl7_version", "supported_message_types",
                         "supported_sop_classes", "supported_profiles", "terminology_systems"):
                assert not hasattr(cls, name), f"{cls.__name__}.{name} was invented"
