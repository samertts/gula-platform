"""Explicit identity contract for critical-result events.

GULA stores clinical results in two independent tables:

* ``lab_results`` — the core result API (``app.models.lab_result.LabResult``).
* ``lims_results`` — the national LIMS result store (``app.lims.models.Result``).

Their integer primary keys are unrelated.  A bare ``result_id`` is therefore
ambiguous and can select a different patient's result.  This module makes the
source table mandatory and refuses ambiguous payloads.
"""

from __future__ import annotations

from typing import Any

LAB_RESULT_STORE = "lab_results"
LIMS_RESULT_STORE = "lims_results"
VALID_STORES = frozenset({LAB_RESULT_STORE, LIMS_RESULT_STORE})


class AmbiguousResultReference(ValueError):
    """Raised when a critical-result payload does not identify one result store."""


def critical_result_ref(
    *,
    lab_result_id: int | None = None,
    lims_result_id: int | None = None,
) -> dict[str, Any]:
    """Build the namespaced result reference used in critical-result events."""
    supplied = [value for value in (lab_result_id, lims_result_id) if value is not None]
    if len(supplied) != 1:
        raise AmbiguousResultReference(
            "Exactly one of lab_result_id or lims_result_id must be supplied",
        )

    if lab_result_id is not None:
        if lab_result_id <= 0:
            raise AmbiguousResultReference("lab_result_id must be positive")
        return {"result_store": LAB_RESULT_STORE, "lab_result_id": lab_result_id}

    assert lims_result_id is not None
    if lims_result_id <= 0:
        raise AmbiguousResultReference("lims_result_id must be positive")
    return {"result_store": LIMS_RESULT_STORE, "lims_result_id": lims_result_id}


def extract_critical_result_ref(payload: dict[str, Any]) -> tuple[str, int]:
    """Return ``(store, id)`` or fail closed on ambiguous/legacy payloads."""
    if "result_id" in payload:
        raise AmbiguousResultReference(
            "Bare result_id is ambiguous; use lab_result_id or lims_result_id",
        )

    store = payload.get("result_store")
    if store not in VALID_STORES:
        raise AmbiguousResultReference("result_store must be lab_results or lims_results")

    key = "lab_result_id" if store == LAB_RESULT_STORE else "lims_result_id"
    other_key = "lims_result_id" if store == LAB_RESULT_STORE else "lab_result_id"
    if other_key in payload:
        raise AmbiguousResultReference("Only one result ID namespace may be present")

    result_id = payload.get(key)
    if not isinstance(result_id, int) or isinstance(result_id, bool) or result_id <= 0:
        raise AmbiguousResultReference(f"{key} must be a positive integer")

    return store, result_id
