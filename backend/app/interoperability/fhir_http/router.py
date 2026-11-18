"""Self-contained FHIR R4 HTTP router for local Phase B / T6 evidence.

CRITICAL: this router is intentionally NOT registered in ``factory.py`` or
``main.py``. It is a local, non-activated HTTP surface. Tests mount it with
``FastAPI()`` + ``app.include_router(router)`` and drive it with ``TestClient``.
It backs every interaction with an in-memory synthetic repository and reuses
the existing Health Core FHIR serializer, deserialiser and OperationOutcome
mapping wherever practical.

All payloads are synthetic. No external endpoint is contacted and no claim of
external interoperability validation is made.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Final

from fastapi import APIRouter, Body, Depends, Header, Query
from fastapi.responses import JSONResponse

from app.health_core.clinical.entities import Observation
from app.health_core.common import HealthCoreError, is_synthetic_id, reject_national_identifier
from app.health_core.fhir.adapter import FhirR4Adapter
from app.health_core.fhir.deserializers import deserialize_resource
from app.health_core.fhir.support import EXT_TENANT, IDENTIFIER_SYSTEM, extension_code
from app.interoperability.fhir_http.capability import build_capability_statement
from app.interoperability.fhir_http.errors import (
    FHIR_JSON_MEDIA_TYPE,
    ErrorBody,
    bad_request,
    conflict,
    error_response,
    error_response_for_health_core_error,
    not_found,
    precondition_required,
    unauthenticated,
)
from app.interoperability.fhir_http.repository import (
    SyntheticFhirRepository,
    VersionedResource,
    get_repository,
)
from app.interoperability.fhir_http.security import (
    EXT_FACILITY,
    Authorization,
    Principal,
    assert_resource_scope,
    authorize_read,
    authorize_write,
)
from app.interoperability.fhir_http.versioning import (
    etag_for,
    etag_matches,
    version_from_meta,
)

__all__ = ["router"]

router = APIRouter(prefix="/fhir", tags=["FHIR R4 - local synthetic evidence"])

_ALLOWED_OBSERVATION_KEYS: Final[frozenset[str]] = frozenset(
    {
        "resourceType",
        "id",
        "meta",
        "identifier",
        "extension",
        "status",
        "category",
        "code",
        "subject",
        "encounter",
        "effectiveDateTime",
        "valueQuantity",
    }
)
_REQUIRED_OBSERVATION_KEYS: Final[tuple[str, ...]] = (
    "id",
    "meta",
    "identifier",
    "status",
    "code",
    "subject",
    "encounter",
    "effectiveDateTime",
    "valueQuantity",
)
_ALLOWED_OBSERVATION_EXTENSIONS: Final[frozenset[str]] = frozenset({EXT_TENANT, EXT_FACILITY})
_DEFAULT_COUNT: Final[int] = 20
_MAX_COUNT: Final[int] = 100


def _guard(auth: Authorization) -> tuple[Principal | None, JSONResponse | None]:
    """Return the authorised principal or a ready-to-return denial response."""
    if auth.error is not None:
        return None, error_response(auth.error)
    if auth.principal is None:
        return None, error_response(unauthenticated())
    return auth.principal, None


def _resource_response(
    resource: dict[str, object],
    *,
    status_code: int = 200,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """Return one FHIR resource with the FHIR JSON media type."""
    return JSONResponse(
        status_code=status_code,
        content=deepcopy(resource),
        headers=headers,
        media_type=FHIR_JSON_MEDIA_TYPE,
    )


def _read(
    resource_type: str,
    resource_id: str,
    principal: Principal,
    repo: SyntheticFhirRepository,
) -> JSONResponse:
    """Return a scoped read response, or a structured 403/404."""
    record = repo.current(resource_type, resource_id)
    if record is None:
        return error_response(not_found())
    denial = assert_resource_scope(principal, record.resource)
    if denial is not None:
        return error_response(denial)
    return _resource_response(
        record.resource, headers={"ETag": etag_for(record.resource)}
    )


def _vread(
    resource_type: str,
    resource_id: str,
    version_id: str,
    principal: Principal,
    repo: SyntheticFhirRepository,
) -> JSONResponse:
    """Return an exact version or a structured 400/404."""
    if not version_id.isdigit() or int(version_id) < 1:
        return error_response(bad_request("Version id must be a positive integer", field="versionId"))
    record = repo.version(resource_type, resource_id, int(version_id))
    if record is None:
        return error_response(not_found())
    denial = assert_resource_scope(principal, record.resource)
    if denial is not None:
        return error_response(denial)
    return _resource_response(
        record.resource, headers={"ETag": etag_for(record.resource)}
    )


def _parse_count(raw: str | None) -> tuple[int | None, ErrorBody | None]:
    """Parse ``_count`` without echoing the supplied value on failure."""
    if raw is None:
        return _DEFAULT_COUNT, None
    candidate = raw.strip()
    if not candidate.isdigit():
        return None, bad_request("_count must be a positive integer", field="_count")
    count = int(candidate)
    if count < 1 or count > _MAX_COUNT:
        return None, bad_request("_count is outside the permitted range", field="_count")
    return count, None


def _validate_observation_payload(payload: object) -> ErrorBody | None:
    """Validate synthetic Observation shape without echoing client values."""
    if not isinstance(payload, dict):
        return bad_request("FHIR payload must be a JSON object", field="resource")

    if payload.get("resourceType") != "Observation":
        return bad_request("resourceType must be Observation", field="resourceType")

    unexpected = set(payload) - _ALLOWED_OBSERVATION_KEYS
    if unexpected:
        # The offending key names are deliberately NOT echoed.
        return bad_request("Observation payload contains an unexpected field", field="payload")

    for key in _REQUIRED_OBSERVATION_KEYS:
        if key not in payload or payload[key] in (None, "", [], {}):
            return bad_request("Observation is missing a required field", field=key)

    meta = payload.get("meta")
    if not isinstance(meta, dict) or version_from_meta(payload) < 1:
        return bad_request("meta.versionId must be a positive integer string", field="meta.versionId")

    identifiers = payload.get("identifier")
    if not isinstance(identifiers, list) or not identifiers:
        return bad_request("identifier must be a non-empty array", field="identifier")
    for item in identifiers:
        if not isinstance(item, dict) or set(item) != {"system", "value"}:
            return bad_request("identifier must carry only system and value", field="identifier")
        if item["system"] != IDENTIFIER_SYSTEM:
            return bad_request("identifier uses an unexpected identifier system", field="identifier")
        value = item["value"]
        if not isinstance(value, str):
            return bad_request("identifier value must be a string", field="identifier")
        try:
            reject_national_identifier(value, field="identifier")
        except HealthCoreError:
            return bad_request("identifier value is not a synthetic reference", field="identifier")
        if not is_synthetic_id(value) or not value.startswith("SYN-OBS-"):
            return bad_request("identifier value is not a synthetic observation", field="identifier")

    extensions = payload.get("extension", [])
    if not isinstance(extensions, list):
        return bad_request("extension must be an array", field="extension")
    for item in extensions:
        if not isinstance(item, dict) or item.get("url") not in _ALLOWED_OBSERVATION_EXTENSIONS:
            return bad_request("Observation carries an unsupported extension", field="extension")
    return None


def _canonical_observation(
    payload: dict[str, object], principal: Principal
) -> JSONResponse | dict[str, object] | None:
    """Deserialise, re-serialise and scope-check an incoming Observation."""
    validation_error = _validate_observation_payload(payload)
    if validation_error is not None:
        return error_response(validation_error)
    try:
        entity = deserialize_resource(payload)
    except HealthCoreError as exc:
        return error_response_for_health_core_error(exc)
    if not isinstance(entity, Observation):
        return error_response(bad_request("resourceType must be Observation", field="resourceType"))

    # Re-serialise through the canonical adapter so unknown client fields never
    # reach storage. Add only the local facility claim to the canonical tenant
    # extension produced by the adapter.
    canonical = FhirR4Adapter().serialize(entity)
    extensions = canonical.get("extension")
    if isinstance(extensions, list):
        extensions.append(extension_code(EXT_FACILITY, principal.facility_id))
    denial = assert_resource_scope(principal, canonical)
    if denial is not None:
        return error_response(denial)
    return canonical


def _write_headers(record: VersionedResource, resource_id: str) -> dict[str, str]:
    """Build Location and ETag headers from a stored version."""
    return {
        "Location": f"/fhir/Observation/{resource_id}/_history/{record.version}",
        "ETag": etag_for(record.resource),
    }


@router.get("/metadata")
def capability_metadata(auth: Authorization = Depends(authorize_read)) -> JSONResponse:
    """Return the FHIR R4 CapabilityStatement for this local evidence surface."""
    _principal, denied = _guard(auth)
    if denied is not None:
        return denied
    return JSONResponse(content=build_capability_statement(), media_type=FHIR_JSON_MEDIA_TYPE)


@router.get("/Patient")
def search_patients(
    identifier: str | None = Query(default=None),
    name: str | None = Query(default=None),
    count: str | None = Query(default=None, alias="_count"),
    auth: Authorization = Depends(authorize_read),
    repo: SyntheticFhirRepository = Depends(get_repository),
) -> JSONResponse:
    """Search synthetic Patients and return a FHIR ``Bundle`` (searchset)."""
    principal, denied = _guard(auth)
    if denied is not None:
        return denied
    assert principal is not None

    limit, count_error = _parse_count(count)
    if count_error is not None or limit is None:
        return error_response(count_error or bad_request("Invalid _count", field="_count"))

    matches = repo.search("Patient", identifier=identifier, name=name, limit=_MAX_COUNT)
    visible = [item for item in matches if assert_resource_scope(principal, item) is None]
    bundle: dict[str, object] = {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(visible),
        "entry": [
            {"fullUrl": f"/fhir/Patient/{item['id']}", "resource": item}
            for item in visible[:limit]
        ],
    }
    return _resource_response(bundle)


@router.get("/Patient/{patient_id}")
def read_patient(
    patient_id: str,
    auth: Authorization = Depends(authorize_read),
    repo: SyntheticFhirRepository = Depends(get_repository),
) -> JSONResponse:
    """Read the current version of one synthetic Patient."""
    principal, denied = _guard(auth)
    if denied is not None:
        return denied
    assert principal is not None
    return _read("Patient", patient_id, principal, repo)


@router.get("/Patient/{patient_id}/_history/{version_id}")
def vread_patient(
    patient_id: str,
    version_id: str,
    auth: Authorization = Depends(authorize_read),
    repo: SyntheticFhirRepository = Depends(get_repository),
) -> JSONResponse:
    """Read one exact historical version of a synthetic Patient."""
    principal, denied = _guard(auth)
    if denied is not None:
        return denied
    assert principal is not None
    return _vread("Patient", patient_id, version_id, principal, repo)


@router.get("/Observation")
def search_observations(
    identifier: str | None = Query(default=None),
    count: str | None = Query(default=None, alias="_count"),
    auth: Authorization = Depends(authorize_read),
    repo: SyntheticFhirRepository = Depends(get_repository),
) -> JSONResponse:
    """Search synthetic Observations and return a FHIR ``Bundle`` (searchset)."""
    principal, denied = _guard(auth)
    if denied is not None:
        return denied
    assert principal is not None

    limit, count_error = _parse_count(count)
    if count_error is not None or limit is None:
        return error_response(count_error or bad_request("Invalid _count", field="_count"))

    matches = repo.search("Observation", identifier=identifier, limit=_MAX_COUNT)
    visible = [item for item in matches if assert_resource_scope(principal, item) is None]
    bundle: dict[str, object] = {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(visible),
        "entry": [
            {"fullUrl": f"/fhir/Observation/{item['id']}", "resource": item}
            for item in visible[:limit]
        ],
    }
    return _resource_response(bundle)


@router.get("/Observation/{observation_id}")
def read_observation(
    observation_id: str,
    auth: Authorization = Depends(authorize_read),
    repo: SyntheticFhirRepository = Depends(get_repository),
) -> JSONResponse:
    """Read the current version of one synthetic Observation."""
    principal, denied = _guard(auth)
    if denied is not None:
        return denied
    assert principal is not None
    return _read("Observation", observation_id, principal, repo)


@router.get("/Observation/{observation_id}/_history/{version_id}")
def vread_observation(
    observation_id: str,
    version_id: str,
    auth: Authorization = Depends(authorize_read),
    repo: SyntheticFhirRepository = Depends(get_repository),
) -> JSONResponse:
    """Read one exact historical version of a synthetic Observation."""
    principal, denied = _guard(auth)
    if denied is not None:
        return denied
    assert principal is not None
    return _vread("Observation", observation_id, version_id, principal, repo)


@router.post("/Observation", status_code=201)
def create_observation(
    payload: object = Body(default=None),
    auth: Authorization = Depends(authorize_write),
    repo: SyntheticFhirRepository = Depends(get_repository),
) -> JSONResponse:
    """Create a new stored version of a synthetic Observation (201 + ETag)."""
    principal, denied = _guard(auth)
    if denied is not None:
        return denied
    assert principal is not None

    if not isinstance(payload, dict):
        return error_response(bad_request("Observation resource must be a JSON object", field="resourceType"))
    canonical_result = _canonical_observation(payload, principal)
    if isinstance(canonical_result, JSONResponse):
        return canonical_result
    if canonical_result is None:
        return error_response(bad_request("Observation could not be normalised", field="resourceType"))

    record = repo.store("Observation", canonical_result)
    return _resource_response(
        record.resource,
        status_code=201,
        headers=_write_headers(record, str(canonical_result.get("id", ""))),
    )


@router.put("/Observation/{observation_id}")
def update_observation(
    observation_id: str,
    payload: object = Body(default=None),
    if_match: str | None = Header(default=None, alias="If-Match"),
    auth: Authorization = Depends(authorize_write),
    repo: SyntheticFhirRepository = Depends(get_repository),
) -> JSONResponse:
    """Conditionally update an Observation using an ``If-Match`` ETag."""
    principal, denied = _guard(auth)
    if denied is not None:
        return denied
    assert principal is not None

    current = repo.current("Observation", observation_id)
    if current is None:
        return error_response(not_found())
    scope_denial = assert_resource_scope(principal, current.resource)
    if scope_denial is not None:
        return error_response(scope_denial)

    if if_match is None or not if_match.strip():
        return error_response(precondition_required())
    if not etag_matches(if_match, current.resource):
        return error_response(conflict())

    if not isinstance(payload, dict) or payload.get("id") != observation_id:
        return error_response(bad_request("Observation id must match the request path", field="id"))

    canonical_result = _canonical_observation(payload, principal)
    if isinstance(canonical_result, JSONResponse):
        return canonical_result
    if canonical_result is None:
        return error_response(bad_request("Observation could not be normalised", field="resourceType"))

    record = repo.store("Observation", canonical_result)
    return _resource_response(
        record.resource,
        status_code=200,
        headers=_write_headers(record, observation_id),
    )
