"""In-memory synthetic repository for the T6 HTTP evidence surface.

Stores immutable, versioned FHIR R4 resource snapshots. Every resource is
synthetic (``SYN-`` prefixed) and is scoped to a synthetic tenant and facility.
Nothing is persisted, no database or broker is contacted, and the repository is
resettable so tests are deterministic.

Observation snapshots are produced by the existing Health Core FHIR serializer
rather than by a second, divergent mapping.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Final

from app.health_core.clinical.entities import Observation
from app.health_core.fhir.adapter import FhirR4Adapter
from app.health_core.fhir.support import (
    EXT_TENANT,
    extension_code,
    make_identifier,
    profile_for,
)
from app.interoperability.fhir_http.security import EXT_FACILITY

__all__ = [
    "FACILITY_A",
    "FACILITY_B",
    "TENANT_A",
    "TENANT_B",
    "SyntheticFhirRepository",
    "VersionedResource",
    "get_repository",
    "reset_repository",
]

TENANT_A: Final[str] = "SYN-TEN-0001"
FACILITY_A: Final[str] = "SYN-FAC-0001"
TENANT_B: Final[str] = "SYN-TEN-0002"
FACILITY_B: Final[str] = "SYN-FAC-0002"

_PATIENT_IDS_A: Final[tuple[str, ...]] = (
    "SYN-PAT-0001",
    "SYN-PAT-0002",
    "SYN-PAT-0003",
    "SYN-PAT-0004",
    "SYN-PAT-0005",
)
_PATIENT_ID_B: Final[str] = "SYN-PAT-0006"
_ENCOUNTER_ID: Final[str] = "SYN-ENC-0001"
_RECORDED_AT: Final[str] = "2026-01-01T00:00:00Z"
_LOINC_HEART_RATE: Final[str] = "8867-4"


@dataclass(frozen=True, slots=True)
class VersionedResource:
    """One immutable version of a stored synthetic resource."""

    version: int
    resource: dict[str, object]


def _scoped_extensions(tenant_id: str, facility_id: str) -> list[dict[str, object]]:
    """Return the canonical tenant extension plus this surface's facility claim."""
    return [
        extension_code(EXT_TENANT, tenant_id),
        extension_code(EXT_FACILITY, facility_id),
    ]


def _patient_resource(patient_id: str, tenant_id: str, facility_id: str, label: str) -> dict[str, object]:
    """Build a minimal, valid synthetic FHIR R4 Patient resource."""
    return {
        "resourceType": "Patient",
        "id": patient_id,
        "meta": {"profile": [profile_for("Patient")], "versionId": "1"},
        "identifier": [make_identifier(patient_id, field="identifier", expected_prefix="SYN-PAT-")],
        "name": [{"use": "official", "text": label, "family": label.split()[-1], "given": ["Synthetic"]}],
        "gender": "unknown",
        "active": True,
        "extension": _scoped_extensions(tenant_id, facility_id),
    }


def _observation_resource(
    observation_id: str,
    *,
    tenant_id: str,
    facility_id: str,
    patient_id: str,
    value: float,
) -> dict[str, object]:
    """Reuse the canonical Health Core serializer for synthetic observations."""
    entity = Observation(
        observation_id=observation_id,
        tenant_id=tenant_id,
        patient_ref=patient_id,
        encounter_id=_ENCOUNTER_ID,
        code=_LOINC_HEART_RATE,
        display="Synthetic heart rate",
        value=value,
        unit="bpm",
        recorded_at=_RECORDED_AT,
    )
    resource = FhirR4Adapter().serialize(entity)
    extensions = resource.get("extension")
    if isinstance(extensions, list):
        extensions.extend(_scoped_extensions(tenant_id, facility_id))
    return resource


