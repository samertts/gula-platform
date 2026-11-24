"""Forward-looking integration contracts. DECLARATION ONLY.

These protocols document the shape that a future, separately authorised MPI
adapter or analyzer gateway would have to satisfy. They are intentionally:

* not implemented anywhere in this program;
* not imported or called by the synthetic workflow services; and
* free of any database, network or real-identity dependency.

Keeping the contracts here (rather than in production modules) makes the seam
explicit without activating any production integration.
"""

from __future__ import annotations

from typing import Protocol

from app.health_core.identity.port import PatientRef


class FuturePatientLookup(Protocol):
    """A future read-only patient lookup seam. Never used in this program."""

    def lookup_patient(self, *, reference: str) -> PatientRef | None:
        """Return a patient reference for a previously approved external key."""
        ...


class FutureAnalyzerGateway(Protocol):
    """A future analyzer gateway seam. There is no implementation or connection."""

    def submit_test(self, *, test_code: str, specimen_barcode: str) -> str:
        """Return an opaque external run identifier for a submitted test."""
        ...

    def fetch_run_status(self, *, run_id: str) -> str:
        """Return an opaque external status token for a submitted run."""
        ...


class FutureResultPublisher(Protocol):
    """A future outbound publish seam for verified results. Never called here."""

    def publish_result(self, *, result_reference: str) -> None:
        """Publish an already verified synthetic result reference."""
        ...
