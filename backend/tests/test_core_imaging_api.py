from __future__ import annotations

from uuid import uuid4

import pytest
from app.identity.api.workspaces import get_current_niam_actor_sync
from app.main import app

from tests.test_core_lab_result_access_api import (
    _create_visit,
    _grant_permissions,
    _provision_second_actor,
    _set_actor,
)

IMAGING_PERMISSIONS = (
    "clinical.imaging.order",
    "clinical.imaging.ingest",
    "clinical.imaging.report.write",
    "clinical.imaging.report.sign",
    "clinical.imaging.report.release",
    "clinical.imaging.report.amend",
    "clinical.imaging.report.read",
    "clinical.imaging.critical_ack",
)


@pytest.fixture()
def context(request):
    return request.getfixturevalue("appointment_context")


def _setup_order(context, client):
    _grant_permissions(context, IMAGING_PERMISSIONS)
    encounter_id = _create_visit(client, context)
    workspace_id = context["workspace"].id
    order = client.post(
        "/api/v1/clinical/imaging-orders",
        headers={"Idempotency-Key": "imaging-order-create-1"},
        json={"workspace_id": workspace_id, "encounter_id": encounter_id, "modality": "CT", "body_part": "Chest", "clinical_indication": "Synthetic indication", "priority": "ROUTINE"},
    )
    assert order.status_code == 201, order.text
    version = 1
    for path, _target in (("place", "PLACED"), ("schedule", "SCHEDULED")):
        response = client.post(f"/api/v1/clinical/imaging-orders/{order.json()['id']}/{path}", headers={"Idempotency-Key": f"imaging-order-{path}-1", "If-Match": f'"{version}"'}, json={"workspace_id": workspace_id})
        assert response.status_code == 200, response.text
        version = response.json()["version"]
    return order.json(), workspace_id


def _complete_study(context, client):
    order, workspace_id = _setup_order(context, client)
    study = client.post(
        "/api/v1/clinical/imaging-studies",
        headers={"Idempotency-Key": "imaging-study-ingest-1"},
        json={"workspace_id": workspace_id, "order_id": order["id"], "study_instance_uid": "1.2.840.113619.2.55.3.604688123.101", "accession_number": order["accession_number"], "modality": "CT", "source_message_id": "synthetic-dicom-message-1", "provenance_type": "SYNTHETIC_ADAPTER", "study_description": "Synthetic chest CT"},
    )
    assert study.status_code == 201, study.text
    study_body = study.json()
    for path, _target in (("match", "MATCHED"), ("acquire", "ACQUIRED"), ("complete", "COMPLETED")):
        response = client.post(f"/api/v1/clinical/imaging-studies/{study_body['id']}/{path}", headers={"Idempotency-Key": f"imaging-study-{path}-1", "If-Match": f'"{study_body["version"]}"'}, json={"workspace_id": workspace_id})
        assert response.status_code == 200, response.text
        study_body = response.json()
    return order, study_body, workspace_id