class SyntheticFhirRepository:
    """Versioned, tenant-scoped in-memory store of synthetic FHIR resources."""

    def __init__(self) -> None:
        self._store: dict[tuple[str, str], list[VersionedResource]] = {}
        self.reset()

    def reset(self) -> None:
        """Restore the deterministic synthetic seed (used between tests)."""
        self._store.clear()

        for index, patient_id in enumerate(_PATIENT_IDS_A, start=1):
            resource = _patient_resource(
                patient_id, TENANT_A, FACILITY_A, f"Synthetic Patient {index}"
            )
            self.store("Patient", resource)
        # A second stored version proves vread returns the exact historical snapshot.
        second = _patient_resource(_PATIENT_IDS_A[0], TENANT_A, FACILITY_A, "Synthetic Patient One")
        second["active"] = False
        self.store("Patient", second)

        cross_tenant = _patient_resource(
            _PATIENT_ID_B, TENANT_B, FACILITY_B, "Synthetic Patient Other"
        )
        self.store("Patient", cross_tenant)

        for observation_id, value in (("SYN-OBS-0001", 72.0), ("SYN-OBS-0002", 68.0)):
            self.store(
                "Observation",
                _observation_resource(
                    observation_id,
                    tenant_id=TENANT_A,
                    facility_id=FACILITY_A,
                    patient_id=_PATIENT_IDS_A[0],
                    value=value,
                ),
            )
        # Version 2 of SYN-OBS-0001, so vread and conditional update have history.
        self.store(
            "Observation",
            _observation_resource(
                "SYN-OBS-0001",
                tenant_id=TENANT_A,
                facility_id=FACILITY_A,
                patient_id=_PATIENT_IDS_A[0],
                value=80.0,
            ),
        )
        self.store(
            "Observation",
            _observation_resource(
                "SYN-OBS-0003",
                tenant_id=TENANT_B,
                facility_id=FACILITY_B,
                patient_id=_PATIENT_ID_B,
                value=90.0,
            ),
        )

    def next_version(self, resource_type: str, resource_id: str) -> int:
        """Return the version number the next stored snapshot will receive."""
        return len(self._store.get((resource_type, resource_id), [])) + 1

    def current(self, resource_type: str, resource_id: str) -> VersionedResource | None:
        """Return the current version of one resource, or ``None``."""
        versions = self._store.get((resource_type, resource_id), [])
        return versions[-1] if versions else None

    def version(self, resource_type: str, resource_id: str, version: int) -> VersionedResource | None:
        """Return one exact historical version, or ``None``."""
        for record in self._store.get((resource_type, resource_id), []):
            if record.version == version:
                return record
        return None

    def store(self, resource_type: str, resource: dict[str, object]) -> VersionedResource:
        """Store a new immutable version and assign ``meta.versionId`` server-side."""
        stored = deepcopy(resource)
        resource_id = stored.get("id")
        if not isinstance(resource_id, str) or not resource_id:
            msg = "stored resources must carry a synthetic id"
            raise ValueError(msg)
        meta = stored.get("meta")
        if not isinstance(meta, dict):
            meta = {}
            stored["meta"] = meta
        version = self.next_version(resource_type, resource_id)
        meta["versionId"] = str(version)
        record = VersionedResource(version=version, resource=stored)
        self._store.setdefault((resource_type, resource_id), []).append(record)
        return record

    def search(
        self,
        resource_type: str,
        *,
        identifier: str | None = None,
        name: str | None = None,
        limit: int,
    ) -> list[dict[str, object]]:
        """Return current resources matching a synthetic query, capped by ``limit``."""
        matches: list[dict[str, object]] = []
        for (stored_type, _), versions in self._store.items():
            if stored_type != resource_type or not versions:
                continue
            resource = versions[-1].resource
            if identifier is not None and not self._identifier_matches(resource, identifier):
                continue
            if name is not None and not self._name_matches(resource, name):
                continue
            matches.append(deepcopy(resource))
        return matches[:limit]

    @staticmethod
    def _identifier_matches(resource: dict[str, object], query: str) -> bool:
        """Match an exact synthetic identifier value without echoing the query."""
        identifiers = resource.get("identifier")
        if not isinstance(identifiers, list):
            return False
        return any(
            isinstance(item, dict) and item.get("value") == query for item in identifiers
        )

    @staticmethod
    def _name_matches(resource: dict[str, object], query: str) -> bool:
        """Case-insensitive substring match over synthetic HumanName text."""
        names = resource.get("name")
        if not isinstance(names, list) or not query:
            return False
        needle = query.casefold()
        return any(
            isinstance(value, str) and needle in value.casefold()
            for item in names
            if isinstance(item, dict)
            for value in (item.get("text"), item.get("family"), *item.get("given", []))
        )


_REPOSITORY: Final[SyntheticFhirRepository] = SyntheticFhirRepository()


def get_repository() -> SyntheticFhirRepository:
    """Return the shared in-memory repository used by the local router."""
    return _REPOSITORY


def reset_repository() -> None:
    """Restore the shared repository to its deterministic synthetic seed."""
    _REPOSITORY.reset()
