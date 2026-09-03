from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class ImagingAdapterError(Exception):
    """Base adapter failure; transport failures never mutate canonical state."""


class ImagingAdapterUnavailable(ImagingAdapterError):
    pass


class ImagingAdapter(Protocol):
    name: str

    def retrieve_metadata(self, *, source_message_id: str, study_instance_uid: str) -> dict[str, str | int]:
        ...


@dataclass(frozen=True)
class SyntheticImagingAdapter:
    """Test-only metadata adapter; it returns no binary and performs no network I/O."""

    name: str = "SYNTHETIC_ADAPTER"

    def retrieve_metadata(self, *, source_message_id: str, study_instance_uid: str) -> dict[str, str | int]:
        if not source_message_id.strip() or not study_instance_uid.strip():
            raise ImagingAdapterError("DICOM metadata identifiers are required")
        return {
            "source_message_id": source_message_id,
            "study_instance_uid": study_instance_uid,
            "adapter": self.name,
        }


class DicomAdapterInterface(Protocol):
    """Boundary for future DICOMweb/C-STORE adapters; no implementation is enabled here."""

    name: str

    def ingest_metadata(self, payload: dict[str, object]) -> dict[str, object]:
        ...


class PacsAdapterInterface(Protocol):
    """Boundary for PACS retrieve; callers must translate failures to typed errors."""

    name: str

    def retrieve(self, *, study_instance_uid: str, series_instance_uid: str | None = None) -> dict[str, object]:
        ...


class RisAdapterInterface(Protocol):
    """Boundary for optional RIS synchronization; canonical rows remain authoritative."""

    name: str

    def publish_order(self, payload: dict[str, object]) -> None:
        ...
