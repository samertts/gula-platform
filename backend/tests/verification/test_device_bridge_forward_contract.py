"""The device bridge posts a payload the endpoint it posts to cannot accept.

IA-041 (P1, NEEDS_DECISION). `services/device_bridge` is the unit that reads
physical analyzers (Sysmex, Roche, Mindray) and forwards results into GULA. Its
only outbound path is `GulaClient.send_results`, which POSTs to
`{base_url}/device/results` -- this module's `receive_device_results`.

The two sides do not agree, and the disagreement is total. Measured against the
real Pydantic models in this file:

    bridge sends     : {"lab_id", "results": [{"patient_id", "test_code",
                                               "value", "unit", "timestamp"}]}
    endpoint requires: {"barcode", "results": [{"test_name", ...}]}
    validation       : REJECTED
                         missing ('barcode',)             Field required
                         missing ('results', 0, 'test_name') Field required

Four independent reasons the forward cannot succeed, each sufficient on its own:

  1. `barcode` is required and never sent. The endpoint matches results to an
     order *through the sample barcode*; the bridge sends a `patient_id` instead,
     which this endpoint has no field for.
  2. `test_name` is required; the bridge sends `test_code`.
  3. `receive_device_results` depends on `get_current_user`, and `GulaClient`
     sets no Authorization header at all -- so the request is 401 before the body
     is read.
  4. The base URL was hardcoded to `http://gula.local` while docker-compose
     deploys the backend as `gula-backend:8000`. That one is fixed (the bridge now
     reads the documented GULA_BACKEND_URL); the other three are not.

`GulaClient` catches every exception and returns `{"status": "failed"}`, so none
of this surfaces: `/ingest` answers HTTP 200 `{"status": "ok", "processed": 1}`
and the result goes to the bridge's retry queue. As of this commit the bridge
also records a `forward_failed` log row, so the failure is at least visible
there -- but the result is still in the bridge and not in the patient record.

Why this is recorded rather than fixed: closing it means authoring an integration
contract, not correcting a mistake. It requires deciding how a service
authenticates to GULA (no service credential exists for the bridge), how an ASTM
message reaches a sample barcode (the bridge accepts a `barcode` on /ingest and
drops it before the forward), and how a vendor `test_code` maps to a catalog
`test_name` -- which is clinical semantics and must not be guessed. Those are
decisions for the platform owner.

The strict xfails below are the encoding of that: they pass while the divergence
exists and fail the moment it is closed, so whoever closes it is told to come
back and delete them rather than leaving a stale test behind.
"""
from __future__ import annotations

import datetime
import inspect

import pytest
from app.routes.device_results import (
    DeviceResult,
    DeviceSubmission,
    receive_device_results,
)
from pydantic import ValidationError

from tests.conftest import auth_headers


def _bridge_payload() -> dict:
    """The exact body `GulaClient.send_results` builds.

    Transcribed from services/device_bridge/app/integration/gula_client.py; the
    source-level guard below keeps this copy honest.
    """
    return {
        "lab_id": "LAB001",
        "results": [
            {
                "patient_id": "12345",
                "test_code": "HEMOGLOBIN",
                "value": 13.5,
                "unit": "g/dL",
                "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            },
        ],
    }


# ── what the endpoint actually requires ──────────────────────────────────────


def test_the_endpoint_requires_a_barcode_and_a_test_name():
    """Pinned so the divergence cannot be "fixed" by loosening this side.

    `barcode` is how a result reaches an order, and `test_name` is how it reaches
    a catalog entry. Making either optional would not reconcile the contract, it
    would let an unattributable result through.
    """
    required = {k for k, f in DeviceSubmission.model_fields.items() if f.is_required()}
    assert required == {"barcode", "results"}
    required_item = {k for k, f in DeviceResult.model_fields.items() if f.is_required()}
    assert required_item == {"test_name"}


def test_the_endpoint_derives_the_tenant_from_the_caller_not_the_payload():
    """A verified negative worth pinning: the bridge sends a hardcoded
    `lab_id: "LAB001"`, and if the endpoint trusted it, every lab's analyzer
    traffic would land in one tenant. It does not -- there is no `lab_id` field,
    and the query filters on `current_user.lab_id`.
    """
    assert "lab_id" not in DeviceSubmission.model_fields
    source = inspect.getsource(receive_device_results)
    assert "LabOrder.lab_id == current_user.lab_id" in source
    assert "data.lab_id" not in source


def test_the_endpoint_is_authenticated():
    parameters = inspect.signature(receive_device_results).parameters
    assert "get_current_user" in repr(parameters["current_user"].default)


def test_an_unauthenticated_post_is_rejected(client):
    """Permanently true and must stay true: whatever the contract becomes, an
    anonymous analyzer feed must not write results."""
    response = client.post("/device/results", json=_bridge_payload())
    assert response.status_code in (401, 403), response.status_code


# ── the divergence itself ────────────────────────────────────────────────────


@pytest.mark.xfail(
    strict=True,
    reason="IA-041: the device bridge payload does not satisfy DeviceSubmission. "
    "When this starts passing the contract has been reconciled -- delete this "
    "xfail and the one below.",
)
def test_the_bridge_payload_satisfies_the_endpoint_it_posts_to():
    DeviceSubmission(**_bridge_payload())


def test_the_divergence_is_exactly_the_two_missing_fields():
    """The xfail above says "it does not validate"; this says *why*, so a partial
    fix cannot quietly leave one half broken."""
    with pytest.raises(ValidationError) as excinfo:
        DeviceSubmission(**_bridge_payload())
    missing = {
        error["loc"] for error in excinfo.value.errors() if error["type"] == "missing"
    }
    assert missing == {("barcode",), ("results", 0, "test_name")}


@pytest.mark.xfail(
    strict=True,
    reason="IA-041: an authenticated post of the bridge's payload is still a 422. "
    "When this starts passing the body has been reconciled.",
)
def test_an_authenticated_post_of_the_bridge_payload_is_accepted(client, make_lab, make_lab_user):
    lab = make_lab()
    user = make_lab_user(lab_id=lab.id, role="admin")
    response = client.post(
        "/device/results",
        json=_bridge_payload(),
        headers=auth_headers(user.id, lab.id),
    )
    assert response.status_code not in (400, 422), response.text


# ── the transcription guard ──────────────────────────────────────────────────


def test_the_payload_above_still_matches_the_client_that_builds_it():
    """This file asserts things about a payload built in another tree. If
    GulaClient changes shape, the assertions become fiction, so the fields are
    checked against its source."""
    import pathlib

    client_src = (
        pathlib.Path(__file__).resolve().parents[3]
        / "services"
        / "device_bridge"
        / "app"
        / "integration"
        / "gula_client.py"
    )
    source = client_src.read_text()
    assert '"lab_id": self.lab_id' in source
    assert '"test_code": r.test_code' in source
    assert '"patient_id": r.patient_id' in source
    assert '"barcode"' not in source, "the bridge now sends a barcode; re-check IA-041"
    assert '"test_name"' not in source, "the bridge now sends a test_name; re-check IA-041"
    assert "/device/results" in source