def test_imaging_workflow_has_exact_matching_duplicate_protection_and_immutable_report(client, context):
    order, study, workspace_id = _complete_study(context, client)
    instance = client.post(
        "/api/v1/clinical/imaging-instances",
        headers={"Idempotency-Key": "imaging-instance-1"},
        json={"workspace_id": workspace_id, "study_id": study["id"], "series_instance_uid": "1.2.3.series", "sop_instance_uid": "1.2.3.sop.1", "source_message_id": "synthetic-instance-message-1", "object_reference": "synthetic://pacs/study/1/series/1/sop/1", "checksum": "a" * 64, "file_size_bytes": 2048},
    )
    assert instance.status_code == 201, instance.text
    replay_different_key = client.post(
        "/api/v1/clinical/imaging-instances",
        headers={"Idempotency-Key": "imaging-instance-duplicate"},
        json={"workspace_id": workspace_id, "study_id": study["id"], "series_instance_uid": "1.2.3.series", "sop_instance_uid": "1.2.3.sop.1", "source_message_id": "synthetic-instance-message-2", "object_reference": "synthetic://pacs/study/1/series/1/sop/1", "checksum": "a" * 64, "file_size_bytes": 2048},
    )
    assert replay_different_key.status_code == 409
    assert replay_different_key.json()["code"] == "DICOM_DUPLICATE"

    public = client.post(
        "/api/v1/clinical/imaging-instances",
        headers={"Idempotency-Key": "imaging-instance-public"},
        json={"workspace_id": workspace_id, "study_id": study["id"], "series_instance_uid": "1.2.3.series", "sop_instance_uid": "1.2.3.sop.2", "source_message_id": "synthetic-instance-message-3", "object_reference": "https://public.example/image.dcm", "checksum": "b" * 64, "file_size_bytes": 2048},
    )
    assert public.status_code == 422

    report = client.post(
        "/api/v1/clinical/imaging-reports",
        headers={"Idempotency-Key": "imaging-report-create-1"},
        json={"workspace_id": workspace_id, "study_id": study["id"], "findings": "Synthetic finding", "impression": "Synthetic impression", "critical": True},
    )
    assert report.status_code == 201, report.text
    signed = client.post(f"/api/v1/clinical/imaging-reports/{report.json()['id']}/sign", headers={"Idempotency-Key": "imaging-report-sign-1", "If-Match": '"1"'}, json={"workspace_id": workspace_id})
    assert signed.status_code == 200, signed.text
    assert signed.json()["version"] == 2
    released = client.post(f"/api/v1/clinical/imaging-reports/{report.json()['id']}/release", headers={"Idempotency-Key": "imaging-report-release-1", "If-Match": '"2"'}, json={"workspace_id": workspace_id})
    assert released.status_code == 200, released.text
    assert released.json()["status"] == "RELEASED"
    assert released.json()["version"] == 3
    fhir_order = client.get(f"/api/v1/clinical/imaging-orders/{order['id']}/fhir?workspace_id={workspace_id}")
    fhir_study = client.get(f"/api/v1/clinical/imaging-studies/{study['id']}/fhir?workspace_id={workspace_id}")
    fhir_report = client.get(f"/api/v1/clinical/imaging-reports/{report.json()['id']}/fhir?workspace_id={workspace_id}")
    assert fhir_order.status_code == 200 and fhir_order.json()["resourceType"] == "ServiceRequest"
    assert fhir_study.status_code == 200 and fhir_study.json()["resourceType"] == "ImagingStudy"
    assert fhir_report.status_code == 200 and fhir_report.json()["resourceType"] == "DiagnosticReport" and fhir_report.json()["status"] == "final"

    amend = client.post(f"/api/v1/clinical/imaging-reports/{report.json()['id']}/amend", headers={"Idempotency-Key": "imaging-report-amend-1", "If-Match": '"3"'}, json={"workspace_id": workspace_id, "reason": "Synthetic correction", "findings": "Corrected synthetic finding", "impression": "Corrected synthetic impression", "critical": False})
    assert amend.status_code == 200, amend.text
    assert amend.json()["status"] == "DRAFT"
    assert amend.json()["version"] == 4
    assert amend.json()["supersedes_id"] == report.json()["id"]


def test_imaging_wrong_radiologist_is_denied_and_critical_ack_is_scoped(client, context):
    _, study, workspace_id = _complete_study(context, client)
    report = client.post("/api/v1/clinical/imaging-reports", headers={"Idempotency-Key": "imaging-report-wrong-1"}, json={"workspace_id": workspace_id, "study_id": study["id"], "findings": "Critical synthetic finding", "impression": "Urgent synthetic impression", "critical": True})
    assert report.status_code == 201, report.text
    reviewer_account, reviewer_session, _ = _provision_second_actor(context)
    _set_actor(reviewer_account, reviewer_session)
    wrong_sign = client.post(f"/api/v1/clinical/imaging-reports/{report.json()['id']}/sign", headers={"Idempotency-Key": "imaging-report-wrong-sign", "If-Match": '"1"'}, json={"workspace_id": workspace_id})
    assert wrong_sign.status_code == 403
    app.dependency_overrides.pop(get_current_niam_actor_sync, None)


def test_imaging_report_sharing_reuses_slice05_access_grant(client, context):
    _order, study, workspace_id = _complete_study(context, client)
    report = client.post("/api/v1/clinical/imaging-reports", headers={"Idempotency-Key": "imaging-share-report-create"}, json={"workspace_id": workspace_id, "study_id": study["id"], "findings": "Shared synthetic finding", "impression": "Shared synthetic impression", "critical": False})
    assert report.status_code == 201, report.text
    signed = client.post(f"/api/v1/clinical/imaging-reports/{report.json()['id']}/sign", headers={"Idempotency-Key": "imaging-share-report-sign", "If-Match": '"1"'}, json={"workspace_id": workspace_id})
    assert signed.status_code == 200, signed.text
    released = client.post(f"/api/v1/clinical/imaging-reports/{report.json()['id']}/release", headers={"Idempotency-Key": "imaging-share-report-release", "If-Match": '"2"'}, json={"workspace_id": workspace_id})
    assert released.status_code == 200, released.text
    grantee_account, grantee_session, _ = _provision_second_actor(context)
    grant = client.post("/api/v1/clinical/access/grants", headers={"Idempotency-Key": "imaging-share-grant"}, json={"workspace_id": workspace_id, "resource_type": "imaging_report", "resource_id": report.json()["id"], "grantee_account_id": grantee_account.id, "purpose": "TREATMENT", "scope": {"read_report": True}, "duration_hours": 12})
    assert grant.status_code == 201, grant.text
    _set_actor(grantee_account, grantee_session)
    shared = client.get(f"/api/v1/clinical/access/imaging-reports/{report.json()['id']}?workspace_id={workspace_id}")
    assert shared.status_code == 200, shared.text
    assert shared.json()["access_mode"] == "GRANTED"
    app.dependency_overrides.pop(get_current_niam_actor_sync, None)
