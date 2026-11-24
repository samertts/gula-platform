"""Stateless, in-process FHIR R4 adapter facade for the synthetic slice.

This is NOT a FastAPI router, endpoint, client or production activation. It is a
pure Python boundary that callers may use in tests or a future owner-authorised
layer; it performs no I/O and never reaches a database, broker or identity
service.
"""

from __future__ import annotations

from app.health_core.common import HealthCoreError
from app.health_core.fhir.deserializers import deserialize_resource
from app.health_core.fhir.errors import operation_outcome_from_error
from app.health_core.fhir.serializers import serialize_entity

__all__ = ["FhirR4Adapter"]


class FhirR4Adapter:
    """Serialise, deserialise and map errors within the synthetic sandbox."""

    def serialize(self, entity: object) -> dict[str, object]:
        """Convert one supported frozen entity into a FHIR R4 resource dict."""
        return serialize_entity(entity)

    def deserialize(self, resource: dict[str, object]) -> object:
        """Convert one supported FHIR R4 resource dict into a frozen entity."""
        return deserialize_resource(resource)

    def round_trip(self, entity: object) -> object:
        """Serialise then deserialise one entity for conformance checking."""
        return self.deserialize(self.serialize(entity))

    def operation_outcome(self, error: HealthCoreError) -> dict[str, object]:
        """Convert one Health Core error into a FHIR R4 OperationOutcome dict."""
        return operation_outcome_from_error(error)
