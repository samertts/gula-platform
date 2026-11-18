"""Local, non-activated FHIR R4 HTTP surface for Phase B / T6 evidence.

This package exposes a self-contained FastAPI ``APIRouter`` backed by an
in-memory synthetic repository. It deliberately does NOT register itself on the
application factory or main module: mounting is an explicit test action
(``FastAPI()`` + ``app.include_router(router)``). It is not a FHIR server, is not
production-activated, and does not constitute external interoperability
validation.

The existing ``app.health_core.fhir`` adapter is reused for resource
serialisation, strict synthetic deserialisation and OperationOutcome mapping.
"""

from __future__ import annotations

from app.interoperability.fhir_http.capability import (
    SUPPORTED_INTERACTIONS,
    build_capability_statement,
)
from app.interoperability.fhir_http.errors import FHIR_JSON_MEDIA_TYPE, ErrorBody, error_response
from app.interoperability.fhir_http.repository import (
    SyntheticFhirRepository,
    get_repository,
    reset_repository,
)
from app.interoperability.fhir_http.router import router
from app.interoperability.fhir_http.security import (
    READ_SCOPE,
    WRITE_SCOPE,
    Authorization,
    Principal,
    authorize_read,
    authorize_write,
)
from app.interoperability.fhir_http.versioning import etag_for, etag_matches

__all__ = [
    "FHIR_JSON_MEDIA_TYPE",
    "READ_SCOPE",
    "SUPPORTED_INTERACTIONS",
    "WRITE_SCOPE",
    "Authorization",
    "ErrorBody",
    "Principal",
    "SyntheticFhirRepository",
    "authorize_read",
    "authorize_write",
    "build_capability_statement",
    "error_response",
    "etag_for",
    "etag_matches",
    "get_repository",
    "reset_repository",
    "router",
]
