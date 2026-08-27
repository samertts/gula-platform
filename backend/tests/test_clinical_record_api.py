from __future__ import annotations

from uuid import uuid4

import pytest
from app.identity.api.workspaces import get_current_niam_actor_sync
from app.main import app

from tests.test_core_imaging_api import _complete_study
from tests.test_core_pharmacy_api import _prescribe, _setup


@pytest.fixture()
def context(request):
    return request.getfixturevalue("appointment_context")


def test_record_is_read_only_provenance_aware_and_filters_unreleased(client, context):
    encounter_id, medication = _setup(context, client)
    rx = _prescribe(context, client, encounter_id, medication["id"], quantity=3)
    workspace_id = context["workspace"].id
    signed = client.post(f"/api/v1/clinical/prescriptions/{rx['id']}/sign", headers={"Idempotency-Key": "record-rx-sign" , "If-Match": '"1"'}, json={"workspace_id": workspace_id})
    assert signed.status_code == 200, signed.text

    _, study, _ = _complete_study(context, client)
    draft_report = client.post("/api/v1/clinical/imaging-reports", headers={"Idempotency-Key": "record-draft-report"}, json={"workspace_id": workspace_id, "study_id": study["id"], "findings": "Draft finding", "impression": "Draft impression", "critical": False})
    assert draft_report.status_code == 201, draft_report.text

    response = client.get(f"/api/v1/clinical-records/{context['person'].id}", params={"workspace_id": workspace_id, "sections": ["medications", "imaging", "timeline"], "limit": 2})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["metadata"]["minimum_necessary"] is True
    assert body["metadata"]["consistency"] == "strong_snapshot"
    assert any(item["type"] == "prescription" and item["status"] == "SIGNED" for item in body["medications"])
    assert all(item.get("report_id") != draft_report.json()["report_id"] for item in body["imaging"])
    assert body["timeline"]
    assert all("source" in event and "domain" in event["source"] and "version" in event["source"] for event in body["timeline"])


def test_record_cursor_is_bounded_and_invalid_sections_are_rejected(client, context):
    encounter_id, medication = _setup(context, client)
    rx = _prescribe(context, client, encounter_id, medication["id"])
    workspace_id = context["workspace"].id
    signed = client.post(f"/api/v1/clinical/prescriptions/{rx['id']}/sign", headers={"Idempotency-Key": "record-cursor-sign", "If-Match": '"1"'}, json={"workspace_id": workspace_id})
    assert signed.status_code == 200, signed.text
    first = client.get(f"/api/v1/clinical-records/{context['person'].id}", params={"workspace_id": workspace_id, "sections": "timeline", "limit": 1})
    assert first.status_code == 200, first.text
    assert first.json()["next_cursor"]
    second = client.get(f"/api/v1/clinical-records/{context['person'].id}", params={"workspace_id": workspace_id, "sections": "timeline", "limit": 1, "cursor": first.json()["next_cursor"]})
    assert second.status_code == 200, second.text
    assert second.json()["timeline"]

    invalid = client.get(f"/api/v1/clinical-records/{context['person'].id}", params={"workspace_id": workspace_id, "sections": "secret_internal_table"})
    assert invalid.status_code == 422
    assert invalid.json()["code"] == "INVALID_RECORD_SECTION"


def test_record_wrong_patient_is_denied_and_no_client_identity_override(client, context):
    _setup(context, client)
    workspace_id = context["workspace"].id
    unknown_patient = "UNKNOWN" + uuid4().hex[:19].upper()
    response = client.get(f"/api/v1/clinical-records/{unknown_patient}", params={"workspace_id": workspace_id, "purpose": "treatment"})
    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"
    assert response.json().get("details", {}).get("correlation_id")
    app.dependency_overrides.pop(get_current_niam_actor_sync, None)
